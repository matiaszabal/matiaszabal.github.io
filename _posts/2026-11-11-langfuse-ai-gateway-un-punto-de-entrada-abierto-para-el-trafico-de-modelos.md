---
layout: post
title: "Langfuse AI Gateway: un punto de entrada abierto para el tráfico de modelos"
date: 2026-11-11 09:00:00 -0300
description: "Langfuse lanzó en beta pública un gateway de código abierto que registra cada llamada a un modelo, quién la hizo y cuánto costó. Qué ofrece, cómo funciona y qué todavía no tiene."
thumbnail: /assets/img/langfuse-ai-gateway-un-punto-de-entrada-abierto-para-el-trafico-de-modelos/thumb.jpg
tags: [observabilidad, gobernanza, langfuse, agentes]
---

Langfuse presentó el 9 de noviembre de 2026 su **AI Gateway**, en beta pública: un punto de entrada central y de código abierto para todo el tráfico hacia modelos de una organización. Registra cada llamada, quién la hizo y cuánto costó, y la guarda como un *trace* nativo de Langfuse. El anuncio original está acá: [Langfuse launches AI Gateway](https://langfuse.com/blog/introducing-gateway).

Lo cuento porque toca un problema práctico de gobernanza: mucho uso de IA ocurre en herramientas que nadie instrumenta (agentes de código en notebooks de ingeniería, asistentes internos, scripts). Un gateway ve todo lo que pasa por él, aunque la herramienta de origen no tenga observabilidad propia.

## Qué ofrece

- **Visibilidad de gasto.** Costo y uso por modelo y proveedor en un solo panel, con alertas.
- **Atribución.** Cada API key pertenece a una persona o servicio y puede llevar un equipo o centro de costos.
- **Traces completos.** Cada llamada se puede buscar, evaluar y anotar.
- **Control de modelos.** Los administradores aprueban modelos de forma central para bloquear los no verificados o caros.
- **Modos de registro.** Solo uso y costo, prompts y respuestas completos, o nada (`NONE`, solo en self-hosted). Por defecto se guardan metadatos, uso y costo, no contenido.
- **Trazado incremental.** Se puede sumar detalle (por ejemplo, la ejecución de tools) con OpenTelemetry o las integraciones existentes.
- **Memoria para agentes.** Los datos están disponibles por MCP y CLI, para que un agente consulte sus pedidos anteriores.
- **Exportación** de métricas y logs crudos a un data lake.

## Cómo funciona

El cambio para el equipo es mínimo: se cambia la *base URL* y se usa una gateway key en lugar de la clave del proveedor. Requests y respuestas conservan el formato nativo del proveedor. Según el anuncio, así se ve con el cliente de OpenAI en Python:

```python
import os

from openai import OpenAI

# Antes: client = OpenAI()
client = OpenAI(
    base_url="https://gateway.cloud.langfuse.com/openai/",
    api_key=os.environ["LANGFUSE_GATEWAY_KEY"],
)
```

Está escrito en Rust y se despliega como una única imagen Docker de 22 MB junto a una instancia de Langfuse existente, sin dependencias extra. Los datos de rendimiento son del propio anuncio: latencia mediana por debajo de 3 ms con el trazado activo y más de 1.000 streams concurrentes en un nodo de 2 vCPU. No los verifiqué de forma independiente.

## Licencia y modelo comercial

- El núcleo está bajo licencia **MIT**.
- Self-hosted es gratis, incluso en entornos aislados (*air-gapped*).
- En Langfuse Cloud solo se cobran las requests registradas; las no registradas son gratis.
- Cada organización mantiene sus contratos y condiciones con los proveedores (por ejemplo, zero data retention). Langfuse dice que no agrega margen ni revende tokens.

## Qué todavía no tiene

Es una beta con límites claros:

- Soporta **OpenAI y Anthropic**. Están anunciados OpenRouter, AWS, GCP, Azure y APIs de inferencia propias.
- En la hoja de ruta: límites de gasto por equipo, usuario o key; *fallbacks* entre proveedores; guardrails y redacción de PII; aprovisionamiento SCIM; y enrutamiento automático de modelos.

Para quien necesite hoy límites de gasto o guardrails en el gateway, eso todavía no está.

## Mi lectura

- **No es lo mismo que un MCP Gateway.** Este gateway intermedia el tráfico hacia los *modelos*. El MCP Gateway que describí en la serie [Reporte MCP 2026](/posts/2026/reporte-mcp-2026-parte-8-gateways-sandboxing-y-prompt-injection/) intermedia el acceso de los agentes a *herramientas y datos*. Resuelven problemas distintos y pueden convivir en una misma arquitectura.
- **El valor está en la atribución.** Saber quién gastó qué y con qué prompt es la base de cualquier control posterior. Sin eso, la gobernanza queda en una política que nadie puede verificar.
- **Registrar contenido es una decisión de datos sensibles.** El modo por defecto (sin contenido) es razonable; activar el registro completo implica decidir dónde viven esos prompts y quién accede a ellos.

Las cifras de adopción y rendimiento que cita el anuncio son del proveedor. Conviene probarlo con tu propio tráfico antes de sacar conclusiones.
