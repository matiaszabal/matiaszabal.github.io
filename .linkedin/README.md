# Publicación automática en LinkedIn

Cada vez que se despliega el sitio, el job `linkedin` de `.github/workflows/pages.yml` ejecuta
`bin/linkedin_post.py`, que publica en tu perfil de LinkedIn los posts nuevos del blog.

## Cómo funciona

1. Después del deploy, el script lee `_posts/` y compara con `.linkedin/posted.json`.
2. Un post es **nuevo** si su slug no está en ese registro. Los 16 posts que existían al activar esto quedaron
   como `baseline` y no se publican.
3. Para cada post nuevo: sube la miniatura (`thumbnail`) a LinkedIn y crea un post de tipo artículo con el
   link, el título y la descripción. LinkedIn no lee el link por su cuenta, por eso el script envía todo.
4. Anota el resultado en `posted.json` y el robot lo guarda en `main` (commit `LinkedIn: registrar publicaciones`).

Se saltea, sin fallar, un post con fecha futura (sale cuando se publique en el sitio), con `linkedin: false`,
o cuya URL todavía no responde 200 (se reintenta en la próxima corrida; el workflow corre en cada push y todos
los días a las 09:00 UTC). Publica como máximo 3 posts por corrida.

## Puesta en marcha (una sola vez, la hacés vos)

Las credenciales son tuyas: no las pegues en el chat con Claude. Hacé estos pasos en tu terminal.

1. **Crear la app**: https://www.linkedin.com/developers/apps → *Create app*. LinkedIn suele pedir asociarla a
   una Página de empresa; si no tenés una, podés crear una vacía.
2. **Agregar productos** (pestaña *Products* de la app):
   - **Share on LinkedIn**: da el permiso `w_member_social`, necesario para publicar.
   - **Sign In with LinkedIn using OpenID Connect**: da `openid` y `profile`, necesarios para saber tu id.
3. **Generar el token**: https://www.linkedin.com/developers/tools/oauth/token-generator → elegí tu app y los
   tres permisos `openid`, `profile` y `w_member_social` → copiá el token. **Dura 60 días.**
4. **Obtener tu id de miembro**:
   ```bash
   LINKEDIN_ACCESS_TOKEN='pegá-el-token-acá' python3 bin/linkedin_post.py --whoami
   ```
5. **Guardar los secretos en GitHub** (cada comando te pide el valor; no queda en el historial):
   ```bash
   gh secret set LINKEDIN_ACCESS_TOKEN
   gh secret set LINKEDIN_PERSON_ID
   gh variable set LINKEDIN_TOKEN_EXPIRES_AT --body 2027-01-05   # fecha de hoy + 60 días
   ```
6. **Probar sin publicar**: `gh workflow run pages.yml -f linkedin_dry_run=true` y mirar el log del job
   `linkedin`.

Hasta completar los pasos 1 a 5, el job corre y no hace nada (avisa «LinkedIn no está configurado»).

## Renovar el token (cada 60 días)

LinkedIn no entrega tokens de renovación a apps comunes: hay que repetir los pasos 3 y 5 (solo
`LINKEDIN_ACCESS_TOKEN` y la fecha de `LINKEDIN_TOKEN_EXPIRES_AT`). El job avisa antes de que venza:

- 10 días o menos: anotación amarilla en el run.
- 5 días o menos: el job **falla a propósito** (después de publicar lo que corresponda) para que GitHub te mande
  un mail.
- Vencido: falla sin intentar publicar.

## Opciones por post (front matter)

| Campo | Efecto |
|---|---|
| `linkedin: false` | El post no sale en LinkedIn |
| `linkedin_text: "..."` | Texto propio para el comentario del post. Los caracteres reservados de LinkedIn se escapan solos |
| `thumbnail: /assets/img/.../thumb.jpg` | Imagen que se sube como miniatura (4:3) |

Sin `linkedin_text`, el texto es «Nuevo en el blog: {título}» seguido de la descripción.

## Mantenimiento

- **Reenviar un post**: borrar su entrada de `posted.json`, commit y push.
- **Omitir un post existente**: agregar `"slug-del-post": {"status": "baseline"}` en `posted.json`.
- **Versión de la API**: el encabezado `Linkedin-Version` está en `pages.yml` (`202610`). LinkedIn retira las
  versiones viejas (la 202511 se da de baja el 16/11/2026): hay que subirla de vez en cuando.
- **Límite de LinkedIn**: 150 requests por día y por miembro. Cada post usa 3.
- **Pruebas**: `python3 -m unittest bin/test_linkedin_post.py -v` (usa un servidor falso, no toca LinkedIn).

## Lo que no se pudo probar contra LinkedIn real

Todo el flujo se probó contra un servidor falso que valida la secuencia de llamadas, los encabezados y el
contenido de cada petición, con la documentación oficial como referencia. No se hizo ninguna llamada real. El
primer post real conviene mirarlo: si LinkedIn rechaza algo (por ejemplo la forma de subir la imagen, que la
documentación describe con POST pero su ejemplo hace PUT), el log del job muestra la respuesta completa.
