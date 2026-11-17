---
layout: post
title: "Plataformas de seguridad para IA: 37 herramientas para modelos, aplicaciones y agentes"
date: 2026-11-17 20:45:00 -0300
description: "Un mapa de 37 productos de seguridad para IA, agrupados en cinco capas (postura, guardrails en runtime, agentes y MCP, red teaming y uso por el personal), con el link de cada uno."
thumbnail: /assets/img/plataformas-de-seguridad-para-ia-37-herramientas-para-modelos-aplicaciones-y-agentes/thumb.jpg
tags: [seguridad, guardrails, agentes, mcp, red-teaming]
---

Elegir una herramienta de seguridad para IA se complica por una razón simple: bajo la misma etiqueta conviven productos que hacen cosas muy distintas. Unos escanean archivos de modelos antes del despliegue, otros filtran prompts en tiempo real, otros controlan qué herramientas puede llamar un agente y otros vigilan lo que los empleados pegan en un chat público.

La lista curada [«AI security platforms for models, apps and agents»](https://dailyaibrief.com/lists/ai-security-guardrails), de Daily AI Brief (actualizada en noviembre de 2026), reúne **37 productos** y los ordena en cinco secciones. Este artículo recorre esas secciones, nombra todas las herramientas con el link a su sitio y agrega una lectura de lo que muestra el conjunto. Los datos de cada producto (funciones, precios, adquisiciones, fechas) son los que consigna la fuente a esa fecha: conviene confirmarlos en el sitio del proveedor antes de decidir una compra.

## Cómo leer el mapa

Cada sección responde a una pregunta distinta de un programa de seguridad de IA:

| Sección | Pregunta que responde | Productos |
|---|---|---|
| Postura y cadena de suministro de modelos | ¿Qué IA tengo, qué contiene y está sana? | 6 |
| Guardrails en runtime y firewalls de IA | ¿Qué entra y qué sale del modelo en cada llamada? | 14 |
| Seguridad de agentes y MCP | ¿Qué puede hacer un agente y con qué identidad? | 6 |
| Red teaming de IA | ¿Cómo lo ataco antes de que lo ataquen? | 6 |
| Uso de IA por el personal | ¿Qué datos salen hacia herramientas de IA de terceros? | 5 |

Son capas complementarias, no alternativas. Un mismo proveedor aparece a veces en dos (por ejemplo, descubrimiento más protección en runtime), y esa superposición es parte de lo que hay que entender al comparar.

## 1. Postura y cadena de suministro de modelos

Esta capa responde al inventario y a la integridad: descubrir los despliegues de IA (incluidos los no autorizados), evaluar configuraciones y revisar que los archivos de modelo no traigan código malicioso. Es el equivalente de la gestión de postura en la nube, aplicado a modelos y agentes.

- **[HiddenLayer](https://www.hiddenlayer.com/).** Escanea archivos de modelos en busca de malware, vulnerabilidades e integridad. Suma descubrimiento de IA, simulación de ataques y monitoreo en runtime, y ofrece una GitHub Action para CI/CD con escáneres SaaS o locales. Según la fuente, cerró una serie B de 100 M USD el 2 de septiembre de 2026.
- **[IBM Guardium AI Security](https://www.ibm.com/support/pages/ibm-guardium-ai-securitysaas).** Descubre despliegues de IA y evalúa vulnerabilidades y malas configuraciones. Su firewall de IA revisa prompts y salidas (inyección de código, datos personales, fugas) y se integra con watsonx.governance. La versión SaaS figura como disponible desde el 30 de mayo de 2025.
- **[Microsoft Defender for Cloud](https://azure.microsoft.com/en-us/products/defender-for-cloud/).** Descubre cargas de IA en Azure, Amazon Bedrock y Google Vertex AI, y señala riesgos de configuración y rutas de ataque mediante Defender CSPM. Analiza prompts y respuestas y escanea modelos. Las funciones de agentes requieren Microsoft Agent 365 desde el 1 de julio de 2026. El precio se mide por cada 1.000 tokens y la prueba dura 30 días o 75.000 millones de tokens escaneados.
- **[Noma Security](https://noma.security/).** Combina descubrimiento de activos de IA, red teaming, control de acceso de agentes y detección y respuesta en runtime. Permite aprobar, revisar o bloquear agentes, servidores MCP y *skills*, y aplica las políticas mediante puntos de control que la empresa ya tiene.
- **[Palo Alto Networks Prisma AIRS](https://docs.paloaltonetworks.com/ai-runtime-security).** Inventario de IA, escaneo de cadena de suministro, red teaming, protección en runtime y gestión de postura, con documentación de una pasarela de IA y de controles de identidad de agentes. La fuente aclara que AI Supply Chain Security reemplaza el nombre AI Model Security y que Managed AI Runtime Security sigue en vista previa o acceso temprano.
- **[Tenable One AI Exposure](https://www.tenable.com/products/ai-exposure).** Monitorea el uso de ChatGPT Enterprise y Microsoft Copilot por parte de empleados y agentes, revisa configuraciones, integraciones y datos compartidos, y aplica políticas contra inyección de prompts, jailbreaks y exposición de datos sensibles. Funciona sin agentes instalados. Tenable completó en 2025 la adquisición de Apex Security.

## 2. Guardrails en runtime y firewalls de IA

La sección más poblada. Aquí cada solicitud al modelo y cada respuesta pasan por una verificación: inyección de prompts, *jailbreaks*, datos personales, contenido dañino, URLs maliciosas. Hay tres tipos de proveedor: nubes que integran el control en su plataforma de modelos, empresas de redes y seguridad que lo suman a su firewall o WAF, y especialistas.

- **[Amazon Bedrock Guardrails](https://aws.amazon.com/bedrock/guardrails/).** Filtra prompts y respuestas por contenido dañino, temas vetados e información sensible, y puede bloquear o enmascarar datos. La API ApplyGuardrail también sirve con modelos autoalojados o de terceros y admite aplicación centralizada en varias cuentas de AWS.
- **[Arcjet](https://arcjet.com/).** SDKs e integraciones para agentes con controles contra inyección de prompts, datos sensibles y acceso a herramientas, servidores MCP y APIs. Descubre agentes y decide permitir, retener o bloquear con un motor de políticas OPA/Rego.
- **[Cisco AI Defense](https://www.cisco.com/site/us/en/products/security/ai-defense/index.html).** Descubrimiento de activos, escaneo de cadena de suministro, validación adversarial y guardrails en runtime. Incluye escaneo de servidores MCP y protección de sus solicitudes y respuestas. La edición Explorer permite hacer red teaming antes de un despliegue empresarial. Según la fuente, Robust Intelligence forma parte del producto.
- **[Cloudflare AI Security for Apps](https://developers.cloudflare.com/waf/detections/ai-security-for-apps/).** Antes llamado Firewall for AI. Agrega al WAF detecciones de inyección de prompts, datos personales y temas, y escanea solicitudes JSON a endpoints marcados como `cf-llm`. Disponible desde el 11 de marzo de 2026: el descubrimiento de endpoints está en todos los planes, pero los campos de detección de IA y el conjunto de reglas en modo log requieren un complemento Enterprise pago.
- **[Enkrypt AI](https://www.enkryptai.com/).** Pruebas adversariales continuas, guardrails en runtime y controles de política; convierte políticas internas en guardrails. Anaconda adquirió la empresa el 4 de agosto de 2026.
- **[F5 AI Guardrails](https://www.f5.com/products/ai-guardrails).** Revisa en runtime las interacciones de modelos y agentes contra ataques a prompts, fuga de datos y salidas no deseadas, con guardrails personalizados, restricción de acciones de agentes, registros de aplicación y exportación a SIEM. Se lanzó tras completar la adquisición de CalypsoAI.
- **[Fiddler Guardrails](https://www.fiddler.ai/guardrails).** Evalúa prompts y respuestas según políticas de seguridad, protección y privacidad, con umbrales configurables. Detecta jailbreaks, inyección, exposición de datos personales y contenido inseguro. Se ejecuta en la nube o VPC del cliente con los modelos Fiddler Centor (antes Fiddler Trust Models).
- **[Google Cloud Model Armor](https://docs.cloud.google.com/model-armor/overview).** Revisa prompts y respuestas por inyección, datos sensibles y URLs maliciosas mediante plantillas, y puede usarse con aplicaciones fuera de Google Cloud. El escaneo de imágenes está en vista previa (JPEG, PNG, BMP de hasta 4 MB, en multirregiones de EE. UU. y la UE). La fuente subraya que procesa cada solicitud de forma independiente, sin contexto entre turnos.
- **[Guardrails AI](https://guardrailsai.com/).** Código abierto. Verificaciones en runtime contra violaciones de políticas, alucinaciones y fuga de datos; Guardrails Hub lista validadores para desarrolladores. Harvey adquirió la empresa el 8 de septiembre de 2026.
- **[Lakera](https://www.lakera.ai/).** Revisa prompts y respuestas por inyección, jailbreaks y exposición de datos. Su producto AI Agent Security descubre agentes y herramientas conectadas por MCP y aplica políticas. Ofrece despliegue cloud por API y red teaming. Check Point adquirió Lakera en 2025. Hay un plan gratuito Community (10.000 solicitudes al mes, límite de 8.000 tokens por prompt) y uno Enterprise con precio a medida, SaaS o autoalojado.
- **[Microsoft Azure AI Content Safety](https://learn.microsoft.com/en-us/azure/ai-services/content-safety/overview).** APIs para contenido dañino, ataques a prompts y material protegido. La API Task adherence detecta uso de herramientas por agentes que no coincide con la interacción del usuario. La detección de *groundedness* está en vista previa y se retirará el 30 de abril de 2027.
- **[NVIDIA NeMo Guardrails](https://docs.nvidia.com/nemo/guardrails/more-deployment-options/using-microservice).** Biblioteca Python de código abierto para verificaciones programables de entrada, recuperación, herramientas y salida, configurable con YAML, Colang y acciones personalizadas. [Documentación de la biblioteca](https://docs.nvidia.com/nemo/guardrails/about-nemo-guardrails-library/overview). Ojo con un detalle que señala la fuente: el catálogo de microservicios marca el artefacto como no soportado y dice que NeMo microservices se discontinuó el 1 de octubre de 2026, mientras que la guía de despliegue y el catálogo todavía lo presentan como opción de NVIDIA AI Enterprise. Hay contradicciones entre esas páginas.
- **[Radware LLM Firewall](https://www.radware.com/products/llm-firewall/).** Inspecciona prompts antes de que lleguen a los servidores de origen y aplica controles contra inyección, abuso de recursos y datos personales, además de políticas para contenido de IA no deseado. Forma parte de la oferta de seguridad cloud de Radware y requiere contactar a ventas.
- **[TrojAI](https://troj.ai/).** Red teaming más verificaciones en runtime: revisa prompts y respuestas, descubre agentes y servidores MCP y monitorea llamadas a herramientas, con despliegue local o en la nube del cliente. A10 Networks adquirió TrojAI el 15 de junio de 2026; antes, la empresa había anunciado 5,75 M USD adicionales de seed el 3 de abril de 2024, liderados por Flying Fish.

## 3. Seguridad de agentes y MCP

Los agentes agregan una superficie que un filtro de prompts no cubre: qué herramientas llaman, con qué identidad y qué datos mueven. Esta sección reúne productos que tratan al agente y a sus conexiones MCP como el objeto a proteger.

- **[CrowdStrike Falcon AIDR](https://www.crowdstrike.com/en-us/resources/crowdcasts/securing-ai-era-crowdstrike-falcon-ai-detection-and-response/).** Visibilidad de prompts, detección de amenazas, protección de datos, controles de acceso y respuesta automatizada. Cubre endpoints, aplicaciones, agentes, servidores MCP y pasarelas de IA con un solo sensor y una consola. Disponible en general dentro de la plataforma Falcon.
- **[Dynamo AI](https://www.dynamo.ai/).** DynamoEval prueba aplicaciones antes del lanzamiento y DynamoGuard revisa prompts y respuestas en runtime (inyección, jailbreaks, fuga de datos, políticas de la empresa). Puede correr en la VPC del cliente o en servidores locales, y una extensión de navegador revisa el uso de ChatGPT y Copilot por el personal. La empresa es DynamoFL, Inc.; anunció una serie A de 15,1 M USD el 16 de agosto de 2023, codirigida por Canapi Ventures y Nexus Venture Partners.
- **[Lasso Security](https://www.lasso.security/).** Descubre agentes y aplicaciones, mapea sus modelos y herramientas, evalúa su postura y aplica políticas en línea mediante proxy, API o pasarela de IA.
- **[NeuralTrust](https://neuraltrust.ai/).** Combina TrustGuard (seguridad de runtime de agentes) con TrustGate (pasarela para modelos, servidores MCP y APIs). Inspecciona prompts, respuestas y llamadas a herramientas y aplica reglas de acceso según la identidad. Planes Free, Standard (49 USD al mes, acreditables al uso, con los cargos de tokens del proveedor aparte) y Enterprise, que incluye despliegue privado.
- **[Operant AI](https://www.operant.ai/).** Protección en runtime para aplicaciones, agentes y conexiones MCP, con una familia que incluye AI Gatekeeper, MCP Gateway, Agent Protector y Endpoint Protector. Su Semantic Firewall permite, bloquea o redacta en línea según la intención del agente, y detecta *shadow AI*.
- **[Zenity](https://zenity.io/).** Inventaría agentes, revisa permisos y configuraciones y aplica políticas en runtime en entornos SaaS, cloud, personalizados y endpoints. Su capa de seguridad MCP registra solicitudes, llamadas y respuestas junto con la identidad asociada. Según la fuente, cerró una serie C de 125 M USD el 3 de agosto de 2026, liderada por Norwest.

## 4. Red teaming de IA

Probar el sistema como lo haría un atacante, de manera sistemática y repetible. Esta sección mezcla plataformas, servicios gestionados y herramientas abiertas.

- **[Adversa AI](https://adversa.ai/ai-red-teaming-agentic-ai/).** Red teaming autónomo para modelos, aplicaciones, agentes y MCP. Los riesgos de negocio se pueden describir en texto o CSV y la entrega incluye hallazgos priorizados, evidencia reproducible y guías de remediación. Se ofrece como servicio, con demo en vivo.
- **[Alice](https://alice.io/).** Antes se llamaba ActiveFence. Prueba modelos y agentes con prompts maliciosos y monitorea entradas y salidas según políticas. Su WonderSuite combina red teaming y guardrails por REST API. Según la fuente, recaudó 140 M USD el 25 de agosto de 2026 (liderados por Apax Digital Funds, con un total de 280 M USD); el acceso requiere una cuenta abierta por un representante.
- **[Giskard](https://www.giskard.ai/).** Red teaming continuo, evaluación de LLM y guardrails para agentes. Hay también una evaluación gestionada con un informe de «desplegar o corregir» y reevaluaciones hasta confirmar las correcciones. La fuente recomienda definir si se compra plataforma, servicio o ambos.
- **[Mindgard](https://mindgard.ai/).** Mapea sistemas, agentes, herramientas y comportamiento, y los prueba con técnicas de atacante. Gestiona vulnerabilidades y remediación, con APIs, integración con CI/CD y con Burp Suite.
- **[Promptfoo](https://www.promptfoo.dev/).** CLI y biblioteca para probar prompts, agentes y aplicaciones RAG, con ejecución en CI/CD. [Repositorio en GitHub](https://github.com/promptfoo/promptfoo), licencia MIT. Ahora se identifica como parte de OpenAI, tras un acuerdo anunciado el 9 de marzo de 2026. El plan Community es gratuito e incluye 10.000 sondas de red teaming por mes; Enterprise y el paquete on-premises tienen precio a medida. Serie A de 18,4 M USD el 29 de julio de 2025, liderada por Insight Partners.
- **[Virtue AI](https://www.virtueai.com/).** El link de la fuente hoy redirige a [FortiAIGate](https://www.fortinet.com/products/fortiaigate), de Fortinet, que adquirió Virtue AI en 2026. FortiAIGate revisa prompts, salidas y llamadas a herramientas de agentes (inyección, jailbreaks, fuga de datos), con políticas de uso y presupuesto y opción de autoalojamiento.

## 5. Uso de IA por el personal

La última capa mira hacia adentro: qué datos de la organización terminan en herramientas de IA que la organización no controla, y cómo se aplica una política sin frenar el trabajo.

- **[Cato AI Security](https://knowledge.catonetworks.com/docs/getting-started-with-ai-security).** Monitorea interacciones con IA y aplica políticas de seguridad y protección de datos. AI for Applications cubre llamadas API y flujos entre aplicaciones y modelos; AI for End Users regula el uso de servicios de IA por empleados. Cato adquirió Aim Security en septiembre de 2025, y las dos licencias son por usuario y separadas.
- **[Harmonic Security](https://www.harmonic.security/).** Revisa el uso de herramientas de IA por el personal y aplica políticas a datos sensibles, con extensión de navegador, agente de endpoint y una pasarela MCP local. Serie B de 50 M USD el 14 de octubre de 2026, liderada por Crosspoint Capital Partners (76 M USD en total, según la fuente).
- **[Nightfall](https://www.nightfall.ai/).** Controla el movimiento de datos sensibles entre agentes de IA, servidores MCP, endpoints y SaaS. Su MCP Gateway aprueba servidores y aplica políticas a las llamadas de herramientas, y descubre y clasifica datos expuestos.
- **[Prompt Security](https://prompt.security/).** Detecta y puede bloquear datos sensibles enviados a aplicaciones web de IA mediante extensión de navegador. Su producto de seguridad de agentes descubre agentes y servidores MCP y mantiene registros de auditoría. Es parte de SentinelOne, que completó la adquisición el 5 de septiembre de 2025; antes había recaudado una serie A de 18 M USD el 20 de noviembre de 2024, liderada por Jump Capital.
- **[Zscaler AI Guard](https://www.zscaler.com/products-and-solutions/ai-guardrails).** AI Guard for Apps inspecciona prompts y respuestas en línea (inyección, jailbreaks, URLs maliciosas, contenido inseguro), con DLP a nivel de prompt y registros de decisiones. AI Guard for Users controla el acceso por usuario, aplicación y riesgo.

## Qué muestra el conjunto

**1. Un mercado que se consolida rápido.** Varias fichas incluyen una adquisición reciente. Según la fuente:

| Producto | Operación |
|---|---|
| Lakera | Adquirida por Check Point (2025) |
| Prompt Security | Adquirida por SentinelOne (5 de septiembre de 2025) |
| Aim Security | Adquirida por Cato (septiembre de 2025) |
| Apex Security | Adquirida por Tenable (2025) |
| Promptfoo | Parte de OpenAI (acuerdo anunciado el 9 de marzo de 2026) |
| TrojAI | Adquirida por A10 Networks (15 de junio de 2026) |
| Enkrypt AI | Adquirida por Anaconda (4 de agosto de 2026) |
| Guardrails AI | Adquirida por Harvey (8 de septiembre de 2026) |
| Virtue AI | Adquirida por Fortinet (2026); hoy FortiAIGate |
| CalypsoAI | Adquirida por F5 (origen de F5 AI Guardrails) |
| Robust Intelligence | Integrada en Cisco AI Defense |

Para quien compra, esto tiene una consecuencia práctica: la continuidad de la hoja de ruta, el precio y el modelo de despliegue de un proveedor pequeño pueden cambiar después de la firma. Vale la pena preguntarlo antes, y pedir cláusulas de salida.

**2. MCP ya es un requisito de producto.** Según mi lectura de las fichas, 13 de los 37 productos mencionan explícitamente servidores MCP: Noma Security, Arcjet, Cisco AI Defense, Lakera, TrojAI, CrowdStrike Falcon AIDR, NeuralTrust, Operant AI, Zenity, Adversa AI, Harmonic Security, Nightfall y Prompt Security. Las funciones se repiten: descubrir qué servidores MCP existen, aprobarlos o bloquearlos, y registrar solicitudes y respuestas con la identidad asociada. Es el mismo problema que describí en [la brecha de control en IA agéntica](/posts/2026/la-brecha-de-control-por-que-la-ia-agentica-necesita-un-programa-de-seguridad-y-gobernanza/): los agentes ya operan, y la gobernanza llega después.

**3. Un guardrail de runtime es una pieza, no un programa.** Casi todos los productos de la sección 2 inspeccionan una solicitud o una respuesta. La fuente lo marca en un caso concreto: Model Armor procesa cada solicitud de forma independiente, sin contexto entre turnos. Una política que depende de lo ocurrido varias interacciones atrás, o de la identidad que delegó la tarea, necesita otra capa (identidad del agente, autorización, trazas). Es el planteo de [seguridad y gobernanza en arquitectura de IA agéntica](/posts/2026/seguridad-y-gobernanza-en-arquitectura-de-ia-agentica/).

**4. Las opciones abiertas existen, pero se mueven.** Entre las abiertas están NVIDIA NeMo Guardrails (biblioteca), Guardrails AI (código abierto) y Promptfoo (MIT, con repositorio público). La lista también muestra el costo de depender de ellas: Guardrails AI y Promptfoo cambiaron de dueño y NeMo Guardrails tiene mensajes contradictorios sobre su despliegue como microservicio.

**5. La disponibilidad tiene letra chica.** Aparecen vistas previas (Prisma AIRS Managed AI Runtime Security, el escaneo de imágenes de Model Armor), funciones que requieren complementos pagos (Cloudflare) y una detección con fecha de retiro (la de *groundedness* de Azure AI Content Safety, el 30 de abril de 2027). Es información que no suele estar en la primera página del producto.

## Criterios para elegir

Esta parte es mi propuesta y no viene de la lista:

- **Empezar por el inventario.** Lo que no se ve no se protege: la capa 1 (y el descubrimiento de agentes y MCP de la capa 3) condiciona las demás.
- **Separar el punto de control del motor de decisión.** Muchos productos aplican la política donde ya existe un control (WAF, proxy, pasarela, endpoint). Conviene definir dónde se aplica cada decisión y quién la audita.
- **Probar con los propios casos.** Una evaluación de red teaming (capa 4) sirve para comparar guardrails de la capa 2 con el mismo conjunto de ataques, antes de elegir.
- **Exigir evidencia de lo que bloquea y de lo que deja pasar.** Cada filtro tiene falsos positivos y falsos negativos. Pedir métricas y logs exportables (algunos productos citan exportación a SIEM o registros de decisiones).
- **Cubrir al personal por separado.** La capa 5 resuelve un riesgo distinto del de las aplicaciones propias.

## Fuente

Este artículo resume y reorganiza la lista de Daily AI Brief [«AI security platforms for models, apps and agents»](https://dailyaibrief.com/lists/ai-security-guardrails) (actualizada en noviembre de 2026). Las descripciones, los datos comerciales y las fechas provienen de esa fuente; los links de cada herramienta son los que ella enlaza. Las observaciones de las secciones «Qué muestra el conjunto» y «Criterios para elegir» son mías.
