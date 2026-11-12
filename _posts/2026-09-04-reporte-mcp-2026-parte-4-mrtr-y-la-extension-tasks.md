---
layout: post
title: "Reporte MCP 2026 - Parte 4: MRTR y la extensión Tasks"
date: 2026-09-04 09:00:00 -0300
description: "El patrón Multi Round-Trip Requests reemplaza los requests anidados servidor→cliente, deprecan Sampling, Roots y Logging, y Tasks pasa a ser una extensión con polling explícito."
thumbnail: /assets/img/reporte-mcp-2026-parte-4-mrtr-y-la-extension-tasks/thumb.jpg
tags: [mcp, mrtr, elicitation, tasks, reporte-mcp-2026]
---

*Cuarto artículo de la serie **Reporte MCP 2026** ([índice en la Parte 1](/posts/2026/reporte-mcp-2026-parte-1-panorama-y-adopcion/)). Las referencias del tipo «§3.1» remiten a las secciones del reporte.*

## 3.3 El patrón Multi Round-Trip Requests (MRTR): elicitation reconstruida, sampling y roots deprecados

El cambio individual más disruptivo de 2026-07-28 es la introducción del patrón Multi Round-Trip Requests (MRTR, SEP-2322), que reemplaza por completo la forma en que MCP manejaba los requests iniciados por el servidor (`roots/list`, `sampling/createMessage`, `elicitation/create`). Antes de este cambio, esos requests se enviaban como mensajes JSON-RPC anidados servidor→cliente sobre la misma conexión bidireccional abierta, un diseño incompatible con el modelo stateless descrito en §3.1, porque exigía mantener un canal de vuelta (*back-channel*) vivo durante todo el intercambio.

Bajo MRTR, cuando un servidor necesita información adicional para completar una operación (`tools/call`, `prompts/get` o `resources/read`), responde con un `InputRequiredResult`, identificado por un nuevo campo obligatorio `resultType: "input_required"` en todos los resultados del protocolo. Ese resultado incluye un mapa `inputRequests` con las solicitudes pendientes (de tipo elicitation, sampling o roots) y, opcionalmente, un campo `requestState`: un blob opaco, cuya integridad el servidor debe proteger criptográficamente (AEAD o HMAC) si de él depende lógica de autorización, y que el cliente debe repetir byte-exacto en el reintento sin inspeccionarlo.

El cliente resuelve las solicitudes pendientes (con el usuario, o automáticamente si actúa como agente) y reintenta la operación original con un nuevo `id` de JSON-RPC, adjuntando `inputResponses` y el `requestState` recibido. El servidor completa la operación con esa información, sin haber mantenido ningún estado propio entre ambas llamadas: el `requestState` es lo único que sobrevive el intervalo, y vive del lado del cliente.

### La contracara: Roots, Sampling y Logging deprecados

La introducción de MRTR vino acompañada, bajo la misma política de ciclo de vida, de la deprecación de tres funcionalidades (SEP-2577): Roots, Sampling y Logging. Las tres permanecen funcionales durante una ventana de doce meses, pero la especificación desaconseja explícitamente su adopción en implementaciones nuevas y sugiere alternativas:

- En lugar de **Roots:** pasar directorios o archivos como parámetros de tool, URIs de recursos o configuración de servidor.
- En lugar de **Sampling:** integrar directamente con la API del proveedor de LLM.
- En lugar de **Logging:** loguear a `stderr` (stdio) o usar OpenTelemetry.

(Model Context Protocol Specification, 2026.)

Es importante notar que Sampling y Roots no fueron «migrados» a MRTR de forma directa. Elicitation sí lo fue, como mecanismo con reemplazo activo, pero Sampling y Roots quedaron sin sucesor dentro del núcleo del protocolo: la especificación delega esa responsabilidad a la capa de aplicación.

### Un matiz de implementación en los SDKs

En la práctica, esto produce un matiz técnico no evidente a primera lectura de la documentación. Los SDKs oficiales (verificado sobre el SDK de Python, versión 2.2.0) conservan un método de conveniencia `ctx.elicit()` que sigue usando el mecanismo viejo, de conexión bidireccional, y que por lo tanto requiere que el cliente declare la capacidad de elicitation desde el handshake, aunque ya no hay handshake en el sentido estricto de §3.1: el chequeo de capacidad persiste.

El mecanismo nuevo, basado en MRTR, se implementa en cambio mediante un sistema de inyección de dependencias (`Resolve(...)` / `Elicit(...)`) que decide en tiempo de ejecución, según la versión de protocolo negociada con cada cliente, si debe empaquetar la solicitud dentro de un `InputRequiredResult` o enviarla como request anidado al estilo antiguo. Dicho de otro modo: el mismo SDK expone dos implementaciones de «elicitation» con comportamientos de red distintos, y el atajo más documentado (`ctx.elicit()`) es, hoy, el que no implementa el patrón que la especificación vigente recomienda.

### Explicación intuitiva: la pausa y el reintento, en una imagen

Vale la pena volver sobre el mismo patrón con otro nivel de abstracción, remarcando qué problema resuelve y cómo se ve en la práctica.

**El problema que resuelve.** En las revisiones anteriores a 2026-07-28, cuando un servidor necesitaba información adicional del cliente en medio de una ejecución (para una elicitation o para consultar roots, por ejemplo) enviaba un request anidado servidor→cliente sobre la misma conexión abierta. Ese diseño exigía mantener un canal de vuelta activo y estado en memoria del lado del servidor, lo que impedía distribuir el tráfico detrás de un balanceador de carga estándar (§3.1).

Bajo MRTR, la interacción se desacopla completamente del estado del servidor mediante una pausa y un reintento del cliente:

```text
[Cliente / Agente]                                         [Servidor MCP]

   | --- (1) tools/call (ej. "transfer_funds") ------------>  |
   | <-- (2) InputRequiredResult ---------------------------  |
   |         - resultType: "input_required"                   |
   |         - inputRequests: [ { elicitation_params } ]      |
   |         - requestState: "blob_encriptado_AEAD"           |
   |                                                          |
   |   (el cliente resuelve la petición con el usuario)       |
   |                                                          |
   | --- (3) tools/call (reintento, nuevo RPC id) --------->  |
   |         - inputResponses: [ { datos_solicitados } ]      |
   |         - requestState: "blob_encriptado, idéntico"      |
   | <-- (4) resultado final ---------------------------------|
```

Cuatro pasos, mecánicamente:

1. **Pausa de la operación.** Cuando el servidor necesita interactuar con el cliente, responde deteniendo el flujo y marcando el resultado con `resultType: "input_required"`, en lugar de bloquear la conexión esperando una respuesta.
2. **Transferencia de estado al cliente.** En vez de guardar el progreso en memoria del servidor, este empaqueta el estado de la ejecución en un blob opaco (`requestState`), protegido criptográficamente (AEAD o HMAC) cuando su contenido lo amerita (§3.5).
3. **Reintento desacoplado.** El cliente resuelve la solicitud pendiente (por ejemplo, pidiéndole al usuario una confirmación o un dato faltante) y vuelve a invocar la herramienta con un nuevo `id` de JSON-RPC, adjuntando las respuestas (`inputResponses`) y devolviendo el `requestState` byte por byte intacto.
4. **Reanudación sin estado.** El servidor valida la integridad del `requestState`, recupera el contexto de la ejecución, aplica las respuestas recibidas y completa la tarea.

Tres beneficios arquitectónicos se derivan directamente de este diseño:

- **Compatibilidad con transporte stateless.** La llamada (1) puede aterrizar en una instancia del servidor (un contenedor en Cloud Run, por ejemplo, §5.4) y el reintento (3) en una instancia totalmente distinta, sin bases de datos compartidas ni *sticky sessions* de por medio.
- **La misma familia de cambios que deprecó Sampling y Roots.** MRTR no «reemplazó» a Sampling y Roots de forma directa (a diferencia de Elicitation, que sí tiene un sucesor operativo en MRTR). Ambos quedaron sin sucesor dentro del núcleo del protocolo, deprecados por una SEP distinta pero contemporánea (SEP-2577, frente a SEP-2322 para MRTR). Es razonable leer la introducción de MRTR como la pieza de diseño que hizo viable deprecar, en conjunto, el modelo bidireccional viejo.
- **Gobernanza.** Permite que proxies e intermediarios (un Gateway MCP, una capa de OPA/Rego, §5.5) inspeccionen el `requestState` y el contenido de la petición pendiente, e intercedan en el intercambio antes de que el flujo continúe hacia la infraestructura interna. Es, de hecho, el mecanismo concreto detrás de la «inspección contextual bajo MRTR» descrita en §5.5.

## 3.4 La extensión Tasks: orquestación asíncrona de operaciones de larga duración

Para operaciones que no pueden resolverse en el ciclo de vida de un único request-response (una suite de tests, un pipeline de ETL, un escaneo de seguridad), MCP contaba con un soporte experimental de *tasks* dentro del núcleo del protocolo. La revisión 2026-07-28 lo removió del núcleo y lo reconstituyó como una extensión oficial (`io.modelcontextprotocol/tasks`, SEP-2663), con un rediseño relevante:

- El método bloqueante `tasks/result` fue reemplazado por polling explícito vía `tasks/get`.
- Se agregó `tasks/update` para que el cliente pueda enviar input adicional a una tarea en curso.
- Se removió `tasks/list`.
- Los servidores pueden ahora devolver identificadores de tarea sin que el cliente haya optado explícitamente por ese modo de antemano.

El efecto neto es coherente con el resto de la revisión: mover Tasks de un modelo que asumía una conexión viva y vigilante a un modelo de polling compatible con un protocolo sin sesiones.

---

**Anterior:** [Parte 3: autorización OAuth y agentes sin humano](/posts/2026/reporte-mcp-2026-parte-3-autorizacion-oauth-y-agentes-sin-humano/) · **Siguiente:** [Parte 5: semántica del protocolo y señales de riesgo](/posts/2026/reporte-mcp-2026-parte-5-semantica-del-protocolo-y-senales-de-riesgo/)
