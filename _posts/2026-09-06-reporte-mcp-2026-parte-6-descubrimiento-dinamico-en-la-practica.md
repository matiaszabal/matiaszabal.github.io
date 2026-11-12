---
layout: post
title: "Reporte MCP 2026 - Parte 6: descubrimiento dinámico en la práctica"
date: 2026-09-06 09:00:00 -0300
description: "Dos ejemplos de punta a punta: un agente que incorpora una tool nueva a través de un Gateway sin tocar su código, y el diálogo JSON-RPC crudo sin intermediarios."
thumbnail: /assets/img/reporte-mcp-2026-parte-6-descubrimiento-dinamico-en-la-practica/thumb.jpg
tags: [mcp, gateway, json-rpc, ejemplos, reporte-mcp-2026]
---

*Sexto artículo de la serie **Reporte MCP 2026** ([índice en la Parte 1](/posts/2026/reporte-mcp-2026-parte-1-panorama-y-adopcion/)). Las referencias del tipo «§5.1» remiten a las secciones del reporte.*

## 3.6 Ejemplo ilustrativo: descubrimiento dinámico de una tool nueva vía Gateway

Para hacer concreto el mecanismo de «integración sin código» descrito en §3.5 y §4.2, vale un ejemplo de extremo a extremo: cómo un agente incorpora una herramienta que no existía cuando se escribió su código, sin ningún cambio en ese código, apoyándose en un MCP Gateway (§5.1) como catálogo centralizado.

El patrón general: el agente solo conoce la URL del Gateway y presenta un token OAuth (§3.2); al conectarse, solicita las herramientas disponibles vía JSON-RPC; el Gateway filtra dinámicamente la respuesta según los permisos asociados a ese token, y el agente inyecta los esquemas recibidos en el contexto del LLM en tiempo de ejecución.

**1. El servidor MCP (servicio remoto).** Un equipo publica un nuevo servicio para consultar métricas en tiempo real. No se modifica el agente: solo se registra este servidor en el Gateway.

```python
# postgres_mcp_server.py (corriendo remotamente en la red)

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Metrics-Service")

@mcp.tool()
def query_db_latency(cluster_id: str) -> str:
    """Devuelve la latencia promedio en milisegundos de un cluster de base de datos."""
    # Lógica de consulta a la infraestructura
    return f"Cluster {cluster_id}: 12ms avg latency"

if __name__ == "__main__":
    mcp.run(transport="streamable-http")
```

**2. El agente (código genérico y dinámico).** El código del agente no tiene ninguna referencia a bases de datos ni a `query_db_latency`; solo sabe hablar con la interfaz del Gateway.

```python
import asyncio
from google import genai
from google.genai import types
from mcp import ClientSession
from mcp.client.http import streamable_http_client

GATEWAY_URL = "https://mcp-gateway.internal.corp/v1"
BEARER_TOKEN = "oauth2_access_token_dev_team"

async def main():
    # 1. Conexión de transporte con el MCP Gateway
    headers = {"Authorization": f"Bearer {BEARER_TOKEN}"}
    async with streamable_http_client(GATEWAY_URL, headers=headers) as (read, write):
        async with ClientSession(read, write) as session:

            # 2. Descubrimiento semántico en tiempo de ejecución
            await session.discover()                 # RPC: server/discover
            mcp_tools = await session.list_tools()   # RPC: tools/list

            # 3. Mapeo dinámico de JSON Schemas de MCP a la API del LLM
            llm_declarations = [
                types.FunctionDeclaration(
                    name=tool.name,
                    description=tool.description,
                    parameters=tool.inputSchema,
                )
                for tool in mcp_tools.tools
            ]
            gemini_tools = [types.Tool(function_declarations=llm_declarations)]
            ai_client = genai.Client()

            # 4. Prompt sobre un tema para el que el agente no tenía herramientas al compilar
            prompt = "¿Cómo está la latencia del cluster 'db-primary'?"

            # 5. El LLM ve la herramienta descubierta dinámicamente
            response = ai_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(tools=gemini_tools),
            )

            # 6. Ejecución remota desacoplada (RPC: tools/call)
            if response.function_calls:
                call = response.function_calls[0]
                result = await session.call_tool(call.name, arguments=call.args)
                print(f"[Resultado del Servidor MCP]: {result.content[0].text}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Flujo de descubrimiento

1. **Registrar.** Un ingeniero añade el servidor `Metrics-Service` al Gateway y le asigna el scope `read:metrics`.
2. **Conectar.** El agente arranca, presenta su `BEARER_TOKEN` al Gateway e invoca `tools/list`.
3. **Filtrar.** El Gateway valida que el token tiene el scope `read:metrics` y devuelve la lista incluyendo `query_db_latency`.
4. **Razonar.** El agente pasa las herramientas recibidas al LLM; el modelo detecta que puede responder la pregunta usando la función recién descubierta, sin que se haya tocado una sola línea del código del cliente.

### Dos aclaraciones sobre este ejemplo

Primero, a diferencia de la demo de MRTR de la sección 3.3 (corrida y verificada línea por línea contra el SDK oficial para este mismo trabajo), el código de arriba es **pseudocódigo ilustrativo del patrón**, no un script verificado de punta a punta. Algunos nombres (`session.discover()`, la ruta exacta de importación de `streamable_http_client`) pueden diferir de la API concreta de una versión dada del SDK.

Segundo, el import `from mcp.server.fastmcp import FastMCP` corresponde a la convención de nombres anterior del SDK oficial. En la versión verificada para este reporte (`mcp==2.2.0`), esa clase se renombró a `MCPServer`, importable desde `mcp.server.mcpserver` (§3.3). Es otro ejemplo puntual del mismo problema de vida media corta de la documentación técnica de MCP señalado en §3.1 (Parte 2).

## 3.7 Ejemplo ilustrativo: diálogo directo agente-servidor, sin Gateway

A diferencia del ejemplo anterior, mediado por un Gateway que agrega descubrimiento de red, RBAC y sanitización (§5.1), este es el caso más simple posible: el agente ya conoce la ubicación del servidor (transporte stdio, sin red de por medio) y dialoga directamente con él, sin intermediarios. Es, en rigor, la única situación de producción donde esto sigue siendo la norma en vez de la excepción (§5.1, «Excepción: entornos locales»).

El agente levanta el servidor como subproceso y le habla por stdin/stdout. Bajo el modelo stateless de 2026-07-28 (§3.1), no hay handshake previo: cada mensaje lleva su propia versión de protocolo y capacidades en `_meta`. Una secuencia mínima (descubrimiento de versión, inspección de herramientas, ejecución) se ve así.

**1) `server/discover`**

```jsonc
// >>> Cliente envía:
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "server/discover",
  "params": {
    "_meta": {
      "io.modelcontextprotocol/protocolVersion": "2026-07-28",
      "io.modelcontextprotocol/clientCapabilities": {}
    }
  }
}

// <<< Servidor responde:
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "protocolVersion": "2026-07-28",
    "serverInfo": { "name": "metrics-server", "version": "0.1.0" },
    "capabilities": { "tools": {} }
  }
}
```

**2) `tools/list`**

```jsonc
// >>> Cliente envía:
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/list",
  "params": {
    "_meta": {
      "io.modelcontextprotocol/protocolVersion": "2026-07-28",
      "io.modelcontextprotocol/clientCapabilities": {}
    }
  }
}

// <<< Servidor responde:
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "tools": [
      {
        "name": "query_db_latency",
        "description": "Latencia promedio (ms) de un cluster de BD.",
        "inputSchema": {
          "type": "object",
          "properties": { "cluster_id": { "type": "string" } },
          "required": ["cluster_id"]
        }
      }
    ]
  }
}
```

**3) `tools/call`**

```jsonc
// >>> Cliente envía:
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "query_db_latency",
    "arguments": { "cluster_id": "db-primary" },
    "_meta": {
      "io.modelcontextprotocol/protocolVersion": "2026-07-28",
      "io.modelcontextprotocol/clientCapabilities": {}
    }
  }
}

// <<< Servidor responde:
{
  "jsonrpc": "2.0",
  "id": 3,
  "result": {
    "content": [
      { "type": "text", "text": "Cluster db-primary: 12ms avg latency" }
    ],
    "isError": false
  }
}
```

Tres idas y vueltas, sin sesión, sin negociación previa por fuera de lo que cada mensaje declara en `_meta` (§3.1 y §3.5). Si la tool necesitara confirmación humana, el paso 3 devolvería un `InputRequiredResult` en lugar del resultado final, y habría un cuarto mensaje reintentando con `inputResponses` y `requestState`: el patrón MRTR descrito en §3.3 y §3.5 (Partes 4 y 5).

### Estado de verificación de este ejemplo

Los nombres de método y las claves `_meta` están verificados contra el código fuente del SDK oficial de Python (`mcp==2.2.0`, el mismo entorno de la demo de MRTR de §3.3). Sin embargo, al intentar correr este diálogo exacto de punta a punta, el servidor stdio de esa versión del SDK arrancó por defecto en lo que el propio código interno llama la «era de handshake» y rechazó el envelope `_meta` de 2026-07-28 hasta ser configurado explícitamente para la «era moderna». Es un matiz de implementación que no se terminó de resolver.

Este ejemplo documenta entonces el flujo tal como lo especifica la especificación (consistente con §3.1 y §3.5), pero, a diferencia de la demo de §3.3, **no es un transcript corrido de punta a punta**.

---

**Anterior:** [Parte 5: semántica del protocolo y señales de riesgo](/posts/2026/reporte-mcp-2026-parte-5-semantica-del-protocolo-y-senales-de-riesgo/) · **Siguiente:** [Parte 7: MCP, A2A y la capa vertical](/posts/2026/reporte-mcp-2026-parte-7-mcp-a2a-y-la-capa-vertical/)
