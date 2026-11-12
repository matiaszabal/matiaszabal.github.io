---
layout: post
title: "Tres formas de armar el lado servidor de MCP: FastMCP, MCP Toolbox y servidores de terceros"
date: 2026-11-23 05:30:00 -0300
description: "Cuándo escribir tu propio servidor MCP en Python, cuándo declarar SQL en un YAML y cuándo consumir un servidor que ya existe."
thumbnail: /assets/img/tres-formas-de-armar-el-lado-servidor-de-mcp-fastmcp-toolbox-y-terceros/thumb.jpg
---

Al empezar con MCP aparece una pregunta práctica: el agente es el cliente, ¿y el servidor de dónde sale? En el curso trabajamos con **tres respuestas distintas**, y conviene saber en qué se diferencian antes de elegir.

## 1. FastMCP: el servidor lo escribís vos

FastMCP es un framework de la comunidad, no de Google ni de ADK, para escribir servidores MCP en Python. Se inspira en la ergonomía de FastAPI: decoradores, *type hints* y *docstrings* generan el esquema de cada herramienta.

Un servidor MCP define tres primitivas, y FastMCP tiene un decorador para cada una:

| Decorador | Primitiva | Para qué sirve |
|---|---|---|
| `@mcp.tool` | Tool | Una función que el modelo puede invocar con argumentos |
| `@mcp.resource` | Resource | Un dato de lectura direccionado por URI, para dar contexto |
| `@mcp.prompt` | Prompt | Una plantilla de mensaje parametrizada |

Para un agente conversacional lo que importa casi siempre es la primera: el modelo «hace cosas». Resources y prompts pesan más en clientes tipo IDE, que navegan contexto sin gastar una llamada a herramienta.

Dos capacidades útiles que mostré en clase:

- **Convertir una API existente.** `FastMCP.from_fastapi(app=...)` toma una aplicación FastAPI y convierte cada ruta en una herramienta, sin reescribir la lógica. Existe el equivalente `from_openapi` a partir de la especificación.
- **Componer.** `mount` permite combinar varios servidores en uno, o usar FastMCP como *proxy* entre transportes.

Un detalle de arquitectura: FastMCP solo aparece del lado servidor. El agente ADK que lo consume sigue usando su cliente MCP genérico, sin importar en qué esté escrito el servidor.

## 2. MCP Toolbox for Databases: SQL declarado, sin código de servidor

El Toolbox de Google es un binario independiente, escrito en Go, que convierte consultas SQL declaradas en un archivo YAML en un servidor MCP. No escribís código de servidor: describís las fuentes y cada herramienta.

```yaml
tools:
  get-ticket-by-id:
    kind: postgres-sql
    source: postgresql
    description: Retrieve a ticket's details using its unique ID.
    parameters:
      - name: ticket_id
        type: string
    statement: SELECT * FROM tickets WHERE ticket_id = $1;
```

El `$1` es un parámetro ligado: la herramienta no interpola cadenas, lo que cierra por diseño la vía clásica de inyección SQL. Además, el cliente permite **fijar parámetros del lado del código** (`bound_params`), de modo que, por ejemplo, un `tenant_id` nunca lo decida el modelo.

Un punto que confunde por el nombre: en ADK, el Toolbox **no se consume con el cliente MCP genérico**, sino con `toolbox_core.ToolboxSyncClient`, que devuelve funciones invocables normales. Por debajo habla MCP, pero esa conversación queda encapsulada.

Un problema real que tuvimos: la versión del binario que indicaba el README del ejemplo (0.6.0) hablaba una versión vieja del protocolo y el cliente actual la rechazó con un error de versión. Hubo que bajar a la 1.11.0. Es un recordatorio de que MCP es un protocolo versionado y que un servidor desactualizado puede romper la compatibilidad.

## 3. Servidores de terceros: no escribís nada

Muchos servidores ya existen: el de Google Maps, el de GitHub, uno de Airbnb de la comunidad. El agente es puro cliente. En el ejemplo de Maps, el servidor es un paquete de npm que se lanza con `npx`, y el código del agente nunca importa FastMCP.

## Cómo elegir

| | FastMCP | MCP Toolbox | Terceros |
|---|---|---|---|
| Quién escribe la lógica | Vos, en Python | Nadie: SQL en YAML | Otro |
| Sirve para | Cualquier lógica propia | Bases de datos | Capacidades que ya existen |
| Control | Total | Alto sobre el SQL | Solo el que ofrezca el cliente |
| Riesgo principal | Tu propio código | Consultas mal diseñadas | La confianza en un tercero |

La última fila es la que conecta con seguridad: usar un servidor ajeno es adoptar su código y sus permisos. Por eso conviene acotar lo que el agente ve de él (tema del próximo post de la serie).

## Qué es opinión y qué no

- Lo descrito de FastMCP y del Toolbox sale de mis notas de clase, verificadas en su momento con las versiones instaladas (FastMCP 3.4.2, Toolbox 1.11.0). Son proyectos que evolucionan y las firmas pueden haber cambiado.
- La conversión de FastAPI se probó con una aplicación de ejemplo de dos rutas, no con una API real.
- La tabla de comparación y los criterios de elección son mi lectura didáctica, no una recomendación de los proyectos.
