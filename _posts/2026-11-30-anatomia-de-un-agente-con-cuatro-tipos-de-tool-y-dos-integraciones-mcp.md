---
layout: post
title: "Anatomía de un agente con cuatro tipos de tool y dos integraciones MCP"
date: 2026-11-30 05:30:00 -0300
description: "Un agente de soporte de ejemplo de google/adk-samples que mezcla funciones nativas, AgentTool, LangChain, MCP Toolbox y GitHub MCP, y por qué no necesita múltiples agentes."
thumbnail: /assets/img/anatomia-de-un-agente-con-cuatro-tipos-de-tool-y-dos-integraciones-mcp/thumb.jpg
---

El *Software Bug Assistant* del repositorio `google/adk-samples` es un agente de soporte de IT para una empresa ficticia de cafeteras. Triagea, busca, crea y actualiza tickets de bugs y complementa su base interna con búsqueda web. Lo uso en el Módulo 4 del curso porque, siendo **un solo agente sin jerarquía**, combina cuatro tipos de herramienta distintos.

## Un único nivel, muchas fuentes

No hay transferencia de turno ni subagentes. Las capacidades se aplanan en una sola lista y es el modelo el que decide, turno a turno, cuál usar, incluso varias en el mismo turno (por ejemplo, buscar un ticket similar y, si no existe, crear uno nuevo). Es el contraejemplo del otro ejemplo del módulo, *travel-concierge*, que resuelve el mismo tipo de problema con una arquitectura multiagente.

## Las cinco fuentes

| Tipo | Mecanismo en ADK | Cómo se invoca |
|---|---|---|
| Función nativa | Función de Python | Llamada directa, mismo proceso |
| Búsqueda en Google | `AgentTool` | Un agente aparte que devuelve texto al padre |
| Herramienta de LangChain | `LangchainTool` | Se adapta la interfaz y se invoca como una nativa |
| MCP Toolbox | `ToolboxSyncClient` | Llamadas MCP internas contra Postgres |
| GitHub MCP | `McpToolset` | JSON-RPC por HTTP *streaming* |

Un detalle que me gusta mostrar: la búsqueda de Google está envuelta en un agente aparte por una **restricción técnica**, no por preferencia de diseño. La herramienta integrada de búsqueda solo puede convivir con otras si es la única del agente. De ahí que `AgentTool` tenga una razón de ser concreta.

## Las dos integraciones MCP, de tipos distintos

1. **MCP Toolbox**, con SQL declarado en YAML sobre Postgres. Se consume con un cliente específico, no con `McpToolset`. El parámetro ligado (`$1`) es la mitigación estructural contra inyección SQL.
2. **GitHub MCP remoto**, con `McpToolset` y un `tool_filter` restringido a lectura: de las decenas de herramientas del servidor real, el agente solo ve las de consulta.

Que dos integraciones MCP se consuman con clientes distintos es una fuente frecuente de confusión entre los alumnos.

## Construcción defensiva

Cada integración se arma dentro de un bloque `try` y el agente solo agrega lo que está disponible. Si falta Postgres, el token de GitHub o `npx`, el agente igual carga.

## RAG, la pieza que no se ve en local

La herramienta `search-tickets` usa búsqueda vectorial sobre la descripción del bug para encontrar duplicados o similares. Requiere la extensión de Cloud SQL con Vertex AI y `pgvector`, así que no funciona con el Postgres local plano del curso. La nombro en clase, pero no se puede demostrar en vivo.

## Qué es opinión y qué no

- Mi informe se basa en el README y el código del ejemplo, y las integraciones locales las corrí en mi máquina. **La búsqueda vectorial y el despliegue en Cloud Run o Agent Engine no los ejecuté.**
- El ejemplo es de Google y puede haber cambiado desde que lo revisé.
- Que este diseño de un solo agente sea preferible a uno multiagente no está demostrado aquí: es un contraste didáctico, no una comparación medida.
