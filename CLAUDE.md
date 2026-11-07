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

## Front matter

```yaml
---
layout: post
title: "Título"
date: 2026-11-06 09:00:00 -0300
tags: [agentes, evaluación]
---
```

## Reglas

- Idioma: español, con tildes correctas.
- No incluir datos de clientes ni de empleadores actuales o anteriores, ni material confidencial.
- Si un post contiene `{{` o `{%` (código, plantillas), envolver ese fragmento en `{% raw %}...{% endraw %}`.
- Posts con `tags:` y `description:` en el front matter: la portada y el blog los muestran.
- Vista previa local: `docker compose up` y abrir http://localhost:8080
- No agregar plugins ni dependencias sin consultarlo: el sitio debe seguir simple.
- Commits con el mail noreply de GitHub (ya configurado en este repo), nunca un mail laboral.
