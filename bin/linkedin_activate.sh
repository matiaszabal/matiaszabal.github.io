#!/usr/bin/env bash
# Asistente para poner en marcha, encender o pausar la publicación en LinkedIn.
# Lo corrés VOS, en tu terminal: el token pasa por acá y va directo a los secretos de GitHub.
#
#   bin/linkedin_activate.sh setup    carga token y secretos y prueba en simulación (no publica)
#   bin/linkedin_activate.sh status   muestra qué está configurado
#   bin/linkedin_activate.sh enable   muestra la cola y, si escribís ENCENDER, activa la publicación diaria
#   bin/linkedin_activate.sh pause    apaga la publicación diaria
set -euo pipefail
cd "$(dirname "$0")/.."
GH=${GH:-gh}
PY=${PYTHON:-python3}

case "${1:-help}" in
  setup)
    echo "Antes: app creada, productos agregados y token generado (pasos 1 a 3 de .linkedin/README.md)."
    read -rsp "Pegá el token de LinkedIn (no se muestra): " TOKEN; echo
    [ -n "$TOKEN" ] || { echo "Token vacío."; exit 1; }
    OUT=$(LINKEDIN_ACCESS_TOKEN="$TOKEN" "$PY" bin/linkedin_post.py --whoami) || { echo "LinkedIn rechazó el token."; exit 1; }
    echo "$OUT"
    PID=$(sed -n 's/^LINKEDIN_PERSON_ID = //p' <<<"$OUT")
    [ -n "$PID" ] || { echo "No pude leer tu id de miembro."; exit 1; }
    read -rp "¿Es tu cuenta? Guardo el token y el id como secretos del repo (s/N): " OK
    [ "$OK" = "s" ] || { echo "Cancelado, no se guardó nada."; exit 1; }
    printf %s "$TOKEN" | "$GH" secret set LINKEDIN_ACCESS_TOKEN
    printf %s "$PID" | "$GH" secret set LINKEDIN_PERSON_ID
    "$GH" variable set LINKEDIN_TOKEN_EXPIRES_AT --body "$(date -d '+59 days' +%F)"
    "$GH" workflow run linkedin.yml -f dry_run=true
    echo
    echo "Listo. La publicación sigue PAUSADA: nada sale hasta que corras '$0 enable'."
    echo "Revisá la simulación en la pestaña Actions (workflow «LinkedIn (1 post por día)»)."
    ;;
  status)
    echo "Secretos:";   "$GH" secret list   | grep -i linkedin || echo "  (ninguno)"
    echo "Variables:";  "$GH" variable list | grep -i linkedin || echo "  (ninguna)"
    ;;
  enable)
    "$GH" secret list | grep -q LINKEDIN_ACCESS_TOKEN || { echo "Falta el token: corré primero '$0 setup'."; exit 1; }
    "$PY" bin/linkedin_post.py --plan
    echo
    echo "Esto es lo que saldrá, un post por día, desde la próxima corrida (09:30 hora de Argentina)."
    read -rp "Para activar la publicación diaria en tu LinkedIn escribí ENCENDER: " C
    [ "$C" = "ENCENDER" ] || { echo "No se activó nada."; exit 1; }
    "$GH" variable set LINKEDIN_ENABLED --body true
    echo "Activado. Para frenar en cualquier momento: $0 pause"
    ;;
  pause)
    "$GH" variable set LINKEDIN_ENABLED --body false
    echo "Pausado: no se publica nada hasta que vuelvas a correr '$0 enable'."
    ;;
  *)
    sed -n '2,9p' "$0" | sed 's/^# \{0,1\}//'
    ;;
esac
