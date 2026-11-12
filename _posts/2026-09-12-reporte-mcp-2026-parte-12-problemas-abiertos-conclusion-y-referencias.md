---
layout: post
title: "Reporte MCP 2026 - Parte 12: problemas abiertos, conclusión y referencias"
date: 2026-09-12 09:00:00 -0300
description: "Cierre de la serie: descubrimiento de agentes, identidad, autorización granular y observabilidad siguen sin resolverse; la conclusión del reporte, una nota pedagógica y las referencias."
thumbnail: /assets/img/reporte-mcp-2026-parte-12-problemas-abiertos-conclusion-y-referencias/thumb.jpg
tags: [mcp, a2a, identidad, observabilidad, reporte-mcp-2026]
---

*Último artículo de la serie **Reporte MCP 2026** ([índice en la Parte 1](/posts/2026/reporte-mcp-2026-parte-1-panorama-y-adopcion/)). Las referencias del tipo «§5.9» remiten a las secciones del reporte.*

## 6. Problemas abiertos

### 6.1 Descubrimiento de agentes a escala de Internet: lo que las Agent Cards no resuelven

Las Agent Cards de A2A (documentos que describen las capacidades, el endpoint y los requisitos de autenticación de un agente) resuelven el problema de «cómo me conecto a este agente que ya sé que existe», no el de «qué agentes existen que podrían servir para esta tarea» (Zylos Research, 2026a). No existe, al momento de este reporte, un equivalente funcional a un DNS o un motor de búsqueda para agentes a escala de Internet abierta; el descubrimiento sigue dependiendo de que el agente consumidor ya conozca, de antemano, la URL o el registro donde publicarse.

### 6.2 Identidad: ¿reemplazará la identidad descentralizada (W3C DIDs) al modelo OAuth actual?

La pregunta que originalmente motivó esta sección del reporte (si la identidad descentralizada reemplazará a OAuth) tiene, con la evidencia disponible, una respuesta más matizada que un sí o un no. Un análisis reciente sobre estándares y vacíos de identidad de agentes de IA (Vaidya, 2026) caracteriza el desajuste estructural de OAuth para este dominio: el estándar «maneja bien la delegación de un solo salto» pero «carece de encadenamiento multi-salto y de flujos asíncronos entre dominios», porque fue diseñado asumiendo un evento de consentimiento humano síncrono y una delegación de un cliente a un único servidor de recursos, mientras que los agentes operan de forma asíncrona, a través de múltiples servicios, en cadenas de delegación.

MCP y A2A extienden OAuth hacia el dominio agéntico, pero ambos heredan debilidades: las Agent Cards de A2A son autodeclaradas, sin atestación de terceros sobre procedencia o comportamiento real, y las verificaciones de seguridad de OAuth 2.1 «terminan en el límite del servidor de recursos», sin capacidad de prevenir ataques de *confused deputy* donde un agente correctamente autenticado es engañado para hacer un mal uso de privilegios legítimos que sí posee.

Las identidades descentralizadas (W3C DIDs) y las credenciales verificables se proponen como alternativa: iniciativas como ProvenAI o el marco MCP-I, donado al Decentralized Identity Foundation en marzo de 2026, buscan emitir credenciales criptográficamente firmadas directamente a agentes, sin depender de un proveedor de identidad centralizado. Pero el mismo análisis identifica limitaciones estructurales serias en este enfoque:

- Pese a la retórica descentralizada, la gobernanza de la infraestructura de DIDs (registros de métodos, marcos de confianza, listas de revocación) sigue requiriendo autoridades coordinadoras.
- Las pruebas de conocimiento cero (ZKPs) ocultan el contenido de una credencial pero no el patrón de eventos de verificación: a una tasa estimada de 144 identidades de máquina por cada humano en entornos empresariales, cada llamada de API deja un mapa de comportamiento observable.
- Sobre todo, ninguna prueba criptográfica de identidad resuelve el problema de fondo: un agente secuestrado por prompt injection, que conserva credenciales válidas y un hash de modelo correcto, sigue siendo indetectable por estos medios, porque las credenciales prueban qué dice ser un agente, no qué va a hacer.

El mismo trabajo identifica, además de la brecha de «verificación de intención semántica», otras cuatro:

- **Rendición de cuentas en delegación recursiva:** solo 24,4 % de las organizaciones relevadas reporta visibilidad sobre la comunicación agente-a-agente.
- **Integridad de identidad del agente:** los agentes son clonables y no deterministas, por lo que una credencial no puede probar unicidad de instancia, habilitando ataques Sybil a velocidad de máquina.
- **Opacidad de gobernanza:** 82 % de confianza declarada en la gobernanza de agentes, contra apenas 47,1 % de agentes efectivamente monitoreados. El estudio lo llama «la paradoja de la aplicación»: exigir cumplimiento estricto empuja a despliegues de «agentes en la sombra» fuera de todo registro, generando exactamente la evasión que se buscaba evitar.
- **Sostenibilidad operacional:** el costo computacional agregado de verificación de confianza cero a escala nunca fue medido.

La conclusión del propio análisis es que extender marcos de identidad humana a agentes «sin modificación estructural produce fallas sistemáticas», y que el campo necesita investigación fundacional que trate estas brechas como condiciones de borde, no como backlog de ingeniería (Vaidya, 2026).

### 6.3 Autorización granular y observabilidad: vacíos que ningún protocolo cubre todavía

Dos limitaciones adicionales, más acotadas mecánicamente que la anterior pero igualmente sin resolver a nivel de protocolo.

**Primero,** los scopes de OAuth no tienen un mecanismo estándar para mapearse a las capacidades específicas de un agente (qué tool, con qué parámetros, en qué contexto), lo que deja la autorización de grano fino como responsabilidad íntegra de cada implementación de gateway (§5.1). Un patrón concreto que emergió para llenar ese vacío, motores de políticas externos como OPA/Rego actuando de Policy Decision Point frente al Gateway, se describe en §5.5 (Parte 9).

**Segundo,** ningún protocolo de los revisados en este reporte exige logging estructurado u observabilidad estandarizada. La revisión 2026-07-28 de MCP dio un paso parcial al documentar convenciones (no obligatorias) para propagar contexto de traza de OpenTelemetry (`traceparent`, `tracestate`, `baggage`) en el campo `_meta`, pero se trata de una convención opcional, no de un mandato (Model Context Protocol Specification, 2026). El «problema de la costura» señalado en §4.3 (fallas que escalan de forma superlineal en sistemas multi-agente) hace que este vacío de observabilidad sea, posiblemente, el más urgente de resolver en despliegues de producción reales.

La evidencia empírica de §5.9 (Parte 11) agrega un matiz incómodo a esta lista: el vacío de autorización granular no es solo un problema de estándares por resolver, sino uno de decisiones que mayoritariamente no se están tomando en el punto donde todavía podrían tomarse. Cuando la falla dominante en servidores desplegados es un plano de control expuesto por completo bajo una credencial compartida, la ausencia de un mecanismo estándar para mapear scopes a capacidades deja de ser la restricción activa.

## 7. Conclusión: MCP como infraestructura asentada, la conversación que se mueve un nivel arriba

La tesis con la que se suele resumir el momento actual de MCP (que dejó de discutirse y se volvió la pieza «de abajo», no cuestionada, de la arquitectura agéntica, mientras la conversación se movió un nivel arriba hacia la coordinación entre agentes) resiste el escrutinio de este reporte, con matices que vale la pena remarcar.

- Es cierta en el plano de la **gobernanza** (MCP, A2A y los remanentes de lo que fue ACP conviven hoy, en su mayoría, bajo el mismo paraguas institucional) y en el plano de la **adopción bruta** (servidores publicados, descargas de SDK).
- Es más matizada en el plano de la **adopción productiva real** (todavía minoritaria según las encuestas disponibles).
- Es llamativamente distinta en el plano **técnico**, donde MCP no se «asentó» en absoluto: la revisión 2026-07-28 es, en varios sentidos, un rediseño del núcleo del protocolo (transporte, gestión de estado, y el mecanismo mismo por el cual un servidor le pide algo a un cliente) más profundo que cualquiera de las revisiones anteriores desde el lanzamiento.

Y es, además, parcialmente inexacta en el plano de los protocolos vecinos: la simplificación de «tres capas» (MCP, A2A, ACP) que sirvió para explicar el ecosistema durante buena parte de 2026 ya no describe con precisión lo que hay. ACP, en sus dos encarnaciones más citadas, dejó de existir como proyecto propio independiente.

Lo que queda, con la evidencia reunida en este reporte, es un ecosistema más simple de lo que la literatura divulgativa todavía asume (MCP + A2A como par dominante), pero con una lista de problemas sin resolver (identidad de agentes en cadenas de delegación, descubrimiento a escala de Internet, autorización granular, observabilidad de sistemas multi-agente) que son, estructuralmente, más difíciles que cualquiera de los que el protocolo ya resolvió, porque exigen coordinación entre organizaciones que no comparten una única autoridad, ni siquiera neutral.

## 8. Nota pedagógica: qué de este análisis es arquitectura y qué resuelve el SDK

Vale la pena cerrar con una distinción útil para cualquiera que esté estudiando arquitectura de agentes a partir de este reporte, porque no todo el nivel de detalle técnico reunido acá tiene el mismo valor pedagógico. Conviene separarlo en tres capas.

**Capa 1: el modelo mental (imprescindible, aunque el SDK lo esconda).** Que MCP sea stateless desde la revisión 2026-07-28 (sin sesiones, sin handshake, con MRTR reemplazando el request anidado servidor→cliente, §3.1 y §3.3) es algo que un SDK abstrae completamente en el código: nadie que use `@mcp.tool()` de un lado y un cliente del otro arma a mano el JSON-RPC. Pero el modelo que hay detrás sí importa para diseñar bien un sistema, más allá de que el código lo oculte. Que no haya estado a nivel de conexión implica que no podés asumir ningún tipo de confianza persistente entre requests, y que una pausa para confirmación humana (elicitation vía MRTR) es un ciclo asincrónico con una request nueva, no una llamada bloqueante. Son decisiones de diseño que, si no se entienden, generan arquitecturas mal pensadas aunque el código «funcione».

**Capa 2: las implicancias de seguridad y gobernanza (imprescindible).** Todo lo desarrollado en la sección 5 (por qué un Gateway centraliza RBAC y audit logging, por qué los resource indicators de OAuth 2.1, RFC 8707, atan un token a un servidor específico, por qué el modelo de *confused deputy* sigue sin resolverse del todo aunque haya Gateways y motores de políticas de por medio, §6.2) es exactamente el tipo de razonamiento que no cambia según qué SDK se use, porque son decisiones de arquitectura y de gobernanza, no de implementación. Un sistema puede estar perfectamente codificado y seguir siendo inseguro si quien lo diseñó no entendió estas implicancias. La evidencia de §5.9 es, en rigor, la mejor defensa disponible de esta afirmación: en un corpus de 89 servidores reales, los problemas graves de gobernanza aparecen mayoritariamente en código sin ningún defecto de programación.

**Capa 3: el detalle de protocolo puro (opcional, de referencia).** El path exacto de un endpoint, si una respuesta es `application/json` o `text/event-stream`, si un POST devuelve 202 o no, los números de SEP y las fechas de cada cambio (buena parte de §3.1): todo esto lo resuelve el SDK en el 99 % de los casos. Tiene sentido conocerlo si vas a auditar tráfico crudo, construir un Gateway propio o escribir políticas de validación contra el *wire format* directamente; no hace falta memorizarlo para diseñar o evaluar un sistema agéntico en general.

### Material para practicar: detectar capa 3 desactualizada en una fuente real

Un buen ejercicio de lectura crítica es cruzar material educativo público contra la especificación vigente y notar qué tan rápido se desactualiza el detalle de protocolo puro (capa 3), incluso en fuentes de buena calidad. El [MCP Course de Hugging Face](https://huggingface.co/learn/mcp-course/) es un caso instructivo, precisamente porque el resto de su contenido es sólido: al momento de escribir este reporte, buena parte de sus páginas describe la generación de transporte y de ciclo de vida anterior a 2025-03-26, no la vigente. Los puntos concretos, verificados página por página contra la especificación 2026-07-28:

- `unit1/communication-protocol` (Hugging Face, s.f.-a): describe el ciclo de vida de la interacción en cuatro fases (inicialización → discovery → ejecución → terminación), que dejó de existir con 2026-07-28.
- `unit1/mcp-clients` (Hugging Face, s.f.-b): afirma sin matices que «el tipo de transporte es stdio o sse», sin mencionar Streamable HTTP.
- `unit1/architectural-components`: el flujo de comunicación describe un paso de conexión previo al discovery, cuando el modelo vigente no tiene conexión que establecer.
- `unit1/capabilities` y `unit1/key-concepts`: describen sampling como un request anidado servidor→cliente sobre una conexión abierta, sin mencionar el reemplazo por MRTR (§3.3).
- `unit1/gradio-mcp`, `unit1/unit1-recap`, `unit2/clients`, `unit2/gradio-server`, `unit2/gradio-client`, `unit2/tiny-agents`, `unit2/lemonade-server`: repiten, en distintas variantes, HTTP+SSE (o directamente `"transport": "sse"`) como si fuera el transporte remoto vigente, sin mencionar que fue deprecado a favor de Streamable HTTP desde 2025-03-26.
- `unit1/quiz2`: una respuesta de autoevaluación presenta HTTP+SSE y Streamable HTTP como dos opciones equivalentes y vigentes, en lugar de una vigente y una deprecada.
- `unit3/build-mcp-server`: usa `await context.session.list_roots()` dentro de una tool, un patrón de sesión persistente que ya no existe bajo el modelo stateless.

El ejercicio no es «encontrar errores» por deporte: es practicar el hábito, necesario en un campo que cambia a este ritmo, de tratar cualquier fuente secundaria sobre MCP con una fecha de verificación explícita (no solo una fecha de publicación) antes de confiar en su descripción de la capa 3.

### Ejercicios opcionales

**Capa 3, sobre tráfico real.** Levantar un servidor MCP mínimo de prueba, capturar el intercambio JSON-RPC real entre cliente y servidor (por ejemplo, interceptando el transporte stdio o inspeccionando las requests HTTP si se usa Streamable HTTP), identificar a mano qué modo de respuesta usó el servidor para cada request (`application/json` frente a `text/event-stream`) y escribir una política mínima de validación (por ejemplo, con OPA/Rego, §5.5, o con un validador Pydantic sobre el `inputSchema`, §5.6) que rechace cualquier mensaje sin el envelope `_meta` completo. Es un ejercicio pensado para quien vaya a construir o auditar infraestructura de MCP directamente, no un requisito para entender el resto de este reporte.

**Capa 2, sin leer código vulnerable.** Tomar un servidor MCP público cualquiera, propio o de un tercero, y clasificarlo contra las tres capas de la taxonomía de §5.9 sin mirar su código en busca de bugs: ¿cuánto del plano de control de la API subyacente quedó expuesto como herramientas? ¿Bajo qué identidad se ejecuta cada una, y qué mutaciones tienen compuerta humana? ¿Usa annotations de riesgo, y son honestas? Después, mapear los hallazgos contra las categorías del OWASP MCP Top 10 descritas en §5.8. Es un ejercicio deliberadamente de capa 2: no requiere leer una línea de código vulnerable para producir un diagnóstico de gobernanza útil, que es precisamente el punto que la evidencia de §5.9 sostiene.

## 9. Referencias

- Basar, M. (2026). *ACP Is Not One Protocol: A Chronological Guide to Four Different ACPs — and Where Acp.Net Fits.* Medium. <https://medium.com/@mertbasar30/acp-is-not-one-protocol-a-chronological-guide-to-four-different-acps-and-where-acp-net-fits-41952bfef80e>
- ChatForest (2026). *Salesforce Summer '26 Agentforce Multi-Agent Orchestration: Atlas 3.0, A2A, MCP, and the Seam Problem.* <https://chatforest.com/builders-log/salesforce-summer-26-agentforce-multi-agent-orchestration-atlas-a2a-mcp-builder-guide/>
- digitalapplied.com (2026). *MCP Adoption Statistics 2026: Model Context Protocol.* <https://www.digitalapplied.com/blog/mcp-adoption-statistics-2026-model-context-protocol>
- Google Cloud (2026a). *MCP supported products.* <https://docs.cloud.google.com/mcp/supported-products>
- Google Cloud (2026b). *Using the fully managed remote BigQuery MCP server to build data & AI agents.* <https://cloud.google.com/blog/products/data-analytics/using-the-fully-managed-remote-bigquery-mcp-server-to-build-data-ai-agents>
- Google Cloud (2026c). *Agent Registry overview.* <https://docs.cloud.google.com/agent-registry/overview>
- Google Cloud (2026d). *Model Armor.* <https://cloud.google.com/security/products/model-armor>
- Google Cloud (2026e). *MCP support for Apigee.* <https://cloud.google.com/blog/products/ai-machine-learning/mcp-support-for-apigee>
- Google Cloud (2026f). *Apigee MCP overview.* <https://docs.cloud.google.com/apigee/docs/api-platform/apigee-mcp/apigee-mcp-overview>
- GitHub — Model Context Protocol (2025). *SEP-1287: WebSocket transport for MCP* (cerrada sin fusionarse, 3 dic. 2025). <https://github.com/modelcontextprotocol/modelcontextprotocol/pull/1287>
- Google for Developers (2026). *Configure MCP servers (Google Workspace).* <https://developers.google.com/workspace/guides/configure-mcp-servers>
- Hugging Face (s.f.-a). *MCP Course — Unit 1: Communication Protocol.* Consultado en septiembre de 2026. <https://huggingface.co/learn/mcp-course/unit1/communication-protocol>
- Hugging Face (s.f.-b). *MCP Course — Unit 1: MCP Clients.* Consultado en septiembre de 2026. <https://huggingface.co/learn/mcp-course/unit1/mcp-clients>
- LF AI & Data (2025). *ACP Joins Forces with A2A.* <https://lfaidata.foundation/communityblog/2025/08/29/acp-joins-forces-with-a2a-under-the-linux-foundations-lf-ai-data/>
- Linux Foundation (2025). *Linux Foundation Announces the Formation of the Agentic AI Foundation (AAIF).* <https://www.linuxfoundation.org/press/linux-foundation-announces-the-formation-of-the-agentic-ai-foundation>
- Linux Foundation (2025). *Linux Foundation Welcomes the AGNTCY Project to Standardize Open Multi-Agent System Infrastructure.* <https://www.linuxfoundation.org/press/linux-foundation-welcomes-the-agntcy-project-to-standardize-open-multi-agent-system-infrastructure-and-break-down-ai-agent-silos>
- MintMCP (2026). *7 top MCP gateways for enterprise AI infrastructure.* <https://www.mintmcp.com/blog/enterprise-ai-infrastructure-mcp>
- Model Context Protocol (2026). *Understanding MCP clients.* <https://modelcontextprotocol.io/docs/2026-07-28/learn/client-concepts>
- Model Context Protocol Blog (2025). *MCP joins the Agentic AI Foundation.* <https://blog.modelcontextprotocol.io/posts/2025-12-09-mcp-joins-agentic-ai-foundation/>
- Model Context Protocol Blog (2026). *The 2026-07-28 Specification.* <https://blog.modelcontextprotocol.io/posts/2026-07-28/>
- Model Context Protocol Specification (2026). *Key Changes (2026-07-28 changelog).* <https://modelcontextprotocol.io/specification/2026-07-28/changelog>
- Model Context Protocol Specification (2026). *Authorization.* <https://modelcontextprotocol.io/specification/draft/basic/authorization>
- Model Context Protocol Specification (2026). *Multi Round-Trip Requests.* <https://modelcontextprotocol.io/specification/draft/basic/patterns/mrtr>
- Model Context Protocol Specification (2026). *Transports — Streamable HTTP.* <https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/streamable-http>
- Open Policy Agent (s.f.). *Rego v1.* Consultado en septiembre de 2026. <https://www.openpolicyagent.org/docs/opa-1>
- OWASP Foundation (s.f.). *OWASP MCP Security Taxonomy* (repositorio de GitHub; documento `MCP-SECURITY-TAXONOMY-COMPLETE.md`, versión v0.1). Consultado en septiembre de 2026. <https://github.com/OWASP/MCP-Taxonomy>. El repositorio remite además al proyecto OWASP MCP Top 10, <https://owasp.org/www-project-mcp-top-10/>, como marco de mapeo.
- quasa.io (2026). *A2A Joins AAIF, While MCP Retains a Different Role.* <https://quasa.io/insights/a2a-joins-the-agentic-ai-foundation-mcp-still-solves-a-different-problem>
- The Next Platform (2025). *Cisco's Outshift Incubator Sends Agentic AI Protocol To The Linux Foundation.* <https://www.nextplatform.com/ai/2025/07/29/ciscos-outshift-incubator-sends-agentic-ai-protocol-to-the-linux-foundation/100917>
- Vaidya, et al. (2026). *AI Identity: Standards, Gaps, and [open problems].* arXiv:2604.23280. <https://arxiv.org/pdf/2604.23280>
- Zabaljáuregui, M. (2026). *SoK: Beyond the Threat Catalog—An Empirical Taxonomy of Authorization Governance and Containment Failures in Model Context Protocol Servers.* Manuscrito en revisión por pares (double-blind).
- Zylos Research (2026a). *Agent Interoperability Protocols 2026: MCP, A2A, ACP and the Path to Convergence.* <https://zylos.ai/research/2026-03-26-agent-interoperability-protocols-mcp-a2a-acp-convergence/>
- Zylos Research (2026b). *Agent-to-Agent Communication Protocols: A2A, MCP, and Multi-Agent Orchestration.* <https://zylos.ai/research/2026-05-16-agent-to-agent-communication-protocols-a2a-mcp/>

## Nota metodológica

Este reporte se construyó a partir de fuentes secundarias (blogs técnicos, análisis de mercado, cobertura especializada) y de las especificaciones primarias de MCP disponibles públicamente en modelcontextprotocol.io. Varias fuentes citadas son análisis independientes no revisados por pares (Zylos Research, digitalapplied.com, ChatForest, quasa.io, Medium); se las señala como tales y se las usó por ser, al momento de la redacción, las fuentes más recientes y específicas disponibles sobre eventos de 2026. Algunas afirmaciones (particularmente las cifras de adopción de §2.1 y el estado de AGNTCY en §4.1) se beneficiarían de una segunda ronda de verificación directa contra fuentes primarias.

Las dos subsecciones de §5.8 y §5.9 tienen estatus de evidencia distinto entre sí y conviene no homogeneizarlas:

- **§5.8** se apoya en una fuente primaria verificada directamente: el archivo `MCP-SECURITY-TAXONOMY-COMPLETE.md` del repositorio OWASP/MCP-Taxonomy, leído en su totalidad. Los nombres y números de las diez categorías del Top 10, los once dominios de primer nivel, los siete dominios legados, las etiquetas de causa raíz y los destinos de crosswalk están transcritos de ese archivo, no reconstruidos de memoria. En cambio, la asignación de cada componente del pipeline de §5.1–§5.6 a una categoría del Top 10 es una lectura propia de este reporte, y se la marca como tal en la tabla correspondiente. El documento de OWASP se encuentra además en estado v0.1 y se autodescribe como referencia combinada, por lo que la numeración y los nombres de categoría podrían cambiar.
- **§5.9** se apoya en un manuscrito en revisión por pares del propio autor de este reporte, todavía no publicado ni evaluado externamente: se lo cita señalando explícitamente ese estado, y trasladando los calificadores que el propio manuscrito impone a sus hallazgos (muestra por conveniencia, verificación de un solo revisor, y la cifra de «menos del 10 %» presentada como cota inferior sobre bugs detectados y no como estimación de prevalencia). El conflicto de interés es evidente y se declara: el autor del reporte es el autor del trabajo citado.

---

**Anterior:** [Parte 11: evidencia empírica de 89 servidores](/posts/2026/reporte-mcp-2026-parte-11-evidencia-empirica-de-89-servidores/) · **Índice de la serie:** [Parte 1](/posts/2026/reporte-mcp-2026-parte-1-panorama-y-adopcion/)
