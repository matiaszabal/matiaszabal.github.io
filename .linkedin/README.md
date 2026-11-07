# Publicación automática en LinkedIn (1 post por día)

El workflow `.github/workflows/linkedin.yml` corre todos los días a las 09:30 (hora de Argentina; GitHub puede
demorarlo unos minutos) y ejecuta `bin/linkedin_post.py`. Publica **como máximo un post por día** en tu perfil.
No toca el sitio: el deploy es otro workflow (`pages.yml`).

## Estado actual: PAUSADO

- No hay credenciales de LinkedIn cargadas y el interruptor `LINKEDIN_ENABLED` no está definido. Mientras no
  hagas la puesta en marcha de abajo, el workflow corre, muestra el plan y no publica nada.
- La cola tiene 4 posts, en este orden (uno por día):
  1. `las-empresas-dicen-que-mitigan-riesgos-de-ia`
  2. `seguridad-y-gobernanza-en-arquitectura-de-ia-agentica`
  3. `memoria-en-adk-cuatro-capas`
  4. `evaluar-agentes-en-adk-lo-que-ya-viene-nativo`
- Los textos (`linkedin_text` en el front matter de cada post) son **borradores sin aprobar**. Se escribieron solo
  con hechos de los propios posts: ni tu perfil de voz ni tu banco de historias están completos
  (`filled: no`), así que no llevan ninguna anécdota personal. Revisalos y cambialos antes de activar.

## Cómo decide qué publicar

1. Primero la **cola** (`status: queued` en `posted.json`, por `order`) y después los **posts nuevos** del blog
   (los que no están en el registro), por fecha.
2. Si ya se publicó el tope del día (`LINKEDIN_MAX_PER_DAY`, 1), no hace nada hasta mañana. El día cuenta en hora
   de Argentina.
3. Se saltea, sin fallar, un post con fecha futura, con `linkedin: false` o cuya URL todavía no responde 200.
4. Sube la miniatura (`thumbnail`) y crea un post de tipo artículo (link, título, descripción e imagen). LinkedIn no
   lee el link por su cuenta: el script envía todo.
5. Anota el resultado en `posted.json` y el robot lo guarda en `main` (`LinkedIn: registrar publicaciones`).

## Poner en marcha (lo hacés vos, en tu terminal; no pegues credenciales en el chat)

1. **Crear la app**: https://www.linkedin.com/developers/apps → *Create app*. Suele pedir una Página de empresa
   asociada; podés crear una vacía.
2. **Productos** (pestaña *Products*): **Share on LinkedIn** (da `w_member_social`) y **Sign In with LinkedIn using
   OpenID Connect** (da `openid` y `profile`).
3. **Token**: https://www.linkedin.com/developers/tools/oauth/token-generator → tu app → permisos `openid`,
   `profile` y `w_member_social`. **Dura 60 días.**
4. **Tu id de miembro**: `LINKEDIN_ACCESS_TOKEN='...' python3 bin/linkedin_post.py --whoami`
5. **Secretos**:
   ```bash
   gh secret set LINKEDIN_ACCESS_TOKEN
   gh secret set LINKEDIN_PERSON_ID
   gh variable set LINKEDIN_TOKEN_EXPIRES_AT --body AAAA-MM-DD   # hoy + 60 días
   ```
6. **Probar sin publicar**: `gh workflow run linkedin.yml` (por defecto es simulación) y mirar el log.
7. **Revisar los textos**: `python3 bin/linkedin_post.py --plan` muestra cada salida tal como se enviaría.
8. **Encender**: `gh variable set LINKEDIN_ENABLED --body true`. **Apagar**: `... --body false`.

## Cola y textos

- Armar o reordenar la cola: `python3 bin/linkedin_post.py --enqueue slug-1 slug-2 slug-3` (el orden es el de
  salida). Un post ya publicado no se vuelve a encolar.
- `linkedin_text` admite `#etiqueta`: el script la convierte en hashtag real. El resto de los caracteres
  reservados de LinkedIn se escapa solo. Sin `linkedin_text`, el texto es «Nuevo en el blog: {título}» más la
  descripción.
- `linkedin: false` saca un post de LinkedIn.
- Tus reglas de voz (`~/.claude/linkedin-shared/voice-rules.md`) piden **el link en el primer comentario y no en
  el cuerpo**. Hoy el link va dentro del post, como tarjeta de artículo (el texto no lo repite). Pasarlo a un
  comentario requiere el permiso `w_member_social_feed` de la API de comentarios, que no se pudo confirmar que
  esté disponible para una app sin aprobación. **Decisión pendiente.**

## Renovar el token (cada 60 días)

LinkedIn no da tokens de renovación a apps comunes: repetir los pasos 3 y 5 (token y fecha). Avisos: 10 días o
menos, anotación amarilla; 5 días o menos, el job falla a propósito para que GitHub te mande un mail; vencido,
falla sin publicar.

## Mantenimiento

- **Reenviar un post**: borrar su entrada de `posted.json`, commit y push.
- **Omitir uno**: `"slug": {"status": "baseline"}` en `posted.json`.
- **Versión de la API**: `Linkedin-Version` está en `linkedin.yml` (`202610`). LinkedIn retira versiones viejas
  (la 202511 se da de baja el 16/11/2026).
- **Límites**: 150 requests por día y por miembro; cada post usa 3.
- **Pruebas**: `python3 -m unittest bin/test_linkedin_post.py -v` (servidor falso, no toca LinkedIn).
- Si el repo pasa 60 días sin actividad, GitHub desactiva los workflows programados.

## Lo que no se pudo probar contra LinkedIn real

Todo se probó contra un servidor falso, con la documentación oficial como referencia; no se hizo ninguna llamada
real. En el primer post real conviene mirar el log: si LinkedIn rechaza algo (por ejemplo la subida de la imagen,
que la documentación describe con POST y cuyo ejemplo hace PUT), ahí queda la respuesta completa.
