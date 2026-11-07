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
5. **Publicar un post también lo publica en LinkedIn, solo y sin confirmación** (job `linkedin`, ver abajo).
   Es público e irreversible: por eso el "publicalo" de Matías cubre las dos cosas.
6. Después de cada publicación, el robot agrega un commit a `main` (`LinkedIn: registrar publicaciones`).
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

## LinkedIn automático

Tras cada deploy, `bin/linkedin_post.py` publica en el perfil de Matías los posts cuyo slug no figure en
`.linkedin/posted.json`. Puesta en marcha, renovación del token (cada 60 días) y detalles: `.linkedin/README.md`.

- **Al crear un post, escribir `linkedin_text`**: un gancho de 2 a 4 líneas en la voz de Matías, pensado para
  LinkedIn y no un copia y pega del resumen (usar los skills `linkedin-post-writer` y `linkedin-humanizer`).
  No escapar caracteres a mano: el script lo hace. Sin `linkedin_text`, el texto por defecto es
  «Nuevo en el blog: {título}» más la descripción.
- `linkedin: false` en el front matter evita que un post salga en LinkedIn.
- Todo post necesita `thumbnail` (miniatura 4:3): LinkedIn no lee el link, el script le manda esa imagen.
- No editar `.linkedin/posted.json` a mano, salvo para reenviar un post (borrar su entrada) o para omitir uno
  (agregar `"slug": {"status": "baseline"}`).
- Corrida de prueba sin publicar: `gh workflow run pages.yml -f linkedin_dry_run=true`.
- Si el job `linkedin` falla con 401 o avisa que el token está por vencer, avisarle a Matías: solo él puede
  generar el token nuevo.

## Reglas

- Idioma: español, con tildes correctas.
- No incluir datos de clientes ni de empleadores actuales o anteriores, ni material confidencial.
- Si un post contiene `{{` o `{%` (código, plantillas), envolver ese fragmento en `{% raw %}...{% endraw %}`.
- Posts con `tags:` y `description:` en el front matter: la portada y el blog los muestran.
- Vista previa local: `docker compose up` y abrir http://localhost:8080
- No agregar plugins ni dependencias sin consultarlo: el sitio debe seguir simple.
- Commits con el mail noreply de GitHub (ya configurado en este repo), nunca un mail laboral.
