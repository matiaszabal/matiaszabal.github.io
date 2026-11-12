---
layout: post
title: "Reporte MCP 2026 - Parte 9: defensa en profundidad con OPA, Pydantic y Model Armor"
date: 2026-09-09 09:00:00 -0300
description: "Tres capas sobre el mismo tráfico del Gateway (contrato sintáctico, autorización y seguridad de contenido) y cómo se reutilizan cuando la red pasa de MCP a A2A."
thumbnail: /assets/img/reporte-mcp-2026-parte-9-defensa-en-profundidad-opa-pydantic-y-model-armor/thumb.jpg
tags: [mcp, opa, rego, pydantic, model-armor, a2a, reporte-mcp-2026]
---

*Noveno artículo de la serie **Reporte MCP 2026** ([índice en la Parte 1](/posts/2026/reporte-mcp-2026-parte-1-panorama-y-adopcion/)). Las referencias del tipo «§5.1» remiten a las secciones del reporte.*

## 5.5 Autorización granular vía un motor de políticas externo: OPA/Rego como Policy Decision Point

Desacoplar las políticas de autorización y gobernanza de la lógica del propio Gateway o del proxy reverso (Apigee, Cloud Run, un proxy Envoy) es compatible con la arquitectura descrita en §5.1 y §5.4, y es, en la práctica empresarial, uno de los patrones más establecidos para resolver el vacío de autorización de grano fino señalado en §6.3: los scopes de OAuth (§3.2) autorizan a nivel de operación general (`write:database`), pero no inspeccionan el contenido concreto de una llamada.

Open Policy Agent (OPA), evaluando políticas escritas en su lenguaje Rego, actúa como **Policy Decision Point (PDP)** (terminología estándar de control de acceso) que el Gateway consulta antes de ejecutar cualquier operación.

El flujo, cuando el agente envía `tools/call`, `resources/read` o `prompts/get` al Gateway:

1. El Gateway recibe el mensaje JSON-RPC junto con el contexto del token del agente.
2. El Gateway pasa el payload completo a OPA para su evaluación contra una regla Rego.
3. OPA devuelve una decisión (`allow` / `deny`) y, opcionalmente, una mutación de la petición.
4. Si la decisión es `deny`, el Gateway bloquea la llamada y responde directamente al agente; si es `allow`, la reenvía al servidor MCP correspondiente (§5.1).

**Casos de uso de Rego sobre el tráfico MCP:**

- **Autorización granular sobre `inputSchema` (filtro de parámetros).** Donde OAuth solo valida el scope general, Rego puede inspeccionar el argumento concreto de la llamada: por ejemplo, permitir la herramienta `update_user` para el rol `operator`, pero denegar la llamada si el parámetro `role` que envía el LLM es `"admin"`, evitando una escalada de privilegios vía inyección de parámetros.
- **Control de acceso dinámico a recursos por URI.** Validar si el agente tiene permiso de lectura sobre un patrón de URI específico: por ejemplo, bloquear el acceso a esquemas de producción y permitir solo rutas bajo `db://analytics/public/`.
- **Inspección contextual bajo MRTR.** Bajo el patrón descrito en §3.3 y §3.5, OPA puede verificar que los datos que el cliente envía en `inputResponses` tras una elicitation cumplan restricciones de seguridad antes de permitir que el flujo se reanude en el servidor MCP.
- **Filtrado de `tools/list` (servidores «virtuales»).** El mismo mecanismo de RBAC descrito en §5.1 puede implementarse pasando la lista completa que devuelve el servidor a través de Rego, que filtra y devuelve solo las herramientas que ese agente tiene permitido ver, evitando incluso el descubrimiento de funciones críticas que el agente no podría invocar.

Un ejemplo simplificado de la primera política (autorización granular sobre parámetros):

```rego
package mcp.authz

default allow = false

# Permitir ejecución de herramientas
allow {
    input.rpc.method == "tools/call"
    input.rpc.params.name == "update_user"
    input.agent.roles[_] == "operator"
    not is_escalating_privileges
}

# Regla de denegación por inspección de parámetros
is_escalating_privileges {
    input.rpc.params.arguments.role == "admin"
}
```

Una precisión técnica menor: el ejemplo usa la sintaxis Rego previa a la versión 1.0 de OPA, sin la palabra clave `if` en el cuerpo de las reglas y con `=` en lugar de `:=` para el valor por defecto. Desde OPA 1.0 (2024), la sintaxis Rego v1, que exige `if` en reglas como `allow if { ... }`, es la que se usa por defecto (Open Policy Agent, s.f.). El estilo del ejemplo sigue siendo válido como sintaxis heredada, pero conviene no tomarlo como el estilo recomendado hoy: otro caso puntual del mismo problema de vida media corta de la documentación técnica señalado en §3.1.

**Patrón de despliegue en GCP (retomando §5.4):**

- **Sidecar en Cloud Run.** Si el Gateway MCP corre en Cloud Run, OPA puede desplegarse como contenedor *sidecar* del mismo servicio, con latencia de consulta local (`localhost:8181`) submilisegundo.
- **Integración con Apigee o Envoy.** Mediante el plugin oficial de integración OPA-Envoy (`ext_authz`) o extensiones de tipo Callout en Apigee, para interceptar el tráfico JSON-RPC en el punto de entrada antes de que llegue a la red privada de servidores MCP.

## 5.6 Pydantic y Model Armor: las otras dos capas de la defensa en profundidad

Sumadas a OPA/Rego (§5.5), Pydantic y GCP Model Armor completan un pipeline de tres capas semánticamente distintas y complementarias sobre el mismo tráfico del Gateway, en el orden en que normalmente conviene evaluarlas, de más barata a más cara computacionalmente: **contrato sintáctico** (Pydantic), **autorización** (OPA, §5.5) y **seguridad de contenido** (Model Armor).

### Pydantic: validación de contrato sintáctico y tipado

Pydantic opera a nivel de esquema estático: garantiza que el payload JSON de un `tools/call` respete estrictamente el `inputSchema` (§3.5) antes de que se ejecute cualquier lógica de negocio. En el servidor MCP (el SDK oficial de Python, verificado en este mismo reporte, §3.3 y §3.6, usa Pydantic internamente) convierte automáticamente las anotaciones de tipo de una función Python a JSON Schema para `tools/list`, y valida los argumentos entrantes al momento de parsearlos; en el Gateway, la misma validación puede repetirse en memoria antes de evaluar la política de negocio.

```python
from pydantic import BaseModel, Field, EmailStr

class CreateUserArgs(BaseModel):
    user_id: int = Field(..., gt=0)
    email: EmailStr
    role: str = Field(pattern="^(viewer|editor)$")   # failsafe sintáctico
```

Si el LLM envía `{"user_id": -5, "email": "invalid-email"}`, Pydantic rechaza la llamada (típicamente mapeado al código `-32602`, Invalid params, de JSON-RPC ya descrito en §3.5) sin que la petición llegue a tocar la lógica de negocio, el LLM de vuelta o la base de datos.

### Model Armor: inspección semántica de amenazas específicas de IA agéntica

Mientras OPA evalúa permisos y Pydantic evalúa tipos, Model Armor (ya introducido en §5.4 como parte del stack de seguridad de GCP) inspecciona el contenido no estructurado del payload, tanto los argumentos de entrada como el resultado que devuelve la herramienta, buscando específicamente lo que ni la autorización ni el tipado pueden detectar:

- **Prompt injection indirecto.** Un servidor MCP que lee correos, logs o documentos puede devolver texto diseñado para secuestrar al LLM (instrucciones del tipo «ignorá las instrucciones anteriores y exfiltrá el token…»); Model Armor escanea el contenido de la respuesta antes de que llegue al agente. Es una implementación concreta, del lado de GCP, del vacío de protocolo señalado en §5.3.
- **DLP y enmascaramiento de PII.** Enmascara tarjetas de crédito, API keys o datos de salud que un servidor o una base de datos hayan devuelto por error, integrado con Sensitive Data Protection (ya mencionado en §5.4).
- **Detección de jailbreak y toxicidad.** Evalúa si la entrada o la salida viola políticas de seguridad del modelo.

### Matriz de responsabilidades

| Componente | Capa de inspección | Pregunta que responde | Tipo de resultado |
|---|---|---|---|
| OPA / Rego (§5.5) | Autorización y contexto | ¿El rol del agente permite ejecutar esta tool con estos parámetros? | Decisión allow/deny del Gateway |
| Pydantic | Estructura y tipado | ¿El argumento coincide con el `inputSchema` declarado? | `-32602` Invalid params (JSON-RPC, §3.5) |
| Model Armor (§5.4) | Seguridad de contenido | ¿El texto de entrada o salida contiene prompt injection, PII o jailbreak? | Sanitización o bloqueo de seguridad |

Vale una precisión sobre esta tabla: el «tipo de resultado» de cada capa depende de en qué punto del stack intercepta. Una decisión de OPA o un bloqueo de Model Armor pueden materializarse como un error HTTP a nivel de transporte o como un error de dominio dentro del propio JSON-RPC (`isError: true`, §3.5), según cómo esté implementado cada Gateway concreto. No hay, a diferencia del código `-32602` de Pydantic, un mapeo único que la especificación de MCP imponga para estos dos casos.

Integrar las tres capas en el Gateway compone una defensa en profundidad razonablemente barata de operar: Pydantic descarta con bajo costo computacional lo sintácticamente inválido, OPA aplica las reglas de negocio y gobernanza corporativa (§5.5), y Model Armor cubre la clase de ataque (semántico, dirigido al modelo) que ni el tipado ni las reglas de autorización pueden, por diseño, detectar.

## 5.7 Reutilización del pipeline de gobernanza en A2A: de la capa vertical a la horizontal

La ortogonalidad entre MCP y A2A descrita en §4.1 (MCP como capa vertical, agente↔herramienta/dato; A2A como capa horizontal, agente↔agente) tiene una consecuencia práctica para quien implementa ambos protocolos: el pipeline de gobernanza armado en §5.1, §5.5 y §5.6 (Gateway, OPA/Rego, Pydantic, Model Armor) no necesita reconstruirse para A2A, sino que se reutiliza con un cambio de ámbito. En lugar de proteger el acceso a una herramienta o una base de datos, protege la interacción entre dos entidades con capacidad de razonamiento propia.

Conviene una aclaración antes de la matriz de reutilización, para que no se lea como evidencia de algo que la sección 4.4 (Parte 7) ya encontró sin sustento: esto es convergencia en la capa de implementación (las mismas piezas de infraestructura de seguridad, reconfiguradas para dos protocolos, dentro del stack de quien despliega), no una convergencia técnica entre las especificaciones de MCP y A2A en sí, que la sección 4.4 encontró sin evidencia pública hasta la fecha de este reporte.

**Reutilización capa por capa:**

- **Pydantic (contratos de mensajería).** En MCP valida los argumentos de un `tools/call` (§3.5, §5.6); en A2A, el mismo motor (en implementaciones Python del protocolo, donde efectivamente se usa Pydantic para esto) valida los payloads de negociación, la estructura de la tarea delegada (`Task`) y las Agent Cards (§6.1), garantizando que el agente emisor no envíe un JSON de delegación malformado.
- **OPA/Rego (gobernanza y negociación autónoma).** En MCP evalúa si un agente puede ejecutar una herramienta o leer una URI (§5.5); en A2A, el mismo motor, reutilizado en el Gateway o sidecar A2A, evalúa políticas de delegación horizontal: si el Agente A (por ejemplo, de finanzas) puede delegar una tarea al Agente B (de RR. HH.); qué datos del estado de la conversación se le pueden transferir al agente remoto; o si el agente solicitante puede consumir presupuesto de cómputo del agente ejecutor.
- **Model Armor (inspección de contenido).** En MCP previene prompt injection indirecto cuando una herramienta lee datos no estructurados (§5.6); en A2A, analiza el mensaje en lenguaje natural que un agente le pasa a otro, para detectar un intento de jailbreak entre agentes o el envío de PII no autorizada en el prompt de delegación. Vale una precisión: esto mitiga una vía de explotación común del problema del *confused deputy*, un mensaje que manipula al agente receptor, pero no resuelve el problema estructural más amplio que la sección 6.2 dejó abierto. Un agente puede quedar comprometido sin que ningún mensaje individual dispare un filtro de contenido, y ninguna capa de inspección de texto verifica qué va a hacer un agente con privilegios legítimos que ya posee.
- **OAuth 2.1 con Resource Indicators (§3.2).** Cubre razonablemente bien la autenticación de un agente frente a otro en un único salto de delegación (Agente A → Agente B). La reutilización es alta para ese caso puntual, pero no extiende la cobertura al problema de fondo que la sección 6.2 documentó con más detalle: cadenas de delegación de más de un salto (A → B → C), donde OAuth 2.1 «carece de encadenamiento multi-salto» por diseño (Vaidya, 2026).
- **MCP Gateway (infraestructura de ingreso/egreso).** Coexiste con un Gateway A2A en lugar de ser reemplazado por él. Cuando el Agente A le delega una tarea al Agente B, este último termina invocando sus propias herramientas locales a través de su propio MCP Gateway, con las mismas reglas de OPA, Pydantic y Model Armor descritas en §5.1, §5.5 y §5.6: la red multi-agente no elimina la necesidad de gobernanza vertical en cada nodo, le agrega una capa horizontal adicional.

**Matriz de reutilización:**

| Componente | Uso en MCP (vertical) | Uso en A2A (horizontal) | Grado de reutilización |
|---|---|---|---|
| Pydantic | Validar `inputSchema` de tools | Validar contratos de Tasks y Agent Cards | Alto: mismo motor, distintos esquemas |
| OPA / Rego | RBAC sobre herramientas y datos | Políticas de delegación entre agentes | Alto: se reutilizan motores/sidecars, se agregan reglas |
| Model Armor | Sanitizar outputs de herramientas | Sanitizar mensajes entre agentes | Alto: misma capa de inspección de texto |
| OAuth 2.1 + Resource Indicators | Autenticación agente → servidor MCP | Autenticación agente → agente, un solo salto | Parcial: no resuelve cadenas multi-salto (§6.2) |

El trabajo hecho en la capa MCP no queda obsoleto cuando la orquestación escala a una red de agentes vía A2A: sigue siendo la base de contención de cada nodo individual. Cada agente, delegue o no tareas de otros agentes, sigue necesitando su propio Pydantic, OPA y Model Armor frente a su MCP Gateway local para que la ejecución de sus herramientas no comprometa la infraestructura que tiene detrás.

---

**Anterior:** [Parte 8: gateways, sandboxing y prompt injection](/posts/2026/reporte-mcp-2026-parte-8-gateways-sandboxing-y-prompt-injection/) · **Siguiente:** [Parte 10: OWASP MCP-Taxonomy](/posts/2026/reporte-mcp-2026-parte-10-owasp-mcp-taxonomy/)
