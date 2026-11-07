"""Pruebas de bin/linkedin_post.py con un servidor falso de LinkedIn.

Correr:  python3 -m unittest bin/test_linkedin_post.py -v
No usa red real ni credenciales: todo va contra un servidor local.
"""
import importlib.util
import io
import json
import os
import tempfile
import threading
import unittest
from contextlib import redirect_stdout
from datetime import date, datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "linkedin_post.py"


class Mock(BaseHTTPRequestHandler):
    log: list = []
    live = {"/posts/2026/nuevo/", "/posts/2026/uno/", "/posts/2026/dos/", "/posts/2026/tres/",
            "/posts/2026/cuatro/", "/posts/2026/cinco/", "/posts/2026/custom/"}
    post_status = 201

    def _body(self):
        n = int(self.headers.get("Content-Length") or 0)
        return self.rfile.read(n) if n else b""

    def _send(self, code, payload=None, headers=None):
        raw = json.dumps(payload).encode() if payload is not None else b""
        self.send_response(code)
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(raw)

    def do_HEAD(self):
        self._send(200 if self.path in self.live else 404)

    def do_GET(self):
        if self.path == "/v2/userinfo":
            return self._send(200, {"sub": "abc123", "name": "Test"})
        self._send(200 if self.path in self.live else 404)

    def do_POST(self):
        body = self._body()
        Mock.log.append(("POST", self.path, dict(self.headers), body))
        if self.path.startswith("/rest/images"):
            port = self.server.server_port
            return self._send(200, {"value": {"uploadUrl": f"http://127.0.0.1:{port}/upload/1",
                                              "image": "urn:li:image:IMG1"}})
        if self.path == "/rest/posts":
            if Mock.post_status != 201:
                return self._send(Mock.post_status, {"message": "nope"})
            return self._send(201, None, {"x-restli-id": f"urn:li:share:{len(Mock.log)}"})
        self._send(404)

    def do_PUT(self):
        Mock.log.append(("PUT", self.path, dict(self.headers), self._body()))
        self._send(201)

    def log_message(self, *a):
        pass


def post_md(title, date_line="2026-11-07 00:20:00 -0300", extra="", thumb=True):
    t = f'thumbnail: /assets/img/x/thumb.jpg\n' if thumb else ""
    return (f'---\nlayout: post\ntitle: {json.dumps(title, ensure_ascii=False)}\n'
            f'date: {date_line}\ndescription: {json.dumps("Resumen (con paréntesis) y #hashtag", ensure_ascii=False)}\n'
            f'{t}{extra}---\n\ncuerpo\n')


class Base(unittest.TestCase):
    def setUp(self):
        Mock.log = []
        Mock.post_status = 201
        self.srv = HTTPServer(("127.0.0.1", 0), Mock)
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.base = f"http://127.0.0.1:{self.srv.server_port}"
        self.tmp = tempfile.TemporaryDirectory()
        self.site = Path(self.tmp.name)
        (self.site / "_posts").mkdir()
        (self.site / "assets/img/x").mkdir(parents=True)
        (self.site / "assets/img/x/thumb.jpg").write_bytes(b"\xff\xd8JPEGDATA")
        (self.site / "_config.yml").write_text(
            f"url: {self.base}\nbaseurl: \"\"\ntimezone: America/Argentina/Buenos_Aires\n"
            "permalink: /posts/:year/:title/\n", encoding="utf-8")
        self.saved = dict(os.environ)
        os.environ.update({"SITE_DIR": str(self.site), "LINKEDIN_API_BASE": self.base,
                           "LINKEDIN_PAUSE": "0", "LINKEDIN_API_VERSION": "202610"})
        for k in ("LINKEDIN_ACCESS_TOKEN", "LINKEDIN_PERSON_ID", "LINKEDIN_TOKEN_EXPIRES_AT", "DRY_RUN",
                  "GITHUB_STEP_SUMMARY", "MAX_POSTS_PER_RUN"):
            os.environ.pop(k, None)

    def tearDown(self):
        self.srv.shutdown()
        self.srv.server_close()
        self.tmp.cleanup()
        os.environ.clear()
        os.environ.update(self.saved)

    def mod(self):
        spec = importlib.util.spec_from_file_location("lp", SCRIPT)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        return m

    def add(self, slug, md, day="2026-11-07"):
        (self.site / "_posts" / f"{day}-{slug}.md").write_text(md, encoding="utf-8")

    def login(self):
        os.environ["LINKEDIN_ACCESS_TOKEN"] = "TOKEN"
        os.environ["LINKEDIN_PERSON_ID"] = "abc123"

    def run_main(self, *args):
        m = self.mod()
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = m.main(list(args))
        return rc, buf.getvalue(), m

    def ledger(self):
        p = self.site / ".linkedin/posted.json"
        return json.loads(p.read_text()) if p.exists() else None


class Unitarias(Base):
    def test_front_matter(self):
        m = self.mod()
        fm = m.parse_front_matter(post_md('Título "con" comillas y tildes: á', extra="linkedin: false\n"))
        self.assertEqual(fm["title"], 'Título "con" comillas y tildes: á')
        self.assertIs(fm["linkedin"], False)
        self.assertEqual(fm["date"], "2026-11-07 00:20:00 -0300")

    def test_escape_todos_los_reservados(self):
        m = self.mod()
        src = "a|b {c} @d [e] (f) <g> #h \\i *j* _k_ ~l~"
        out = m.escape_little(src)
        for ch in "|{}@[]()<>#*_~":
            self.assertIn("\\" + ch, out, ch)
        self.assertIn("\\\\", out)
        self.assertNotIn("(", out.replace("\\(", ""))

    def test_url_usa_la_zona_horaria_del_sitio(self):
        # 01:00 UTC del 1/1/2027 es 22:00 del 31/12/2026 en Buenos Aires
        self.add("fin-de-anio", post_md("x", "2027-01-01 01:00:00 +0000"), day="2027-01-01")
        m = self.mod()
        p = m.load_posts(m.read_config())[0]
        self.assertTrue(p["url"].endswith("/posts/2026/fin-de-anio/"), p["url"])

    def test_custom_text_se_escapa(self):
        self.add("custom", post_md("T", extra='linkedin_text: "Mirá esto (nuevo) #ia"\n'))
        m = self.mod()
        p = m.load_posts(m.read_config())[0]
        self.assertEqual(m.build_commentary(p), "Mirá esto \\(nuevo\\) \\#ia")

    def test_comentario_por_defecto(self):
        self.add("nuevo", post_md("Mi post"))
        m = self.mod()
        c = m.build_commentary(m.load_posts(m.read_config())[0])
        self.assertTrue(c.startswith("Nuevo en el blog: Mi post\n\nResumen \\(con paréntesis\\) y \\#hashtag"))

    def test_vencimiento_del_token(self):
        m = self.mod()
        os.environ["LINKEDIN_TOKEN_EXPIRES_AT"] = (date.today() + timedelta(days=7)).isoformat()
        self.assertEqual(m.token_days_left(), 7)
        os.environ.pop("LINKEDIN_TOKEN_EXPIRES_AT")
        self.assertIsNone(m.token_days_left())


class Flujo(Base):
    def test_baseline_y_nuevo(self):
        self.add("uno", post_md("Uno"), day="2026-11-05")
        self.add("dos", post_md("Dos"), day="2026-11-06")
        rc, out, _ = self.run_main("--baseline")
        self.assertEqual(rc, 0)
        self.assertEqual({v["status"] for v in self.ledger()["posts"].values()}, {"baseline"})
        self.login()
        rc, out, _ = self.run_main()
        self.assertEqual(rc, 0)
        self.assertEqual(Mock.log, [], "no debe publicar posts del baseline")
        self.add("nuevo", post_md("Nuevo"))
        rc, out, _ = self.run_main()
        self.assertEqual(rc, 0)
        self.assertEqual(self.ledger()["posts"]["nuevo"]["status"], "posted")

    def test_flujo_completo_contra_la_api(self):
        self.add("nuevo", post_md("Nuevo (post) #1"))
        self.login()
        rc, out, _ = self.run_main()
        self.assertEqual(rc, 0, out)
        kinds = [(m, p.split("?")[0]) for m, p, _, _ in Mock.log]
        self.assertEqual(kinds, [("POST", "/rest/images"), ("PUT", "/upload/1"), ("POST", "/rest/posts")])
        init, put, create = Mock.log
        self.assertEqual(json.loads(init[3]), {"initializeUploadRequest": {"owner": "urn:li:person:abc123"}})
        self.assertEqual(init[2]["Authorization"], "Bearer TOKEN")
        self.assertEqual(init[2]["Linkedin-Version"], "202610")
        self.assertEqual(init[2]["X-Restli-Protocol-Version"], "2.0.0")
        self.assertEqual(put[3], b"\xff\xd8JPEGDATA")
        body = json.loads(create[3])
        self.assertEqual(body["author"], "urn:li:person:abc123")
        self.assertEqual(body["visibility"], "PUBLIC")
        self.assertEqual(body["lifecycleState"], "PUBLISHED")
        self.assertEqual(body["distribution"]["feedDistribution"], "MAIN_FEED")
        art = body["content"]["article"]
        self.assertEqual(art["source"], f"{self.base}/posts/2026/nuevo/")
        self.assertEqual(art["thumbnail"], "urn:li:image:IMG1")
        self.assertEqual(art["title"], "Nuevo (post) #1")
        self.assertIn("\\(post\\) \\#1", body["commentary"])
        self.assertTrue(self.ledger()["posts"]["nuevo"]["urn"].startswith("urn:li:share:"))
        # idempotente: una segunda corrida no vuelve a publicar
        Mock.log.clear()
        rc, out, _ = self.run_main()
        self.assertEqual((rc, Mock.log), (0, []))

    def test_dry_run_no_llama_ni_escribe(self):
        self.add("nuevo", post_md("Nuevo"))
        self.login()
        rc, out, _ = self.run_main("--dry-run")
        self.assertEqual(rc, 0)
        self.assertEqual(Mock.log, [])
        self.assertIsNone(self.ledger())
        self.assertIn("[DRY RUN] nuevo", out)

    def test_sin_secretos_se_omite_sin_fallar(self):
        self.add("nuevo", post_md("Nuevo"))
        rc, out, _ = self.run_main()
        self.assertEqual((rc, Mock.log), (0, []))
        self.assertIn("LinkedIn no está configurado", out)
        self.assertIsNone(self.ledger())

    def test_401_corta_y_no_marca_como_publicado(self):
        self.add("nuevo", post_md("Nuevo"))
        self.login()
        Mock.post_status = 401
        rc, out, _ = self.run_main()
        self.assertEqual(rc, 1)
        self.assertIn("401", out)
        self.assertNotIn("nuevo", (self.ledger() or {"posts": {}})["posts"])

    def test_fecha_futura_y_optout_no_se_publican(self):
        self.add("uno", post_md("Futuro", "2999-01-01 00:00:00 -0300"))
        self.add("dos", post_md("Optout", extra="linkedin: false\n"))
        self.login()
        rc, out, _ = self.run_main()
        self.assertEqual((rc, Mock.log), (0, []))

    def test_maximo_por_corrida(self):
        for s in ("uno", "dos", "tres", "cuatro", "cinco"):
            self.add(s, post_md(s))
        self.login()
        rc, out, _ = self.run_main("--max", "3")
        self.assertEqual(rc, 0)
        self.assertEqual(sum(1 for v in self.ledger()["posts"].values() if v["status"] == "posted"), 3)
        rc, out, _ = self.run_main("--max", "3")
        self.assertEqual(sum(1 for v in self.ledger()["posts"].values() if v["status"] == "posted"), 5)

    def test_url_que_no_responde_se_reintenta(self):
        self.add("fantasma", post_md("No existe todavía"))
        self.login()
        m = self.mod()
        m.url_is_live = lambda url, attempts=3, wait=20: False
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = m.main([])
        self.assertEqual((rc, Mock.log), (0, []))
        self.assertIsNone(self.ledger())

    def test_vencido_falla_y_por_vencer_avisa(self):
        self.add("nuevo", post_md("Nuevo"))
        self.login()
        os.environ["LINKEDIN_TOKEN_EXPIRES_AT"] = (date.today() - timedelta(days=1)).isoformat()
        rc, out, _ = self.run_main()
        self.assertEqual((rc, Mock.log), (2, []))
        os.environ["LINKEDIN_TOKEN_EXPIRES_AT"] = (date.today() + timedelta(days=3)).isoformat()
        rc, out, _ = self.run_main()
        self.assertEqual(rc, 5)  # publicó, pero falla a propósito para que GitHub avise
        self.assertEqual(self.ledger()["posts"]["nuevo"]["status"], "posted")

    def test_whoami(self):
        self.login()
        rc, out, _ = self.run_main("--whoami")
        self.assertEqual(rc, 0)
        self.assertIn("abc123", out)


if __name__ == "__main__":
    unittest.main()
