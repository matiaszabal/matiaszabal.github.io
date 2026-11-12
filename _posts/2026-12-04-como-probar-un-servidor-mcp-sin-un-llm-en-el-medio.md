---
layout: post
title: "Cómo probar un servidor MCP sin un LLM en el medio"
date: 2026-12-04 05:30:00 -0300
description: "Un cliente mínimo con el SDK de MCP para verificar el handshake, el listado de herramientas, una llamada y la validación del esquema, sin credenciales ni red."
thumbnail: /assets/img/como-probar-un-servidor-mcp-sin-un-llm-en-el-medio/thumb.jpg
---

Cuando un agente falla al usar una herramienta MCP, hay dos sospechosos: el modelo o el servidor. Probar el servidor de forma aislada descarta uno. Para eso alcanza un cliente mínimo, sin LLM, sin credenciales y sin red.

## El servidor de ejemplo

En el curso uso un servidor de clima escrito con FastMCP, con datos simulados de ciudades argentinas y tres herramientas: clima actual, pronóstico y lista de ciudades disponibles.

## El cliente de prueba

Usa las mismas piezas del SDK de MCP que `McpToolset` emplea por debajo del lado del agente: un transporte STDIO que lanza el servidor como subproceso y una sesión de cliente.

```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    params = StdioServerParameters(command="python3", args=["weather_mcp_server.py"])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()          # handshake

            tools = await session.list_tools()
            print("TOOLS:", [t.name for t in tools.tools])

            ok = await session.call_tool("get_current_weather", {"city": "Buenos Aires"})
            print(ok.content[0].text)

            bad = await session.call_tool("get_current_weather", {"city": "Tucumán"})
            print(bad.isError, bad.content[0].text)

asyncio.run(main())
```

## Qué verifica

1. **El handshake** de inicialización entre cliente y servidor.
2. **El descubrimiento:** que las herramientas esperadas aparezcan en `list_tools`.
3. **Una llamada válida:** que devuelva el contenido esperado.
4. **La validación del esquema:** una ciudad fuera de la lista permitida debería devolver un error (`isError`) y no un resultado inventado.

El cuarto punto es el más valioso para un agente: si el servidor valida su entrada, el modelo recibe un error claro y puede corregirse.

## Por qué sirve

- Es rápido y determinista: no depende de un modelo ni de la red.
- Separa responsabilidades: si esta prueba pasa y el agente igual falla, el problema está en las instrucciones, en el modelo o en la configuración del cliente.
- Es una base para pruebas automáticas del servidor antes de conectarlo a un agente.

## Qué es opinión y qué no

- El script y el servidor están en mi material del Módulo 4. En este post muestro una versión abreviada y **no reproduzco aquí una salida concreta**: conviene correrlo en tu entorno.
- Que la validación del enumerado devuelva `isError` depende de cómo esté definido el servidor y de la versión de FastMCP.
- Probar el servidor de forma aislada no garantiza que un modelo lo use bien. Son dos verificaciones distintas.
