---
layout: post
title: "Reporte MCP 2026 - Parte 8: gateways, sandboxing y prompt injection"
date: 2026-09-08 09:00:00 -0300
description: "Qué hace un MCP Gateway en producción, por qué el límite de seguridad real está en el sandboxing del host, por qué el protocolo no resuelve el prompt injection indirecto y cómo se compone el patrón en Google Cloud."
thumbnail: /assets/img/reporte-mcp-2026-parte-8-gateways-sandboxing-y-prompt-injection/thumb.jpg
tags: [mcp, gateway, sandboxing, prompt-injection, gcp, reporte-mcp-2026]
---

*Octavo artículo de la serie **Reporte MCP 2026** ([índice en la Parte 1](/posts/2026/reporte-mcp-2026-parte-1-panorama-y-adopcion/)). Las referencias del tipo «§5.1» remiten a las secciones del reporte.*

## 5. Seguridad y gobernanza operacional en producción

### 5.1 MCP Gateways: RBAC, audit logging y aislamiento de servidores críticos

Un MCP Gateway es el componente de infraestructura intermediario que actúa como punto de control centralizado (patrón *hub-and-spoke*) entre los clientes MCP (agentes, aplicaciones de IA) y los servidores MCP que exponen herramientas o datos. La práctica que se consolidó durante 2026 en entornos empresariales es evitar precisamente la alternativa: conectar agentes directamente a servidores de infraestructura crítica en un esquema de conexiones punto a punto no gobernadas (N agentes × M servidores), que el Gateway reemplaza por un único punto de entrada que concentra la gestión de tráfico, la seguridad y la observabilidad.

**Funcionalidades técnicas principales:**

- **Aislamiento y enrutamiento centralizado.** Un único endpoint HTTP/Streamable administra el catálogo de servidores disponibles, sin que el código de los agentes necesite conocer la topología real detrás del Gateway.
- **Control de acceso basado en roles (RBAC).** El Gateway expone servidores MCP «virtuales» que filtran dinámicamente la lista que devuelven `tools/list` o `resources/list` según el rol, grupo o permisos de quien consulta: por ejemplo, operaciones de solo lectura para analistas, herramientas de escritura restringidas a administradores autorizados.
- **Patrón de triple compuerta (*triple-gate*).**
  - *Compuerta 1:* filtrado de prompt injection indirecto y exfiltración de PII entre el cliente/LLM y el Gateway.
  - *Compuerta 2:* validación estricta de esquemas JSON (`inputSchema` / `outputSchema`) y autorización granular de tools entre el LLM y el servidor MCP.
  - *Compuerta 3:* autenticación mediante *resource indicators* (§3.2), límites de tasa y gestión de credenciales frente a la API externa que finalmente ejecuta la acción (MintMCP, 2026).
- **Observabilidad y auditoría.** Registro de cada llamada JSON-RPC, solicitud de acceso y cambio de configuración; los productos de este segmento suelen agregar además métricas de latencia y tasa de error, e inyectar metadatos de traza de OpenTelemetry (§6.3), una capa útil para mitigar el «problema de la costura» descrito en §4.3.

**Casos de uso empresariales:**

- **Prevención de servidores «sombra».** Evitar que servidores MCP no verificados se conecten directamente a la red corporativa por fuera del Gateway.
- **Gobierno de credenciales.** Evitar que el contexto del LLM maneje API keys o tokens de infraestructura de forma directa; el Gateway inyecta las credenciales de transporte de forma transparente al agente.
- **Virtualización de entornos.** Redirigir llamadas hacia servidores MCP que corren en contenedores efímeros o microVMs (§5.2) cuando la herramienta requiere ejecución de código arbitrario o manipulación del sistema de archivos.

### Patrón de comunicación: el agente nunca habla directamente con el servidor final

En una arquitectura empresarial desacoplada, toda la comunicación con el servidor MCP final, desde la inspección de capacidades hasta la ejecución de herramientas, pasa por el Gateway como intermediario obligatorio:

1. El agente pide la lista de herramientas al Gateway (`tools/list`).
2. El Gateway repite el descubrimiento contra el o los servidores MCP de origen.
3. Esos servidores devuelven sus esquemas al Gateway.
4. El Gateway responde al agente con una lista «virtual», ya filtrada según el rol del token que presentó.
5. El agente invoca una herramienta (`tools/call`), autenticado con su propio token frente al Gateway.
6. El Gateway reenvía la llamada al servidor final con credenciales de servicio a servicio (*service-to-service*), distintas de las del agente.
7. El servidor final devuelve su resultado en JSON al Gateway.
8. El Gateway devuelve al agente un payload ya sanitizado.

Ese diseño responde a cuatro motivos:

- **Abstracción de red y topología.** El servidor MCP final puede vivir en una subred privada, detrás de un firewall o en un clúster de Kubernetes sin IP pública; el agente solo necesita conocer el endpoint HTTPS del Gateway.
- **Propagación y mapeo de credenciales.** El agente se autentica ante el Gateway con sus propias credenciales (por ejemplo, un rol «agente-analista»); el Gateway valida esa petición e inyecta, por separado, las credenciales de servicio a servicio que hablan con el servidor final (API keys, certificados mTLS, tokens machine-to-machine). Las credenciales sensibles de infraestructura nunca llegan al contexto del agente ni a sus logs.
- **Intercepción y sanitización (patrón triple-gate).** Antes de reenviar la llamada, el Gateway valida que los parámetros de `tools/call` coincidan rígidamente con el `inputSchema` para evitar inyección de parámetros; antes de devolver la respuesta, inspecciona la salida del servidor buscando datos sensibles (PII, secretos) o contenido diseñado para prompt injection indirecto.
- **Administración dinámica de estado (servidores «virtuales»).** Si un servidor entra en mantenimiento o se agrega una réplica, el Gateway gestiona el balanceo y los fallos de forma transparente; para el agente, la lista de herramientas simplemente cambia en el siguiente `tools/list`.

**Excepción: entornos locales.** La única situación donde el agente habla directamente con el servidor MCP, sin Gateway intermedio, es el desarrollo local o de escritorio: por ejemplo, un IDE como Cursor o un cliente como Claude Desktop ejecutando un servidor propio vía transporte stdio (§3.1) en el mismo sistema operativo. En despliegues de producción o de nube distribuida, la intermediación por Gateway es, a 2026, el patrón estándar.

Productos con este perfil (MintMCP Gateway, Docker MCP Gateway, Traefik Hub, Lasso Security, Obot, Lunar.dev MCPX, entre otros) se mencionan aquí como evidencia de que existe ya un mercado de infraestructura de seguridad específico para MCP, no como una recomendación de producto.

### 5.2 Sandboxing: contenedores efímeros, microVMs, y qué reemplaza a Roots ahora que está deprecado

Los servidores MCP que ejecutan código arbitrario o interactúan con el sistema de archivos del host suelen operar dentro de contenedores efímeros o microVMs, restringidos espacialmente por límites que en versiones anteriores de la especificación se comunicaban en parte a través de la primitiva Roots.

Es importante precisar algo que la propia documentación de MCP siempre reconoció y que la deprecación de §3.3 vuelve más relevante todavía: **Roots nunca fue, por diseño, un mecanismo de seguridad en sentido estricto, sino un mecanismo de coordinación.** El servidor «debería» (SHOULD, no MUST) respetar los límites comunicados, precisamente porque el cliente no tiene forma de controlar el código que corre el servidor. «La seguridad real debe imponerse a nivel de sistema operativo, mediante permisos de archivos y/o sandboxing» (Model Context Protocol, 2026).

Con Roots deprecado y sin sucesor directo en el núcleo del protocolo, esa distinción se vuelve el punto central: el límite de seguridad efectivo siempre estuvo, y sigue estando, en la capa de sandboxing del host (contenedor, microVM, permisos de sistema de archivos), no en el protocolo. Lo que cambia es que ahora la especificación deja de sugerir siquiera una convención estándar para comunicar el alcance pretendido, y delega esa comunicación a parámetros de tool, URIs de recursos o configuración de servidor específica de cada implementación.

### 5.3 Prompt injection indirecto: por qué el protocolo no lo resuelve

Ninguna fuente consultada para este reporte, ni la especificación misma ni la literatura de análisis del ecosistema, sostiene que MCP resuelva la mitigación de prompt injection indirecto (instrucciones maliciosas embebidas en el contenido devuelto por una herramienta o un recurso, que el modelo puede interpretar como comandos legítimos). Zylos Research lo señala explícitamente como uno de los vacíos no resueltos del ecosistema de protocolos en su conjunto: «ningún protocolo aborda adecuadamente las respuestas de herramientas que contienen instrucciones maliciosas» (Zylos Research, 2026a).

En la práctica, esa responsabilidad se desplazó a la capa de gateway descrita en §5.1 (filtrado y detección en tiempo real como parte del *triple-gate*) y a prácticas de sanitización del lado del servidor, no a ninguna garantía del protocolo en sí. Esto es coherente con el diseño general que emerge de la revisión 2026-07-28: el núcleo del protocolo se redujo deliberadamente a mecánica de transporte, negociación de capacidades y estructura de mensajes, dejando cada vez más responsabilidades (logging, sanitización, identidad granular) explícitamente fuera de su alcance y del lado de la aplicación.

### 5.4 Caso de referencia: cómo se compone el patrón de Gateway en la práctica, el ejemplo de Google Cloud

En la infraestructura gestionada de Google Cloud conviven dos realidades distintas para MCP. No existe, contra lo que a veces se asume, un único producto con nombre propio del estilo «Vertex MCP Gateway» (una búsqueda específica hecha para este reporte no encontró ningún producto de Google con ese nombre, solo integraciones de terceros), pero el catálogo de servicios de GCP sí permite componer la arquitectura de Gateway descrita en §5.1 combinando piezas nativas de la plataforma.

**Lo que GCP ya ofrece de forma gestionada:**

- **Servidores MCP remotos oficiales.** Google mantiene endpoints MCP remotos y documentados para BigQuery, Cloud Storage, la CLI de gcloud y varios productos de Google Workspace: Gmail y Drive tienen servidores propios (`gmailmcp.googleapis.com`, `drivemcp.googleapis.com`), además de Calendar, Chat y la People API. No hay, en cambio, un servidor MCP separado específicamente para Docs, cuyo acceso queda integrado dentro del servidor de Drive (Google Cloud, 2026a; Google Cloud, 2026b; Google for Developers, 2026).
- **Agent Registry.** Un catálogo centralizado, propio de la plataforma Gemini Enterprise, para registrar, descubrir y gobernar servidores MCP, herramientas y agentes, con su propio endpoint MCP (Google Cloud, 2026c).
- **Control de acceso e identidad (IAM).** Autenticación OAuth 2.1 (§3.2) integrada con la capa IAM de GCP para gobernar qué agente puede invocar qué herramienta.
- **Seguridad de payload (Model Armor).** Un producto real de la familia Security Command Center, no exclusivo de MCP, que inspecciona entradas y salidas de cargas de trabajo de IA para detectar prompt injection, contenido dañino y fuga de datos sensibles, integrado además con Sensitive Data Protection/DLP (Google Cloud, 2026d).

**Lo que queda a cargo de quien despliega.** Aunque GCP provee el registro, los servidores de origen, la sanitización con Model Armor y la autenticación con IAM, el Gateway como proxy unificado (el único endpoint HTTPS del que habla el agente, según el patrón de §5.1) no viene empaquetado como un solo producto: se compone sobre **Apigee**, que Google sí documenta oficialmente combinado con Model Armor, IAM y Sensitive Data Protection/DLP como capas de seguridad para tool-calling vía MCP (Google Cloud, 2026e; Google Cloud, 2026f).

Cloud Run, en cambio, es un complemento razonable para alojar servidores MCP propios detrás de ese mismo Apigee, y aparece documentado así en guías de despliegue de terceros, pero no forma parte de la combinación que Google documenta oficialmente como un patrón único. Vale aquí la misma cautela metodológica de §2.1: no tratar una combinación plausible de servicios como si fuera un producto o una recomendación de arquitectura oficial.

| Componente | ¿Lo provee GCP? | Servicio de GCP asociado |
|---|---|---|
| Descubrimiento y catálogo | Sí | Agent Registry |
| Servidores MCP oficiales | Sí | Remote MCP Servers de Google (BigQuery, Drive, Gmail, Storage, gcloud CLI, entre otros) |
| Seguridad de payload | Sí | Model Armor |
| Autenticación / RBAC | Sí | Google Cloud IAM + OAuth 2.1 |
| Proxy inverso / punto de entrada único | Implementación propia (sobre Apigee) | Apigee, combinado con Model Armor + IAM + Sensitive Data Protection |

No hace falta escribir un Gateway desde cero en código: la combinación que Google documenta oficialmente es Apigee actuando de hub, con Model Armor e IAM como capas de seguridad, consumiendo los servidores MCP remotos gestionados por Google junto con servidores propios alojados, por ejemplo, en Cloud Run.

---

**Anterior:** [Parte 7: MCP, A2A y la capa vertical](/posts/2026/reporte-mcp-2026-parte-7-mcp-a2a-y-la-capa-vertical/) · **Siguiente:** [Parte 9: defensa en profundidad con OPA, Pydantic y Model Armor](/posts/2026/reporte-mcp-2026-parte-9-defensa-en-profundidad-opa-pydantic-y-model-armor/)
