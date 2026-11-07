---
layout: post
title: "MCP SoK: Beyond the Threat Catalog"
date: 2026-09-26 18:17:15 -0300
description: "Resumen de “SoK: Beyond the Threat Catalog — An Empirical Taxonomy of Authorization Governance and Containment Failures in Model Context Protocol Servers”"
image: /assets/img/los-servidores-mcp-no-fallan-por/00.png
substack_url: "https://matiaszz.substack.com/p/los-servidores-mcp-no-fallan-por"
---

**Matías Zabaljáuregui**

📄 **Paper completo (PDF):**

Short\_Paper.pdf

228KB ∙ PDF file

[Download](https://matiaszz.substack.com/api/v1/file/a1eaa5a0-c8fd-4081-9359-93562d417e8e.pdf)

---

## El problema

El Model Context Protocol (MCP) estandariza cómo un agente basado en LLM descubre e invoca herramientas externas: sistemas de archivos, bases de datos, APIs SaaS, pagos, wallets, historias clínicas. A diferencia de una API tradicional, acá quien llama no es un cliente conocido y auditado: es un modelo de lenguaje cuya decisión de invocar una herramienta puede ser influida por contenido no confiable.

Casi toda la literatura sobre seguridad de MCP cae en dos géneros: catálogos de amenazas que no se apoyan en código de producción, y escaneos automatizados masivos que miden la prevalencia de patrones de bugs conocidos. Faltaba mirar, código en mano, **cómo se decide (o no) qué puede hacer el agente**.

## Qué hice

Una auditoría manual de **89 repositorios MCP públicos** (91 pasadas de auditoría en 15 rondas, estratificadas por dominio de aplicación y no por popularidad). Cada hallazgo se clasificó y verificó a mano. Las pruebas de concepto se corrieron solo contra reconstrucciones privadas y aisladas, con datos sintéticos.

## La tesis

**La falla dominante no es un bug de programación: es una decisión de autorización que nunca se tomó.** Menos del 10% de los repositorios tiene bugs de código explotables. Lo más frecuente es un mapeo 1:1 y sin alcance acotado del plano de control de una API subyacente hacia herramientas MCP: el servidor expone todo lo que la API permite porque nadie decidió qué debería poder hacer un llamador guiado por un LLM.

## Qué aporta

1. **Una taxonomía en tres capas**, más un eje ortogonal de integridad de implementación: exposición del plano de control, ejecución y delegación de confianza, y señalización de riesgo a nivel de protocolo.
2. **Seis dimensiones de gobernanza** que las taxonomías previas no cubren. Una de ellas es la *intención de contención sin una primitiva técnica válida*: el servidor intenta aislar, pero el mecanismo elegido no aísla. El caso ilustrativo es un escape de sandbox contra un servidor de datos de salud que usaba el módulo `vm` de Node.js, que no es un límite de seguridad.
3. **Un catálogo de diez patrones de mitigación** que aparecen de forma independiente en código real. Ningún repositorio combina más de tres o cuatro.
4. **Un modelo de severidad que depende de la plataforma subyacente y no solo del código del servidor.** Por ejemplo, un borrado en QuickBooks es un soft-delete recuperable, mientras que `DeleteObject` en S3 es irreversible. El mismo tipo de falla pesa distinto según lo que hay debajo.

## Divulgación responsable

Diez repositorios afectados están en proceso de *coordinated disclosure*. **En el paper los nombres de esos repositorios están omitidos** (”name withheld pending disclosure”), y en este post tampoco los menciono. Los reportes técnicos completos se enviarán a cada mantenedor por un canal privado en cuanto lo habilite; el detalle público espera a que se cumpla el plazo de divulgación o a que haya un fix.

## Límites que declaro en el paper

- **Un solo revisor.** Toda la clasificación y verificación la hizo una persona, sin una segunda revisión adversarial independiente.
- **No estimo tasas comparativas de falla.** Los datos sostienen una taxonomía y patrones, no una medición de prevalencia comparable con estudios de gran escala.
- **Uso de un asistente de IA.** El trabajo mecánico de la auditoría (leer repositorios, correr el escáner estático, redactar notas, construir pruebas de concepto) se hizo con Claude, bajo mi dirección y revisión. Está declarado en la sección *LLM Usage Considerations*.

## Cómo se posiciona frente a otros trabajos

Contra cuatro trabajos concurrentes de 2025–2026: un SoK existente de seguridad MCP, un estudio de registros a escala (67.057 servidores), un estudio empírico de 1.899 repositorios y una taxonomía de defensas alineada por capas. El aporte diferencial es la auditoría manual y la atención a las decisiones de autorización, no a los patrones de bug.
