# Blog de Matías: reglas para publicar

Sitio Jekyll con el tema al-folio en GitHub Pages (`matiaszabal.github.io`). URLs de posts: `/posts/AAAA/titulo/`. Audiencia: colegas de IA agéntica.
Cada push a `main` despliega solo con GitHub Actions.

## Flujo para un artículo nuevo

1. Escribir el post en `_drafts/titulo-en-minusculas.md` (sin fecha en el nombre) y mostrárselo a Matías.
2. **Publicar solo cuando Matías lo pida explícitamente en esa conversación** ("publicalo").
   Un push a este repo público no se puede deshacer del todo (historial, cachés, RSS).
3. Para publicar: mover a `_posts/AAAA-MM-DD-titulo.md`, commit y push a `main`.
   Fecha futura en el front matter = publicación programada (el sitio se reconstruye a diario).
4. Verificar: `gh run watch` hasta que termine en verde, luego abrir la URL del post y `/feed.xml`.
5. Publicar el post en el blog **no** lo publica en LinkedIn: eso lo maneja la cola diaria (ver abajo) y hoy está pausada.
6. Cuando LinkedIn esté activo, el robot agrega un commit a `main` (`LinkedIn: registrar publicaciones`).
   Hacer `git pull --rebase origin main` antes del próximo push.

## Front matter

```yaml
---
layout: post
title: "Título"
date: 2026-11-06 09:00:00 -0300
description: "Resumen de una o dos frases"
thumbnail: /assets/img/<slug>/thumb.jpg
linkedin_text: "Texto del post de LinkedIn (opcional, ver abajo)"
tags: [agentes, evaluación]
---
```

## LinkedIn automático (1 post por día, hoy PAUSADO)

`.github/workflows/linkedin.yml` publica a las 09:30 (Argentina) como máximo UN post por día en el perfil de
Matías: primero la cola de `.linkedin/posted.json`, después los posts nuevos. Puesta en marcha, cola, renovación del
token (cada 60 días) y detalles: `.linkedin/README.md`.

- **Está pausado.** Sin credenciales y sin `LINKEDIN_ENABLED=true` no se publica nada. **Nunca activarlo, cargar
  secretos ni cambiar `LINKEDIN_ENABLED` sin que Matías lo pida.** Publicar en su cuenta es público e irreversible.
- Los textos de LinkedIn necesitan **su aprobación explícita** antes de encenderlo (sus reglas de voz lo exigen).
- **Al crear un post, escribir `linkedin_text`** con los skills `linkedin-post-writer` y `linkedin-humanizer`:
  gancho con cifra y fuente en los primeros 210 caracteres, sin link en el cuerpo, 0 a 2 hashtags al final, sin
  inventar nada (perfil de voz y banco de historias siguen en `filled: no`: no hay anécdotas personales para usar).
  Las `#etiquetas` se vuelven hashtags reales; los demás caracteres reservados se escapan solos.
- `linkedin: false` saca un post de LinkedIn. Todo post necesita `thumbnail` (4:3).
- Para sumar un post a la cola: `python3 bin/linkedin_post.py --enqueue slug-1 slug-2 ...`; ver lo que saldría:
  `python3 bin/linkedin_post.py --plan`. No editar `posted.json` a mano salvo para reenviar u omitir un post.
- Corrida de prueba: `gh workflow run linkedin.yml` (por defecto es simulación y no llama a LinkedIn).
- `bin/linkedin_activate.sh` (setup, status, enable, pause) lo corre **Matías** en su terminal: ahí pasa el token. No
  ejecutarlo ni reproducir sus pasos por él. Modo del link: variable `LINKEDIN_LINK_MODE` (`card` por defecto, o `comment`).
- Si el workflow falla con 401 o avisa que el token vence, avisarle a Matías: solo él puede generar el token.

## Reglas

- Idioma: español, con tildes correctas.
- No incluir datos de clientes ni de empleadores actuales o anteriores, ni material confidencial.
- Si un post contiene `{{` o `{%` (código, plantillas), envolver ese fragmento en `{% raw %}...{% endraw %}`.
- Posts con `tags:` y `description:` en el front matter: la portada y el blog los muestran.
- Vista previa local: `docker compose up` y abrir http://localhost:8080
- No agregar plugins ni dependencias sin consultarlo: el sitio debe seguir simple.
- Commits con el mail noreply de GitHub (ya configurado en este repo), nunca un mail laboral.
