---
layout: post
title: "FunctionTool, AgentTool y MCP: tres formas de darle herramientas a un agente en ADK"
date: 2026-12-03 05:30:00 -0300
description: "Qué cambia (y qué no) entre pasar una función, envolver un agente o conectar un servidor MCP, con una corrección que hice a mis propias notas."
thumbnail: /assets/img/functiontool-agenttool-y-mcp-tres-formas-de-darle-herramientas-a-un-agente/thumb.jpg
---

En ADK hay tres maneras habituales de darle una capacidad a un agente, y las tres terminan en la misma lista `tools=[...]`. Cambian el origen de la capacidad y dónde vive la lógica.

| Mecanismo | De dónde viene la capacidad | Dónde se ejecuta |
|---|---|---|
| `FunctionTool` | Una función de Python | En el mismo proceso |
| `AgentTool` | Otro agente, envuelto como herramienta | Un agente completo corre y devuelve su resultado al padre |
| `McpToolset` | Un servidor MCP, propio o de terceros | En otro proceso o en un servicio remoto |

## FunctionTool: tu función, con su esquema

ADK toma los *type hints* y el *docstring* de una función de Python y genera la declaración que el modelo necesita para saber qué parámetros pasar. Por eso el docstring no es decoración: es lo que el modelo lee para decidir cuándo usarla.

## Una corrección a mis propias notas

En mis notas de clase había escrito que usar `FunctionTool(func=f)` explícito tenía ventajas sobre pasar `tools=[f]`: callbacks, contexto y control del esquema. **Era incorrecto**, y lo comprobé corriendo código: el agente envuelve `tools=[f]` en un `FunctionTool` idéntico al explícito, y los *callbacks* de herramienta (`before_tool_callback`, `after_tool_callback`, `on_tool_error_callback`) viven en el **agente**, no en la herramienta. Se disparan igual con las dos formas. Para una función simple son exactamente lo mismo.

Además, mi fuente original traía varios detalles de API que no existen en ADK 2.2.0. Los conceptos eran correctos, pero la sintaxis estaba inventada, y lo dejé anotado en el documento. Es un buen recordatorio de verificar contra la versión instalada.

## AgentTool: cuando una herramienta es un agente

`AgentTool` expone un agente como si fuera una herramienta. Un caso concreto donde resuelve una restricción técnica y no una preferencia de diseño: la herramienta integrada de búsqueda de Google solo puede convivir con otras si es la única del agente. Para usarla junto a otras, se aísla en un agente propio y se envuelve con `AgentTool`.

## MCP: la capacidad vive afuera

`McpToolset` conecta con un servidor que no controlás y descubre sus herramientas en ejecución. Eso agrega superficie: lo que ese servidor expone es código y permisos ajenos. Por eso conviene acotar lo que el agente ve (`tool_filter`) y auditar las invocaciones con los *callbacks* del agente, que sirven igual para las tres formas.

## Qué es opinión y qué no

- Las comprobaciones sobre `FunctionTool` las hice con ADK 2.2.0; las firmas y comportamientos pueden cambiar en otras versiones.
- La tabla resume mis notas del curso, no la documentación oficial completa.
- No medí diferencias de rendimiento entre los tres mecanismos.
