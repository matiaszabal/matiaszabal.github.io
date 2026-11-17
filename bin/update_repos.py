#!/usr/bin/env python3
"""Regenera _data/repos.yml con TODOS los repos públicos de la cuenta (usa `gh`).

Uso: python3 bin/update_repos.py [usuario]   (por defecto: matiaszabal)
Orden: primero los propios, por estrellas y último push; después los forks.
"""
import json
import subprocess
import sys

user = sys.argv[1] if len(sys.argv) > 1 else "matiaszabal"
raw = subprocess.check_output(
    ["gh", "api", f"users/{user}/repos", "--paginate", "--jq", ".[]"], text=True
)
repos = [json.loads(line) for line in raw.splitlines() if line.strip()]
repos = [r for r in repos if not r["private"]]  # solo públicos, por las dudas
# Orden estable en dos pasos: primero por último push (reciente primero) y después por estrellas.
by_push = sorted(repos, key=lambda r: r["pushed_at"] or "", reverse=True)
own = sorted([r for r in by_push if not r["fork"]], key=lambda r: -r["stargazers_count"])
forks = [r for r in by_push if r["fork"]]


def q(s):
    return '"' + (s or "").replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ") + '"'


out = ["# Generado por bin/update_repos.py: no editar a mano.", "repos:"]
for r in own + forks:
    out += [
        f"  - name: {r['name']}",
        f"    url: {r['html_url']}",
        f"    description: {q(r['description'])}",
        f"    language: {q(r['language'])}",
        f"    stars: {r['stargazers_count']}",
        f"    fork: {'true' if r['fork'] else 'false'}",
    ]
open("_data/repos.yml", "w", encoding="utf-8").write("\n".join(out) + "\n")
print(f"{len(own)} propios + {len(forks)} forks = {len(own) + len(forks)} repos")
