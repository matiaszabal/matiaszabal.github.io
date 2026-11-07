#!/usr/bin/env bash
# Asistente para poner en marcha, encender o pausar la publicación en LinkedIn.
# Lo corrés VOS, en tu terminal: el token pasa por acá y va directo a los secretos de GitHub.
#
#   bin/linkedin_activate.sh setup    carga token y secretos y prueba en simulación (no publica)
#   bin/linkedin_activate.sh status   muestra qué está configurado
#   bin/linkedin_activate.sh test-first   publica SOLO el primer post de la cola, ahora, y deja todo pausado
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
  test-first)
    "$GH" secret list | grep -q LINKEDIN_ACCESS_TOKEN || { echo "Falta el token: corré primero '$0 setup'."; exit 1; }
    read -rp "¿Link en el primer comentario (c) o dentro del post como tarjeta (t)? [c]: " M
    MODE=comment; [ "${M:-c}" = "t" ] && MODE=card
    LINKEDIN_LINK_MODE=$MODE "$PY" bin/linkedin_post.py --plan | sed -n '1,40p'
    echo
    echo "Se publicará SOLO el primer post de la cola, ahora, en tu LinkedIn (modo: $MODE). Después queda todo pausado."
    read -rp "Para publicarlo escribí PUBLICAR: " C
    [ "$C" = "PUBLICAR" ] || { echo "No se publicó nada."; exit 1; }
    "$GH" variable set LINKEDIN_LINK_MODE --body "$MODE"
    "$GH" variable set LINKEDIN_ENABLED --body true
    "$GH" workflow run linkedin.yml -f dry_run=false
    sleep "${LINKEDIN_WAIT:-15}"
    ID=$("$GH" run list --workflow linkedin.yml --limit 1 --json databaseId --jq '.[0].databaseId')
    "$GH" run watch "$ID" --exit-status || echo "El workflow terminó con error: mirá el log."
    "$GH" variable set LINKEDIN_ENABLED --body false
    echo
    echo "Pausado de nuevo. Revisá el post en LinkedIn y el log: gh run view $ID --log"
    echo "Si salió bien, '$0 enable' activa un post por día; si no, no se publicó nada más."
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
    sed -n '2,10p' "$0" | sed 's/^# \{0,1\}//'
    ;;
esac
