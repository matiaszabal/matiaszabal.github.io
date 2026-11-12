---
layout: post
title: "Agent Name Service llega a la Linux Foundation: identidad verificable para agentes sobre DNS"
date: 2026-11-12 09:00:00 -0300
description: "La Linux Foundation anunció Agent Name Service (ANS), un estándar abierto sobre DNS para nombrar, verificar y descubrir agentes de IA. Qué es, quién lo respalda y qué deja abierto."
thumbnail: /assets/img/agent-name-service-identidad-verificable-para-agentes-bajo-la-linux-foundation/thumb.jpg
tags: [agentes, identidad, a2a, mcp, linux-foundation]
---

Los protocolos agénticos más importantes están convergiendo bajo un mismo techo institucional. **MCP** pasó a la Agentic AI Foundation (AAIF) de la Linux Foundation en diciembre de 2025, y **A2A** se incorporó a la misma fundación en agosto de 2026. Ahora la Linux Foundation suma una pieza que ninguno de los dos resuelve: **Agent Name Service (ANS)**, un estándar abierto para dar identidad verificable y descubrimiento a los agentes de IA.

Esa convergencia es de gobernanza, no una especificación técnica común. Lo analicé en el [Reporte MCP 2026](/posts/2026/reporte-mcp-2026-parte-7-mcp-a2a-y-la-capa-vertical/): MCP cubre la capa vertical (agente-herramientas) y A2A la horizontal (agente-agente). Ambos dejan abiertos la identidad y el descubrimiento a escala de Internet (Parte 12 de la serie, [problemas abiertos](/posts/2026/reporte-mcp-2026-parte-12-problemas-abiertos-conclusion-y-referencias/)). ANS apunta a ese hueco.

El anuncio, publicado el 10 de noviembre de 2026 durante KubeCon + CloudNativeCon North America, está acá: [Linux Foundation Welcomes Agent Name Service to Bring Verifiable Identity and Discovery to AI Agents](https://www.linuxfoundation.org/press/linux-foundation-welcomes-agent-name-service-to-bring-verifiable-identity-and-discovery-to-ai-agents).

## Qué es ANS

Según el comunicado, ANS es «un estándar abierto construido sobre la infraestructura del Domain Name System (DNS)» que se apoya también en los certificados que los sitios web ya usan. Define:

- cómo se **nombran y registran** los agentes;
- cómo se **publican** sus identidades a través de DNS;
- cómo se **verifica** una identidad y cómo se verifican los agentes entre sí;
- cómo se **monitorean** los registros de identidad para detectar cambios no autorizados.

La especificación completa tiene siete documentos que cubren el nombrado anclado a dominios, el registro y el versionado, la publicación en DNS, la auditoría con registros públicos, el monitoreo de integridad y la autenticación agente a agente. Se desarrolla de forma abierta y la gobierna el comité directivo técnico del proyecto bajo la Linux Foundation. Ken Huang (DistributedApps.ai) dice haber liderado el desarrollo inicial y planea sumarse a ese comité. El comunicado no aclara qué organización lo creó originalmente.

## Quién lo respalda

Once organizaciones contribuyeron o adoptaron ANS desde el anuncio de intención de junio: Cisco, Cloudflare, DigiCert, DistributedApps.ai, GoDaddy, HOL, Infoblox, Radix, Salesforce, OWASP y Trustmodel.ai.

Sobre adopción temprana, el comunicado menciona dos casos:

- el Agent Directory Service de AGNTCY, otro proyecto de la Linux Foundation, soporta la verificación de identidades ANS;
- ANS Finder implementa la especificación Agentic Resource Discovery (ARD) y pasa sus pruebas de conformidad de registros.

Las frases más representativas del lado de los participantes: Jim Zemlin (Linux Foundation) dice que los agentes autónomos «no pueden tener éxito sin una identidad verificable»; DigiCert lo llama «un pasaporte para agentes de IA»; Infoblox lo describe como una capa de nombrado y descubrimiento «para agentes y servidores MCP»; y Cisco lo separa del descubrimiento: ANS da identidad confiable y el AGNTCY Directory permite descubrir agentes.

## Por qué me parece relevante

- **Reutiliza infraestructura existente.** Anclar la identidad en DNS y en certificados evita inventar una capa nueva de confianza. Es una apuesta conservadora, pero operable.
- **Separa identidad de plataforma.** El objetivo declarado es una identidad abierta e interoperable, independiente de cualquier plataforma propietaria.
- **Ataca un problema que quedó abierto.** Las Agent Cards de A2A son autodeclaradas y no hay un equivalente a un DNS para agentes. ANS propone justamente un mecanismo verificable de nombrado y publicación.

## Qué no resuelve (todavía)

El comunicado no detalla la arquitectura de PKI, los formatos de certificado ni los protocolos más allá de la publicación en DNS y la autenticación agente a agente, así que conviene leer la especificación antes de sacar conclusiones técnicas. Y, en general, una identidad verificada prueba **qué dice ser** un agente, no **qué va a hacer**: no reemplaza a la autorización granular ni a los controles de ejecución de los que hablamos en la serie. Esa última frase es mi lectura, no del comunicado.

El sitio del proyecto es [ansinfo.ai](https://ansinfo.ai) y la especificación y el código están en [github.com/agentnameservice](https://github.com/agentnameservice).
