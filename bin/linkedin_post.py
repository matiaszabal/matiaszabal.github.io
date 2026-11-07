#!/usr/bin/env python3
"""Publica en LinkedIn los posts nuevos del blog.

Solo usa la biblioteca estándar. Pensado para correr en GitHub Actions después
del deploy (ver el job `linkedin` de .github/workflows/pages.yml).

Cómo decide qué publicar
- Un post es "nuevo" si su slug no está en .linkedin/posted.json.
- Los posts que ya existían al activar la automatización se marcan como
  `baseline` (python3 bin/linkedin_post.py --baseline) y nunca se publican.
- Se saltea un post con fecha futura, con `linkedin: false` en el front matter
  o cuya URL todavía no responde 200.

Configuración (variables de entorno)
- LINKEDIN_ACCESS_TOKEN   token OAuth de 60 días (permiso w_member_social)
- LINKEDIN_PERSON_ID      id del miembro (o el URN completo urn:li:person:...)
- LINKEDIN_API_VERSION    cabecera Linkedin-Version (AAAAMM). Default: 202610
- LINKEDIN_TOKEN_EXPIRES_AT  AAAA-MM-DD; avisa al acercarse y falla al vencer
- LINKEDIN_API_BASE       solo para pruebas (default https://api.linkedin.com)
- DRY_RUN=1               muestra lo que publicaría, sin llamar a LinkedIn
- SITE_DIR                raíz del sitio (default: el repo)

Opciones por post (front matter)
- linkedin: false         no publicar este post en LinkedIn
- linkedin_text: "..."    texto propio para el comentario (se escapa solo)
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(os.environ.get("SITE_DIR") or Path(__file__).resolve().parent.parent)
LEDGER = ROOT / ".linkedin" / "posted.json"
API = (os.environ.get("LINKEDIN_API_BASE") or "https://api.linkedin.com").rstrip("/")
VERSION = os.environ.get("LINKEDIN_API_VERSION") or "202610"

# Caracteres reservados del formato de texto de LinkedIn ("little"): hay que
# escaparlos con una barra invertida aunque no se usen como mención o hashtag.
RESERVED = set("|{}@[]()<>#\\*_~")
MAX_COMMENTARY = 3000
MAX_PER_RUN_DEFAULT = 3
PAUSE = float(os.environ.get("LINKEDIN_PAUSE") or 2)  # segundos entre posts
MAX_PER_DAY = int(os.environ.get("LINKEDIN_MAX_PER_DAY") or 1)  # tope diario (día del sitio)


class LinkedInError(Exception):
    def __init__(self, status: int, body: str):
        super().__init__(f"HTTP {status}: {body[:400]}")
        self.status, self.body = status, body


# ----------------------------------------------------------------- utilidades
def log(msg: str) -> None:
    print(msg, flush=True)


def gh(kind: str, msg: str) -> None:
    """Anotación visible en la pantalla de GitHub Actions."""
    print(f"::{kind}::{msg}", flush=True)


def summary(lines: list[str]) -> None:
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if path:
        with open(path, "a", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")


def read_config() -> dict:
    text = (ROOT / "_config.yml").read_text(encoding="utf-8")

    def get(key: str, default: str = "") -> str:
        m = re.search(rf"^{key}:\s*[\"']?([^\s\"'#]+)", text, re.M)
        return m.group(1) if m else default

    return {
        "url": get("url").rstrip("/"),
        "permalink": get("permalink", "/:year/:month/:day/:title/"),
        "timezone": get("timezone", "UTC"),
    }


def parse_front_matter(text: str) -> dict:
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    fm: dict = {}
    if not m:
        return fm
    for line in m.group(1).splitlines():
        if not line or line[0] in " \t#":
            continue
        key, sep, value = line.partition(":")
        if not sep:
            continue
        value = value.strip()
        if value.startswith('"'):
            try:
                value = json.loads(value)
            except ValueError:
                value = value.strip('"')
        elif value.startswith("'"):
            value = value.strip("'")
        elif value.lower() in ("true", "false"):
            value = value.lower() == "true"
        fm[key.strip()] = value
    return fm


def parse_date(raw, filename_date: str, tz: ZoneInfo) -> datetime:
    if isinstance(raw, str):
        for fmt in ("%Y-%m-%d %H:%M:%S %z", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
            try:
                d = datetime.strptime(raw.strip(), fmt)
                return d if d.tzinfo else d.replace(tzinfo=tz)
            except ValueError:
                continue
    return datetime.strptime(filename_date, "%Y-%m-%d").replace(tzinfo=tz)


def load_posts(cfg: dict) -> list[dict]:
    tz = ZoneInfo(cfg["timezone"])
    posts = []
    for path in sorted((ROOT / "_posts").glob("*.md")):
        m = re.match(r"(\d{4}-\d{2}-\d{2})-(.+)\.md$", path.name)
        if not m:
            continue
        fm = parse_front_matter(path.read_text(encoding="utf-8"))
        when = parse_date(fm.get("date"), m.group(1), tz)
        local = when.astimezone(tz)
        slug = m.group(2)
        route = (
            cfg["permalink"]
            .replace(":year", f"{local:%Y}")
            .replace(":month", f"{local:%m}")
            .replace(":day", f"{local:%d}")
            .replace(":title", slug)
        )
        posts.append(
            {
                "slug": slug,
                "when": when,
                "title": str(fm.get("title") or slug),
                "description": str(fm.get("description") or ""),
                "thumbnail": fm.get("thumbnail") or "",
                "optout": fm.get("linkedin") is False,
                "custom_text": fm.get("linkedin_text") or "",
                "url": cfg["url"] + route,
            }
        )
    return sorted(posts, key=lambda p: p["when"])


def load_ledger() -> dict:
    if LEDGER.exists():
        return json.loads(LEDGER.read_text(encoding="utf-8"))
    return {"version": 1, "posts": {}}


def save_ledger(ledger: dict) -> None:
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    LEDGER.write_text(
        json.dumps(ledger, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


# ------------------------------------------------------------------- contenido
def escape_little(text: str) -> str:
    return "".join("\\" + c if c in RESERVED else c for c in text)


HASHTAG = re.compile(r"(?<![\w#\\])#([^\W\d_][^\W_]*)")


def to_little(text: str) -> str:
    """Texto plano a formato de LinkedIn: escapa lo reservado y convierte #etiqueta en hashtag real."""
    out, pos = [], 0
    for m in HASHTAG.finditer(text):
        out.append(escape_little(text[pos:m.start()]))
        out.append("{hashtag|\\#|" + m.group(1) + "}")
        pos = m.end()
    out.append(escape_little(text[pos:]))
    return "".join(out)


def clip(text: str, limit: int) -> str:
    text = text.strip()
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def build_commentary(post: dict) -> str:
    if post["custom_text"]:
        plain = str(post["custom_text"])
    else:
        plain = f"Nuevo en el blog: {post['title']}"
        if post["description"]:
            plain += f"\n\n{post['description']}"
    return to_little(clip(plain, MAX_COMMENTARY // 2))


def build_post_body(post: dict, person_urn: str, thumbnail_urn: str | None) -> dict:
    article = {"source": post["url"], "title": clip(post["title"], 200)}
    if post["description"].strip():  # LinkedIn rechaza campos de texto en blanco
        article["description"] = clip(post["description"], 250)
    if thumbnail_urn:
        article["thumbnail"] = thumbnail_urn
    return {
        "author": person_urn,
        "commentary": build_commentary(post),
        "visibility": "PUBLIC",
        "distribution": {
            "feedDistribution": "MAIN_FEED",
            "targetEntities": [],
            "thirdPartyDistributionChannels": [],
        },
        "content": {"article": article},
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False,
    }


# ------------------------------------------------------------------------ HTTP
def _request(method: str, url: str, headers: dict, data: bytes | None):
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, dict(r.headers), r.read()
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        e.close()
        raise LinkedInError(e.code, body) from None
    except urllib.error.URLError as e:
        raise LinkedInError(0, f"sin conexión: {e.reason}") from None


def api(method: str, path: str, token: str, body: dict | None = None):
    headers = {
        "Authorization": f"Bearer {token}",
        "Linkedin-Version": VERSION,
        "X-Restli-Protocol-Version": "2.0.0",
        "Content-Type": "application/json",
    }
    data = json.dumps(body).encode("utf-8") if body is not None else None
    status, hdrs, raw = _request(method, f"{API}{path}", headers, data)
    return status, {k.lower(): v for k, v in hdrs.items()}, (json.loads(raw) if raw else {})


def upload_thumbnail(path: Path, person_urn: str, token: str) -> str:
    _, _, init = api(
        "POST", "/rest/images?action=initializeUpload", token,
        {"initializeUploadRequest": {"owner": person_urn}},
    )
    value = init["value"]
    blob = path.read_bytes()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/octet-stream"}
    try:
        _request("PUT", value["uploadUrl"], headers, blob)
    except LinkedInError as e:
        if e.status not in (405, 415):  # la doc menciona POST; el ejemplo usa PUT
            raise
        _request("POST", value["uploadUrl"], headers, blob)
    return value["image"]


def publish(post: dict, person_urn: str, token: str) -> str:
    thumb_urn = None
    thumb_path = ROOT / str(post["thumbnail"]).lstrip("/") if post["thumbnail"] else None
    if thumb_path and thumb_path.exists():
        thumb_urn = upload_thumbnail(thumb_path, person_urn, token)
    else:
        gh("warning", f"{post['slug']}: sin miniatura utilizable; se publica sin imagen")
    body = build_post_body(post, person_urn, thumb_urn)
    _, hdrs, _ = api("POST", "/rest/posts", token, body)
    return hdrs.get("x-restli-id", "")


def url_is_live(url: str, attempts: int = 3, wait: int = 20) -> bool:
    for i in range(attempts):
        try:
            req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "blog-linkedin-bot"})
            with urllib.request.urlopen(req, timeout=20) as r:
                if r.status == 200:
                    return True
        except (urllib.error.URLError, OSError):
            pass
        if i < attempts - 1:
            time.sleep(wait)
    return False


# ------------------------------------------------------------------------ main
def person_urn_from_env() -> str:
    pid = (os.environ.get("LINKEDIN_PERSON_ID") or "").strip()
    if not pid:
        return ""
    return pid if pid.startswith("urn:li:person:") else f"urn:li:person:{pid}"


def token_days_left(today: date | None = None) -> int | None:
    raw = (os.environ.get("LINKEDIN_TOKEN_EXPIRES_AT") or "").strip()
    if not raw:
        return None
    return (date.fromisoformat(raw) - (today or date.today())).days


def cmd_whoami(token: str) -> int:
    _, _, info = api("GET", "/v2/userinfo", token)
    log(f"LINKEDIN_PERSON_ID = {info.get('sub')}")
    log(f"nombre: {info.get('name')}")
    return 0


def cmd_baseline() -> int:
    cfg = read_config()
    ledger = load_ledger()
    added = 0
    for p in load_posts(cfg):
        if p["slug"] not in ledger["posts"]:
            ledger["posts"][p["slug"]] = {"status": "baseline"}
            added += 1
    save_ledger(ledger)
    log(f"baseline: {added} posts marcados como ya existentes (no se publicarán)")
    return 0


def candidates(posts: list[dict], ledger: dict, now: datetime) -> list[dict]:
    """Primero la cola explícita (status queued, por `order`), después los posts nuevos por fecha."""
    queued, new = [], []
    for p in posts:
        entry = ledger["posts"].get(p["slug"])
        if entry and entry.get("status") != "queued":
            continue
        if p["optout"]:
            log(f"- {p['slug']}: omitido (linkedin: false)")
            continue
        if p["when"] > now:
            log(f"- {p['slug']}: fecha futura, se publicará cuando salga")
            continue
        (queued if entry else new).append(p)
    queued.sort(key=lambda p: ledger["posts"][p["slug"]].get("order", 10**6))
    return queued + new


def posted_today(ledger: dict, tz: ZoneInfo, now: datetime) -> int:
    today = now.astimezone(tz).date()
    n = 0
    for v in ledger["posts"].values():
        if v.get("status") == "posted" and v.get("at"):
            if datetime.fromisoformat(v["at"]).astimezone(tz).date() == today:
                n += 1
    return n


def cmd_enqueue(slugs: list[str]) -> int:
    """Pone posts en la cola, en ese orden. Pisa un `baseline`; no toca lo ya publicado."""
    posts = {p["slug"]: p for p in load_posts(read_config())}
    ledger = load_ledger()
    for slug in slugs:
        if slug not in posts:
            log(f"No existe el post '{slug}' en _posts/")
            return 2
        if ledger["posts"].get(slug, {}).get("status") == "posted":
            log(f"'{slug}' ya fue publicado en LinkedIn; no se vuelve a encolar")
            return 2
    for i, slug in enumerate(slugs, 1):
        ledger["posts"][slug] = {"status": "queued", "order": i}
    save_ledger(ledger)
    log(f"cola: {len(slugs)} posts, uno por día, en este orden:")
    for i, slug in enumerate(slugs, 1):
        log(f"  {i}. {slug}")
    return 0


def cmd_plan() -> int:
    """Muestra la cola y exactamente lo que se publicaría, sin llamar a LinkedIn."""
    cfg = read_config()
    tz = ZoneInfo(cfg["timezone"])
    ledger = load_ledger()
    todo = candidates(load_posts(cfg), ledger, datetime.now(timezone.utc))
    done = posted_today(ledger, tz, datetime.now(timezone.utc))
    log(f"tope diario: {MAX_PER_DAY} | ya publicados hoy: {done} | en cola o nuevos: {len(todo)}")
    for i, p in enumerate(todo, 1):
        commentary = build_commentary(p)
        thumb = bool(p["thumbnail"]) and (ROOT / p["thumbnail"].lstrip("/")).exists()
        log(f"\n--- salida #{i}: {p['slug']}\nlink: {p['url']}\nminiatura: {'sí' if thumb else 'NO'} | "
            f"texto propio: {'sí' if p['custom_text'] else 'no (usa el texto por defecto)'} | {len(commentary)} caracteres\n"
            f"texto tal como lo enviaría el script:\n{commentary}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--dry-run", action="store_true", help="no llama a LinkedIn")
    ap.add_argument("--baseline", action="store_true", help="marca los posts actuales como ya existentes")
    ap.add_argument("--whoami", action="store_true", help="muestra el id de miembro del token")
    ap.add_argument("--max", type=int, default=int(os.environ.get("MAX_POSTS_PER_RUN") or MAX_PER_RUN_DEFAULT))
    ap.add_argument("--enqueue", nargs="+", metavar="SLUG", help="pone posts en la cola, en ese orden (uno por día)")
    ap.add_argument("--plan", action="store_true", help="muestra la cola y el texto exacto de cada salida")
    args = ap.parse_args(argv)
    dry = args.dry_run or os.environ.get("DRY_RUN", "") not in ("", "0", "false")
    token = (os.environ.get("LINKEDIN_ACCESS_TOKEN") or "").strip()

    if args.baseline:
        return cmd_baseline()
    if args.enqueue:
        return cmd_enqueue(args.enqueue)
    if args.plan:
        return cmd_plan()
    if args.whoami:
        if not token:
            log("Falta LINKEDIN_ACCESS_TOKEN")
            return 2
        return cmd_whoami(token)

    days = token_days_left()
    if days is not None and days < 0:
        gh("error", "El token de LinkedIn venció: generá uno nuevo y actualizá el secreto (ver .linkedin/README.md)")
        return 2

    cfg = read_config()
    posts = load_posts(cfg)
    ledger = load_ledger()
    todo = candidates(posts, ledger, datetime.now(timezone.utc))
    log(f"{len(posts)} posts en el sitio, {len(ledger['posts'])} en el registro, {len(todo)} para publicar")
    now = datetime.now(timezone.utc)
    left = max(0, MAX_PER_DAY - posted_today(ledger, ZoneInfo(cfg["timezone"]), now))
    cap = min(args.max, left)
    enabled = os.environ.get("LINKEDIN_ENABLED", "").strip().lower() in ("1", "true", "yes")

    rc = 0
    done: list[str] = []
    if todo and dry:
        if left == 0:
            log("(ya se publicó el máximo de hoy: lo siguiente saldría mañana)")
        for p in todo[:MAX_PER_DAY]:
            body = build_post_body(p, person_urn_from_env() or "urn:li:person:DRY_RUN", "urn:li:image:DRY_RUN" if p["thumbnail"] else None)
            log(f"\n[DRY RUN] {p['slug']}\n{json.dumps(body, ensure_ascii=False, indent=2)}")
        log("\n[DRY RUN] no se llamó a LinkedIn ni se tocó el registro")
    elif todo and not enabled:
        gh("notice", f"Publicación en LinkedIn PAUSADA (falta LINKEDIN_ENABLED=true): {len(todo)} post(s) en cola, no se publica nada")
    elif todo and left == 0:
        log(f"Ya se publicó el máximo de hoy ({MAX_PER_DAY}); quedan {len(todo)} en cola para los días siguientes")
    elif todo and (not token or not person_urn_from_env()):
        gh("notice", f"LinkedIn no está configurado (faltan secretos): {len(todo)} post(s) quedan pendientes")
    elif todo:
        person = person_urn_from_env()
        if len(todo) > cap:
            log(f"{len(todo)} para publicar; hoy sale(n) {cap} (tope diario {MAX_PER_DAY}); el resto, los días siguientes")
        for p in todo[:cap]:
            if not url_is_live(p["url"]):
                gh("warning", f"{p['slug']}: la URL todavía no responde 200; se reintenta en la próxima corrida")
                continue
            try:
                urn = publish(p, person, token)
            except LinkedInError as e:
                if e.status == 401:
                    gh("error", "LinkedIn rechazó el token (401): vencido o revocado. Generá uno nuevo (ver .linkedin/README.md)")
                else:
                    gh("error", f"{p['slug']}: LinkedIn respondió {e}")
                rc = 1
                break
            ledger["posts"][p["slug"]] = {
                "status": "posted",
                "urn": urn,
                "url": p["url"],
                "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            }
            save_ledger(ledger)  # se guarda ya mismo: evita duplicados si falla algo después
            done.append(p["slug"])
            log(f"publicado: {p['slug']} -> {urn}")
            time.sleep(PAUSE)

    if days is not None and days <= 10:
        msg = f"El token de LinkedIn vence en {days} día(s): renovalo (ver .linkedin/README.md)"
        gh("warning", msg)
        if days <= 5 and rc == 0:
            gh("error", msg)  # falla el job a propósito para que GitHub te mande un mail
            rc = 5

    summary(["### LinkedIn", f"- publicados: {', '.join(done) or 'ninguno'}", f"- pendientes: {len(todo) - len(done)}"])
    return rc


if __name__ == "__main__":
    sys.exit(main())
