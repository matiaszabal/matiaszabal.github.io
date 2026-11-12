---
layout: post
title: "McpToolset en ADK: el cliente MCP genérico y cómo acotar lo que el agente ve"
date: 2026-11-26 05:30:00 -0300
description: "Los tres transportes, el filtro de herramientas, la autenticación dinámica y por qué acotar un servidor de terceros es una decisión de seguridad."
thumbnail: /assets/img/mcptoolset-en-adk-el-cliente-mcp-generico-y-como-acotarlo/thumb.jpg
---

`McpToolset` es el cliente MCP genérico de ADK: se conecta a un servidor (propio o de terceros, en cualquier lenguaje), descubre sus herramientas y se las presenta al agente como si fueran funciones nativas. Este post resume su API y, sobre todo, las opciones que sirven para **acotar** lo que el agente puede hacer.

## Una nota de nombres

En la versión de ADK que usé (2.2.0), `MCPToolset` con «CP» en mayúsculas es un alias deprecado de `McpToolset`: emite una advertencia y llama a la clase real. Aparece todavía en varios ejemplos y en el material del lab. Un buen dato para clase: en un SDK que evoluciona rápido, hasta la capitalización de una clase puede cambiar entre versiones.

## Lo único obligatorio: cómo llegar al servidor

El parámetro `connection_params` define el transporte:

| Clase | Transporte | Cuándo |
|---|---|---|
| `StdioConnectionParams` | STDIO, un subproceso local | El agente lanza el servidor (un script de Python, un paquete de npm) |
| `SseConnectionParams` | HTTP con Server-Sent Events | Servidor remoto, versión más antigua del transporte HTTP |
| `StreamableHTTPConnectionParams` | HTTP *streaming* | Servidor remoto persistente, el recomendado hoy |

## Acotar: `tool_filter`

Un servidor puede exponer más herramientas de las que querés darle al agente. `tool_filter` acepta una lista de nombres permitidos o un predicado. En el ejemplo del servidor remoto de GitHub, el filtro deja solo operaciones de lectura (buscar repositorios, listar issues, ver pull requests), aunque el servidor también tenga herramientas de escritura:

```python
McpToolset(
    connection_params=StreamableHTTPConnectionParams(
        url="https://api.githubcopilot.com/mcp/",
        headers={"Authorization": "Bearer " + github_token},
    ),
    tool_filter=["search_repositories", "search_issues", "list_issues",
                 "get_issue", "list_pull_requests", "get_pull_request"],
)
```

Es el principio de mínimo privilegio aplicado a un servidor que no controlás: las herramientas de escritura existen, pero el agente ni se entera. Y la decisión queda en el código del agente, no delegada al modelo.

## Autenticación por sesión: `header_provider`

Para transportes HTTP, en lugar de fijar un encabezado al construir el cliente, `header_provider` es una función que ADK ejecuta en cada llamada y que puede leer del contexto de la invocación. En un agente con varios usuarios, cada sesión puede usar su propio token sin crear un `McpToolset` por usuario.

## Otras opciones

- `tool_name_prefix`: agrega un prefijo a los nombres, útil para evitar colisiones entre servidores.
- `require_confirmation`: pide confirmación antes de ejecutar una herramienta.
- `auth_scheme` y `auth_credential`: autenticación estructurada.

## Un patrón defensivo

En los ejemplos del curso, cada integración se arma dentro de un bloque `try` y el agente filtra los resultados nulos antes de armar su lista de herramientas. Si falta `npx` o el servidor no arranca, el agente igual carga, solo que sin esa capacidad.

## Qué es opinión y qué no

- Las firmas las verifiqué en su momento con `inspect.signature()` sobre ADK 2.2.0. Pueden haber cambiado en versiones posteriores.
- Que `tool_filter` sea una buena práctica de seguridad es mi lectura: **no reemplaza** la autenticación ni los permisos del lado del servidor. Si el token tiene permisos de escritura, el filtro del cliente es la única barrera.
- No probé `require_confirmation` ni las opciones de autenticación estructurada en un caso real.
