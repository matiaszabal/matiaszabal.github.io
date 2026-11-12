---
layout: post
title: "Reporte MCP 2026 - Parte 3: autorización OAuth y agentes sin humano"
date: 2026-09-03 09:00:00 -0300
description: "OAuth 2.1, Resource Indicators y el problema del confused deputy en MCP, más las opciones de autenticación para agentes headless: client credentials, device grant y SPIFFE/SPIRE."
thumbnail: /assets/img/reporte-mcp-2026-parte-3-autorizacion-oauth-y-agentes-sin-humano/thumb.jpg
tags: [mcp, oauth, identidad, seguridad, reporte-mcp-2026]
---

*Tercer artículo de la serie **Reporte MCP 2026** ([índice en la Parte 1](/posts/2026/reporte-mcp-2026-parte-1-panorama-y-adopcion/)). Las referencias del tipo «§5.1» remiten a las secciones del reporte.*

## 3.2 Autorización: OAuth 2.1, Resource Indicators y el problema del «confused deputy»

La autorización en MCP, opcional para transportes stdio (donde las credenciales se obtienen del entorno) pero recomendada para transportes HTTP, se apoya en OAuth 2.1 y un conjunto acotado de RFCs complementarias: Bearer Token Usage (RFC 6750), Authorization Server Metadata (RFC 8414), Protected Resource Metadata (RFC 9728) y, de forma central para el diseño de seguridad, Resource Indicators for OAuth 2.0 (RFC 8707) (Model Context Protocol Specification, 2026).

El problema concreto que resuelven los *resource indicators* es el siguiente. En un ecosistema donde un mismo servidor de autorización puede emitir tokens válidos para múltiples servidores MCP, un cliente que obtiene un token para el servidor A podría, sin esta protección, reutilizarlo (o un atacante podría robarlo y reutilizarlo) contra el servidor B, si ambos confían en el mismo emisor. El parámetro `resource`, obligatorio tanto en la request de autorización como en la de token, ata criptográficamente el token a la URI canónica del servidor MCP específico para el que fue emitido; el servidor, a su vez, está obligado a validar que él mismo es la audiencia del token antes de aceptarlo.

La revisión 2026-07-28 reforzó además la validación del parámetro `iss` en las respuestas de autorización según RFC 9207, específicamente para mitigar ataques de *mix-up* entre servidores de autorización durante el flujo de PKCE (Model Context Protocol Specification, 2026). En la misma revisión, el registro dinámico de clientes (RFC 7591) pasó a estado deprecado en favor de *Client ID Metadata Documents*, un mecanismo que permite usar directamente una URL HTTPS como identificador de cliente.

### El flujo de autenticación, paso a paso

Cuando el transporte es HTTP/Streamable HTTP (§3.1), la secuencia típica de un cliente que todavía no tiene un token válido es:

1. **Descubre el desafío.** El cliente intenta una operación contra el servidor MCP (por ejemplo, `server/discover`); si se requiere autenticación, el servidor responde `401 Unauthorized`, incluyendo la ubicación de sus metadatos de autorización (RFC 8414 / RFC 9728).
2. **Inicia la autorización.** El cliente arma la *authorization request* usando PKCE (Proof Key for Code Exchange, obligatorio en OAuth 2.1 para evitar la intercepción del código de autorización) y adjunta el parámetro `resource` (RFC 8707) con la URI canónica del servidor MCP de destino.
3. **Consentimiento e intercambio.** Tras el consentimiento del usuario, o la política del sistema, el servidor de autorización devuelve un *authorization code*; el cliente lo intercambia por un *access token* (y un *refresh token*) enviando el *code verifier* correspondiente.
4. **Peticiones autenticadas.** En cada request JSON-RPC posterior, el cliente adjunta el token en la capa de transporte (cabecera `Authorization: Bearer <token>`).

### Tres términos que se confunden: Authorization Code, Access Token y Bearer Token

Vale la pena distinguirlos con precisión, porque cumplen roles distintos dentro del flujo y suelen usarse indistintamente en la literatura divulgativa:

- **Authorization Code:** no es un token con el que se pueda invocar el servidor MCP. Es una credencial opaca, de un solo uso y de vida ultracorta (típicamente segundos o minutos), cuya única función es probar que el usuario completó el login y dio su consentimiento. El Identity Provider (IdP) la entrega en el paso 3 y la destruye apenas el cliente la canjea por un access token.
- **Access Token:** la credencial de autorización propiamente dicha. En la práctica suele ser un JWT firmado criptográficamente por el IdP (por ejemplo, con RS256 o EdDSA), con claims estándar: `iss` (quién lo emitió), `sub` (el usuario o el agente), `aud`/`resource` (la URI canónica exacta del servidor MCP de destino, RFC 8707), `scope` (los permisos concedidos) y `exp`/`iat` (expiración y emisión). El servidor MCP o el Gateway valida la firma contra las claves públicas (JWKS) del IdP y verifica que `aud` coincida con su propia URI, el mismo mecanismo antirreplay ya descrito.
- **Bearer Token:** no es un tercer tipo de credencial, sino el esquema de transmisión HTTP (RFC 6750) que define cómo viaja el access token en cada petición: en la cabecera `Authorization: Bearer <token>`. El nombre describe su modelo de seguridad con precisión: «quien porta esta credencial está autorizado a usarla». A diferencia de esquemas como mTLS o DPoP, el servidor no exige ninguna prueba adicional de posesión de una clave privada en cada request; si el token se filtra, cualquiera que lo tenga puede usarlo hasta que expire.

| Concepto | Tipo de entidad | ¿Quién lo emite? | ¿Dónde se presenta? |
|---|---|---|---|
| Authorization Code | Token opaco, temporal | Identity Provider | Endpoint `/token` del IdP |
| Access Token | Estructura de datos (JWT) | Identity Provider | Validado por el Gateway o el servidor MCP |
| Bearer Token | Esquema de transporte (RFC 6750) | — | Cabecera `Authorization: Bearer <token>` |

Un detalle de diseño que conecta con el resto del pipeline de seguridad (sección 5, Partes 8 y 9): las credenciales y el access token viven exclusivamente en la capa de transporte que gestiona el Host/Cliente MCP. El modelo de lenguaje nunca ve el token ni ningún parámetro de autenticación dentro del `inputSchema` de una herramienta. Es la misma lógica de aislamiento del «gobierno de credenciales» de un Gateway (§5.1), aplicada aquí al propio cliente MCP incluso antes de que exista un Gateway de por medio.

### Una limitación que retomaremos

Estas protecciones operan correctamente dentro del modelo de OAuth (delegación de un solo salto, Usuario → Agente → Servidor MCP, con consentimiento humano síncrono), pero no fueron diseñadas para cadenas de delegación multi-agente más largas (Agente A → Agente B → Servidor MCP), donde un agente A actúa en nombre de un agente B que a su vez actúa en nombre de un usuario humano. Por sí solo, OAuth 2.1 no previene ataques de *confused deputy* cuando un agente correctamente autenticado es manipulado (vía prompt injection, por ejemplo) para ejecutar acciones dentro de un rango de privilegios legítimo pero ajeno al flujo original.

En arquitecturas de producción, esta limitación se complementa con los Gateways y motores de políticas descritos en las secciones 5.1 y 5.5, no con una extensión del propio estándar OAuth. Ese desajuste estructural es, según la literatura reciente sobre identidad de agentes, uno de los motivos por los que se está explorando la identidad descentralizada como alternativa (Vaidya, 2026). Lo retomamos en la sección 6.2 (Parte 12).

## 3.9 Autenticación sin humano en el loop: agentes headless y SPIFFE/SPIRE

El flujo de Authorization Code + PKCE descrito arriba asume, por diseño, un humano completando un login interactivo en un navegador. Para agentes autónomos que corren en segundo plano (*daemons*, servicios de fondo, microservicios en Kubernetes o en un contenedor de Cloud Run, §5.4), sin presencia humana ni navegador, ese flujo no aplica. OAuth 2.1 contempla, para este caso, mecanismos alternativos que MCP hereda tal cual, sin extenderlos ni redefinirlos.

### Tres mecanismos estándar

- **Client Credentials Grant** (`grant_type=client_credentials`): el estándar para comunicación *machine-to-machine*. El agente no pasa por un authorization code: hace un POST directo al endpoint `/token` del servidor de autorización con su `client_id` y `client_secret` (o una aserción de cliente firmada, ver más abajo), sin navegador de por medio.
- **Device Authorization Grant** (RFC 8628, `urn:ietf:params:oauth:grant-type:device_code`): pensado para un agente que arranca en un entorno *headless* (una CLI o terminal sin interfaz gráfica) pero que igual requiere la delegación explícita de un humano. El agente solicita un `device_code` y muestra un `user_code` en la consola; la ejecución queda pausada hasta que el humano aprueba el acceso desde otro dispositivo con navegador.
- **Assertion frameworks / token exchange** (RFC 7523, RFC 8693): el agente no usa un secreto estático. En cambio, presenta una aserción ya firmada por su propio entorno de ejecución (una *workload identity* de Google Cloud, un IAM role de AWS, una service account de Kubernetes) y la intercambia por un access token en el endpoint del servidor de autorización o del Gateway.

### SPIFFE/SPIRE como caso particular del tercer mecanismo

SPIFFE (Secure Production Identity Framework For Everyone) y su implementación de referencia, SPIRE, no reemplazan a OAuth en el Gateway MCP: resuelven la autenticación del agente en la capa de infraestructura, de forma criptográfica y sin secretos estáticos, combinándose con OAuth 2.1 exactamente por la vía de *assertion frameworks* recién descrita. Un SVID (SPIFFE Verifiable Identity Document) puede intervenir en dos niveles:

- **X.509-SVID vía mTLS, en la capa de transporte.** El proceso SPIRE inyecta un certificado X.509 en el propio proceso del agente; el agente abre un canal mTLS contra el Gateway usando ese certificado, y el Gateway lo valida contra la autoridad de certificación del *trust domain* de SPIFFE. La identidad queda respaldada por la infraestructura misma, sin depender de un flujo de usuario.
- **JWT-SVID como client assertion en OAuth 2.1 (`private_key_jwt`).** En lugar de un `client_secret` estático, el agente presenta un JWT-SVID, firmado por la CA de SPIFFE, que lo identifica de forma atestada como, por ejemplo, `spiffe://domain/workload/agent-prod`. Lo envía como `client_assertion` en una petición `client_credentials` (RFC 7523), con el parámetro `resource` (RFC 8707) apuntando a la URI del servidor MCP de destino. El servidor de autorización valida la firma contra el endpoint JWKS de SPIFFE/SPIRE y, si la atestación de la carga de trabajo es válida, emite un access token acotado a esa audiencia.

Vale una precisión: nada de esto está definido dentro de la especificación de MCP en sí. MCP delega la autenticación a OAuth 2.1 (§3.2), y SPIFFE es, en este esquema, simplemente un método más de autenticación de cliente para OAuth (vía `client_assertion`), igual que lo sería un `client_secret` o un `private_key_jwt` convencional. Es, no obstante, el patrón que la literatura de identidad de cargas de trabajo describe como el más cercano a *zero-trust* para agentes autónomos: elimina los secretos estáticos de larga vida (el punto de fuga más común en integraciones M2M) a cambio de una identidad rotada continuamente y atestada por la infraestructura misma.

| Mecanismo | ¿Exige navegador? | Nivel de seguridad | Uso típico |
|---|---|---|---|
| Authorization Code + PKCE (§3.2) | Sí | Alto (delegación de usuario) | Agentes interactivos en apps de escritorio o web |
| Client Credentials con secreto estático | No | Medio (riesgo de fuga de API keys) | Integraciones M2M simples, scripts locales |
| Client Credentials + JWT-SVID (SPIFFE) | No | Alto (zero-trust, rotación continua sin secretos) | Agentes autónomos en Kubernetes o Cloud Run (§5.4) |

---

**Anterior:** [Parte 2: del protocolo con sesión al protocolo stateless](/posts/2026/reporte-mcp-2026-parte-2-del-protocolo-con-sesion-al-protocolo-stateless/) · **Siguiente:** [Parte 4: MRTR y la extensión Tasks](/posts/2026/reporte-mcp-2026-parte-4-mrtr-y-la-extension-tasks/)
