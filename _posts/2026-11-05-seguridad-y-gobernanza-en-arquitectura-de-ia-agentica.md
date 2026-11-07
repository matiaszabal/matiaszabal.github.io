---
layout: post
title: "Seguridad y gobernanza en arquitectura de IA agéntica"
date: 2026-11-05 10:00:00 -0300
description: "Un arquitecto de IA agéntica no puede tratar la seguridad y la gobernanza como una capa perimetral o un filtro posterior."
thumbnail: /assets/img/seguridad-y-gobernanza-en-arquitectura-de-ia-agentica/thumb.jpg
linkedin_text: "Cinco áreas definen qué puede hacer un agente de IA dentro de una empresa, y ninguna es la de arquitectura: seguridad de la información, legales y compliance, riesgos, auditoría y plataforma.\n\nCada una pone el qué. El arquitecto diseña el cómo.\n\nUn ejemplo del informe que escribí: el CISO dice «nadie fuera de Finanzas puede aprobar transferencias». La arquitectura lo hace cumplir con una herramienta de pago que exige un token OAuth firmado por el sistema de identidad corporativo, verificado en el paso de ejecución. Sin ese diseño, la política es una frase en un documento.\n\nTres ideas más del informe:\n- La seguridad y la gobernanza se diseñan desde el principio, no se agregan como filtro al final.\n- Lo que no se registra no se puede auditar: trazas de decisiones y logs inmutables.\n- Cada riesgo necesita un control con nombre, un responsable y una evidencia de que funciona.\n\n¿En tu organización quién escribe el «cómo» de una política de seguridad para agentes?\n\n#IAagéntica #Gobernanza"
---

Un arquitecto de IA agéntica no puede tratar la seguridad y la gobernanza como una capa perimetral o un filtro posterior. Debe dominarlas como un componente estructural de primer orden, porque los sistemas agénticos tienen autonomía operativa, ejecutan herramientas en entornos productivos y toman decisiones de varios pasos sin supervisión humana continua.

## Índice

- **I. Conocimiento requerido sobre seguridad y gobernanza**
  - 1\. Superficie de ataque y robustez adversarial en bucles autónomos
  - 2\. Gestión de identidad, delegación y protocolos (p. ej., Model Context Protocol)
  - 3\. Observabilidad, trazabilidad forense y AgentOps
  - 4\. Alineación y riesgos en sistemas multiagente
- **II. Políticas como código, guardrails, gateways y registries de agentes**
  - 1\. Políticas como código y autorización dinámica
  - 2\. Guardrails de ejecución y validación estructurada
  - 3\. Gateways de agentes y proxies de inferencia
  - 4\. Registries de agentes y catálogos de habilidades
- **III. Otros temas de gobernanza**
  - 1\. Linaje de datos y trazabilidad de la memoria a largo plazo
  - 2\. Cumplimiento normativo y auditoría de cajas negras
  - 3\. Soberanía, privacidad de datos e inferencia híbrida
- **IV. Colaboración con otros roles y límites de responsabilidad**
  - 1\. CISO y equipos de seguridad de la información (SecOps)
  - 2\. Compliance, Legal y DPO (oficial de protección de datos)
  - 3\. Gestión de riesgos empresariales y de modelos (ERM y MRM)
  - 4\. Auditoría interna y forense
  - 5\. Infraestructura, Platform y SRE
- **V. Marcos de referencia y threat modeling**
  - 1\. Marcos de referencia
  - 2\. La matriz de amenazas y riesgos
- **VI. Momento de aplicación**
  - A. Fase de diseño (arquitectura y modelado preventivo)
  - B. Fase de implementación y CI/CD (pruebas automatizadas y políticas como código)
  - C. Fase de despliegue y operación (monitoreo, red teaming y auditoría continua)

## I. Conocimiento requerido sobre seguridad y gobernanza

El conocimiento requerido abarca cuatro dominios críticos:

### 1. Superficie de ataque y robustez adversarial en bucles autónomos

- **Inyección de prompts directa e indirecta:** comprender cómo las entradas no confiables (correos, páginas web procesadas, APIs de terceros) pueden secuestrar el flujo de control del agente, porque el modelo confunde datos con instrucciones del sistema. En el OWASP Top 10 for Agentic Applications el riesgo equivalente se llama *Agent Goal Hijack* (ASI01).
- **Tool poisoning y manipulación de esquemas:** diseñar defensas contra la alteración o la suplantación de las descripciones y los esquemas de las herramientas expuestas al agente. El objetivo es que el agente no ejecute acciones destructivas ni exfiltre datos a través de los parámetros de las llamadas. El riesgo vecino es el uso indebido de herramientas legítimas (*Tool Misuse*, ASI02).
- **Agotamiento de recursos y bucles infinitos (denial of wallet o de servicio):** límites de profundidad (max-steps), presupuestos de tokens por sesión y disyuntores (*circuit breakers*) para que un agente no entre en bucles recursivos ni sea manipulado para consumir cuotas masivas de cómputo y APIs. En OWASP LLM 2025 corresponde a *Unbounded Consumption* (LLM10).

### 2. Gestión de identidad, delegación y protocolos (p. ej., Model Context Protocol)

- **Menor privilegio por agente:** los tokens de acceso del usuario no se heredan a ciegas. Las herramientas se ejecutan bajo identidades acotadas, con permisos específicos por tarea.
- **Delegación explícita:** en lugar de reenviar el token del usuario, el agente obtiene un token propio, de alcance y duración limitados, que deja constancia de quién actúa en nombre de quién. OAuth 2.0 Token Exchange (RFC 8693) define ese mecanismo de delegación.
- **Identidad de carga de trabajo:** cada agente y cada servidor de herramientas necesita una identidad verificable y de vida corta, no una clave estática compartida. SPIFFE es el estándar de referencia para identidades de carga de trabajo.
- **Gobernanza de protocolos de contexto:** dominar la autoría y la auditoría de servidores de protocolos estandarizados (como MCP), con aislamiento de memoria, saneamiento de los recursos expuestos y control de los flujos de lectura y escritura sobre sistemas de archivos o bases vectoriales.

### 3. Observabilidad, trazabilidad forense y AgentOps

- **Trazabilidad de decisiones (linaje y procedencia):** poder reconstruir el árbol de decisión completo de un agente a lo largo de ejecuciones asíncronas y distribuidas, con frameworks de telemetría como OpenInference, Langfuse o MLflow.
- **Reproducibilidad por registro:** las APIs de modelos de lenguaje no garantizan resultados idénticos, ni siquiera con la misma semilla. Por eso la reproducibilidad se diseña registrando, para cada ejecución, la versión del modelo y del prompt, el contexto recuperado, las salidas de cada herramienta y la versión de las políticas aplicadas. Con ese registro se pueden hacer auditorías de cumplimiento y análisis posteriores a un incidente (*post-mortems*).

### 4. Alineación y riesgos en sistemas multiagente

- **Alineación basada en incentivos:** en arquitecturas de enjambres, entender la teoría de juegos y los mecanismos de consenso que resisten comportamientos colusorios o maximizadores de recompensas desalineadas.
- **Fallas en cascada y agentes fuera de política:** un error o una instrucción maliciosa se propaga de un agente a otro. El Top 10 agéntico de OWASP lo trata como *Rogue Agents* (ASI10), con monitoreo del comportamiento y un interruptor de apagado (*kill switch*) como mitigaciones.
- **Confianza excesiva de las personas en el agente:** las salidas persuasivas del agente pueden llevar a una persona a aprobar una acción dañina (*Human-Agent Trust Exploitation*, ASI09). La arquitectura debe mostrar a quien aprueba qué se va a hacer, con qué datos y con qué efecto, y no solo la conclusión del agente.

Un arquitecto senior debe poder auditar su propia topología antes de llevarla a producción. Conviene asumir que cualquier agente conectado a herramientas con capacidad de escritura o de llamada a red será atacado tarde o temprano.

## II. Políticas como código, guardrails, gateways y registries de agentes

La evolución de los sistemas agénticos hacia entornos empresariales distribuidos exige trasladar a la capa de agentes los patrones de los microservicios y del service mesh, adaptados al razonamiento probabilístico y dinámico de los modelos de lenguaje.

Un arquitecto senior debe dominar cuatro capas operativas:

### 1. Políticas como código y autorización dinámica

- **OPA y Rego para el control de flujo y de herramientas:** no basta con validar esquemas estáticos. Un motor como Open Policy Agent, con políticas escritas en Rego, evalúa cada llamada a una herramienta y responde en tiempo de ejecución preguntas como esta: ¿este agente, en este contexto conversacional y con este usuario autenticado, tiene permiso de negocio para invocar la API de transferencias en este paso exacto?
- **Barandas semánticas y contextuales:** políticas basadas en el estado de la memoria y en la traza anterior, para impedir la deriva del agente (*agent drift*), por ejemplo cuando intenta saltarse una fase obligatoria como la validación de cumplimiento antes de una acción de escritura.

### 2. Guardrails de ejecución y validación estructurada

- **Validación determinista de entradas y salidas:** esquemas tipados (p. ej., Pydantic) que rechazan toda salida del modelo que no cumpla el contrato antes de que llegue a una herramienta. Es la baranda dura entre el razonamiento probabilístico y los efectos en el mundo real.
- **Guardrails de texto en tiempo de ejecución:** componentes como NeMo Guardrails, LLM Guard, Model Armor o Llama Guard filtran entradas y salidas, detectan inyecciones y enmascaran datos sensibles. Ningún filtro de texto sabe de quién es una cuenta, así que no reemplazan a la autorización en la herramienta.
- **No confundir con las herramientas de prueba:** garak, PyRIT y promptfoo no filtran tráfico. Atacan y miden el sistema antes del despliegue y durante la operación (ver la sección VI).

### 3. Gateways de agentes y proxies de inferencia

- **Control perimetral y enrutamiento inteligente:** así como un API Gateway gestiona el tráfico web, un Agent Gateway es el punto único de entrada y salida para las interacciones con modelos y agentes. Se encarga de:
  - **Sanitización y ofuscación:** detección y enmascaramiento de datos personales y secretos antes de que salgan hacia el proveedor del modelo.
  - **Límites de tasa y control de costos:** presupuestos basados en tokens y en complejidad de razonamiento por inquilino, usuario o sesión, para mitigar el *denial of wallet*.
  - **Enrutamiento por capacidad y costo:** derivar tareas a modelos más pequeños y baratos o a modelos de razonamiento profundo, según la criticidad.

### 4. Registries de agentes y catálogos de habilidades

- **Gobernanza de componentes reutilizables:** un Agent Registry es un repositorio central y versionado donde se publican agentes, subagentes, flujos declarativos y esquemas de herramientas certificados.
- **Integridad y ciclo de vida:** ningún agente ni servidor de herramientas (como un endpoint MCP) entra a una topología productiva sin escaneo automatizado de vulnerabilidades y sin metadatos criptográficos que verifiquen su procedencia y sus permisos. Es la defensa frente al riesgo de cadena de suministro (*Supply Chain*, LLM03).

La robustez de una arquitectura agéntica ya no depende solo de la calidad del prompt, sino de la solidez de la infraestructura de control que lo rodea.

## III. Otros temas de gobernanza

Además de las políticas en ejecución, los guardrails, los gateways y los registries, un arquitecto de IA agéntica en entornos empresariales complejos debe dominar la gobernanza en tres dimensiones que cierran el ciclo de vida, el cumplimiento normativo y la soberanía del dato:

### 1. Linaje de datos y trazabilidad de la memoria a largo plazo

- **Bases de conocimiento y RAG híbrido:** los agentes consumen bases vectoriales, grafos de conocimiento y almacenes de estado dinámicos. La gobernanza exige saber qué documento, fragmento o interacción previa llevó al agente a una decisión concreta.
- **Envenenamiento de memoria:** auditar y depurar periódicamente la memoria episódica y semántica frente a la inyección persistente de datos maliciosos que alteren el comportamiento a largo plazo (envenenamiento de bases vectoriales o secuestro de la memoria). OWASP lo recoge como *Data and Model Poisoning* (LLM04) y *Vector and Embedding Weaknesses* (LLM08).

### 2. Cumplimiento normativo y auditoría de cajas negras

- **Clasificación de riesgo:** la EU AI Act regula por uso de alto riesgo (anexo III), no por sector. Entre los usos listados están la evaluación de solvencia crediticia (anexo III, punto 5.b) y la evaluación de riesgos y precios en seguros de vida y de salud (punto 5.c). Las obligaciones para los sistemas del anexo III rigen desde el 2 de diciembre de 2027 y las del anexo I desde el 2 de agosto de 2028, tras el Digital Omnibus on AI. Las normas locales de protección de datos se suman a ese marco.
- **Supervisión humana (HITL):** para los usos de alto riesgo, el art. 14 exige supervisión humana efectiva y el art. 12 exige registro automático de eventos. El arquitecto diseña los puntos de aprobación humana y los activa por criterios objetivos, como el monto de la operación, su carácter irreversible o la sensibilidad de los datos. La confianza que declara el modelo es un mal disparador, porque no está bien calibrada.
- **Explicabilidad posterior y auditoría forense:** informes de auditoría estructurados y no alterables que certifiquen por qué un agente autónomo siguió una ruta de ejecución, a un nivel que satisfaga la auditabilidad corporativa y legal.

### 3. Soberanía, privacidad de datos e inferencia híbrida

- **Aislamiento y localidad del dato:** políticas estrictas sobre qué datos pueden salir hacia APIs comerciales de modelos y cuáles se procesan solo en modelos locales o en despliegues propios (por ejemplo con vLLM, Ollama o infraestructura on-premise).
- **Aislamiento entre inquilinos:** en arquitecturas multi-tenant, asegurar que la caché, el contexto de ejecución y los embeddings de un cliente no contaminen ni filtren información hacia el contexto de otro a través del razonamiento del agente.

## IV. Colaboración con otros roles y límites de responsabilidad

El arquitecto de IA agéntica es quien traduce las directrices estratégicas, legales y de seguridad de la organización en patrones de software. El límite fundamental es claro: los especialistas definen el qué (la política, el apetito de riesgo y la norma) y el arquitecto diseña el cómo (la infraestructura, los mecanismos de cumplimiento y la topología de ejecución).

La colaboración y la delimitación de fronteras se estructuran en cinco frentes:

### 1. CISO y equipos de seguridad de la información (SecOps)

- **El especialista (CISO y SecOps):** establece las políticas de control de acceso corporativo, gestiona el inventario de amenazas, define los estándares de IAM (gestión de identidades y accesos) y lidera la respuesta a incidentes a nivel empresarial.
- **El arquitecto de IA:** traduce esas directrices en aislamiento de runtime para agentes y servidores MCP, diseña los perímetros de ejecución de herramientas para prevenir el tool poisoning e implementa los guardrails de texto y el enmascaramiento de datos personales en el Agent Gateway.
- **El límite:** el CISO dice «nadie fuera de Finanzas puede aprobar transferencias». El arquitecto diseña el flujo para que la herramienta de pago requiera un token OAuth firmado por el sistema de identidad corporativo y verificado criptográficamente en el paso de ejecución.

### 2. Compliance, Legal y DPO (oficial de protección de datos)

- **El especialista (Compliance y Legal):** interpreta los marcos regulatorios aplicables, clasifica el nivel de riesgo de los casos de uso y redacta los términos de uso y las políticas de privacidad.
- **El arquitecto de IA:** diseña la arquitectura de datos y el flujo de inferencia que garantizan el cumplimiento técnico. Define qué datos se procesan en modelos on-premise para cumplir con la soberanía del dato, implementa los criterios técnicos que activan la supervisión humana y asegura la trazabilidad del linaje de la memoria.
- **El límite:** Legal determina que un proceso de crédito es de alto riesgo y exige supervisión humana. El arquitecto implementa la cola de revisión y el bloqueo asíncrono de las operaciones que superan el umbral definido. A modo de ejemplo ilustrativo, ese umbral puede ser un monto máximo por operación.

### 3. Gestión de riesgos empresariales y de modelos (ERM y MRM)

- **El especialista (gestión de riesgos):** define el apetito de riesgo de la organización, evalúa el impacto financiero o reputacional de las alucinaciones y de los fallos sistémicos, y valida modelos en entornos tradicionales de machine learning.
- **El arquitecto de IA:** diseña los mecanismos cuantitativos de mitigación del riesgo operativo: presupuestos de tokens por sesión contra el *denial of wallet*, disyuntores ante bucles infinitos y arquitecturas de respaldo (*fallback*) entre modelos.
- **El límite:** Riesgos fija la pérdida financiera máxima tolerable por un agente autónomo en un ciclo de ejecución. El arquitecto implementa límites estrictos a las llamadas a APIs transaccionales y compartimentos estancos (*bulkheads*) en el motor de políticas.

### 4. Auditoría interna y forense

- **El especialista (Auditoría):** diseña los planes de auditoría de controles internos, verifica el cumplimiento normativo y ejecuta revisiones periódicas retrospectivas.
- **El arquitecto de IA:** construye la infraestructura de observabilidad y trazabilidad inmutable (árboles de decisión exportables, logs estructurados vía OpenInference y snapshots de las bases de conocimiento) que hace auditable al sistema.
- **El límite:** Auditoría define qué evidencias necesita para certificar que el agente no violó regulaciones. El arquitecto implementa el pipeline de telemetría y el almacenamiento cifrado de trazas que generan esas evidencias de forma automática.

### 5. Infraestructura, Platform y SRE

- **El especialista (Platform y SRE):** gestiona los clústeres de Kubernetes, las políticas de red, la disponibilidad de la infraestructura y los pipelines de CI/CD.
- **El arquitecto de IA:** especifica los requisitos de cómputo y latencia de la inferencia local (por ejemplo, vLLM u Ollama), las redes aisladas entre agentes y servidores de herramientas, y los ciclos de despliegue de los artefactos agénticos (prompts, esquemas y políticas OPA versionadas).
- **El límite:** SRE garantiza que el clúster esté operativo según el nivel de servicio acordado. El arquitecto define cómo se reparte la carga de razonamiento pesado entre réplicas de modelos locales y APIs externas bajo restricciones estrictas de latencia.

## V. Marcos de referencia y threat modeling

El conocimiento de los marcos estandarizados y el modelado formal de amenazas son obligatorios para pasar de una prueba de concepto frágil a una arquitectura empresarial resiliente.

### 1. Marcos de referencia

Un arquitecto debe usar estos marcos de forma operativa y no solo teórica:

- **OWASP Top 10 for LLM Applications (2025):** taxonomía base de vulnerabilidades de las aplicaciones con modelos de lenguaje: LLM01 Prompt Injection, LLM02 Sensitive Information Disclosure, LLM03 Supply Chain, LLM04 Data and Model Poisoning, LLM05 Improper Output Handling, LLM06 Excessive Agency, LLM07 System Prompt Leakage, LLM08 Vector and Embedding Weaknesses, LLM09 Misinformation y LLM10 Unbounded Consumption.
- **OWASP Top 10 for Agentic Applications (2026, publicado en diciembre de 2025):** riesgos específicos de agentes que planifican, tienen memoria, llaman herramientas y actúan con autoridad delegada, como ASI01 Agent Goal Hijack, ASI02 Tool Misuse, ASI09 Human-Agent Trust Exploitation y ASI10 Rogue Agents.
- **MITRE ATLAS:** matriz de tácticas y técnicas de atacantes reales contra sistemas de IA. Para un agente, la técnica de partida es AML.T0051 LLM Prompt Injection (directa .000 e indirecta .001). AML.T0043 Craft Adversarial Data cubre los ejemplos adversariales de evasión.
- **MAESTRO (Cloud Security Alliance):** modelo de amenazas de siete capas pensado para IA agéntica: modelos de base, operaciones de datos, frameworks de agentes, despliegue e infraestructura, evaluación y observabilidad, seguridad y cumplimiento, y ecosistema de agentes.
- **NIST AI RMF y su perfil de IA generativa (NIST AI 600-1):** el ciclo de cuatro funciones (Govern, Map, Measure y Manage) para gobernar el riesgo durante todo el ciclo de vida. El perfil 600-1 detalla los riesgos propios de la IA generativa.
- **ISO/IEC 42001:** norma certificable de sistema de gestión de IA. Su Declaración de Aplicabilidad lista cada control con la justificación de por qué se incluye o se excluye, y es un buen modelo de vínculo entre riesgo y control.
- **EU AI Act:** ordena los requisitos por nivel de riesgo. Para el arquitecto pesan el sistema de gestión de riesgos (art. 9), el registro de eventos (art. 12), la supervisión humana (art. 14) y el reporte de incidentes graves (art. 73).

### 2. La matriz de amenazas y riesgos

El modelado de amenazas en arquitecturas agénticas adapta metodologías clásicas como STRIDE a componentes estocásticos y dinámicos. El resultado es una matriz de riesgos agénticos con estas columnas:

1. **Componente afectado:** p. ej., el núcleo del modelo, un servidor MCP, la base vectorial de memoria o una API de escritura.
2. **Vector de amenaza e identificadores:** p. ej., LLM01, ASI01 o AML.T0051.001.
3. **Escenario de explotación:** cómo un agente comprometido o un usuario malicioso activaría la vulnerabilidad en el bucle de varios pasos.
4. **Impacto y probabilidad:** cuantitativo (pérdida financiera, filtración de datos) y cualitativo.
5. **Control arquitectónico que lo mitiga:** el mecanismo técnico (validación OPA, guardrail, menor privilegio en la herramienta).
6. **Responsable:** quién define la política y quién implementa el control.
7. **Evidencia o prueba:** cómo se demuestra que el control funciona (prueba automatizada, traza, informe).

Ejemplo ilustrativo de una fila:

| Columna | Contenido |
|---|---|
| Componente | Herramienta de pago del agente |
| Vector | LLM01, ASI01, AML.T0051.001 (inyección indirecta) |
| Escenario | Un correo con instrucciones ocultas hace que el agente proponga una transferencia a una cuenta nueva |
| Impacto y probabilidad | Alto y media (valores de ejemplo) |
| Control mitigante | OPA autoriza la llamada solo con un token delegado del usuario, con alcance y monto limitados, y con aprobación humana sobre el umbral definido |
| Responsable | CISO define la política de pagos. El arquitecto implementa el control |
| Evidencia | Pruebas adversariales en CI (promptfoo, PyRIT) y traza de la decisión de OPA en Langfuse |

Esta matriz es la respuesta al hallazgo central del estudio «Unmitigated?» del MIT: las empresas dicen que mitigan riesgos, pero casi ninguna vincula cada mitigación con un riesgo concreto. Cada fila de la matriz hace ese vínculo de forma explícita y verificable.

## VI. Momento de aplicación

Seguridad y gobernanza no se aplican en una sola etapa. Siguen un enfoque *shift-left*, integrado de forma transversal en el ciclo de vida de desarrollo (SDLC) agéntico, y se reparten en tres momentos críticos. Cada uno corresponde a funciones del NIST AI RMF y deja evidencia propia.

| Fase | Funciones NIST | Qué se produce | Evidencia |
|---|---|---|---|
| Diseño | Govern y Map | Modelo de amenazas, arquitectura de gobernanza, clasificación de riesgo | Matriz de amenazas aprobada |
| Implementación y CI/CD | Measure | Pruebas adversariales, políticas versionadas, puerta de calidad | Resultados de las pruebas y decisión de la puerta |
| Despliegue y operación | Measure y Manage | Monitoreo, red teaming periódico, respuesta a incidentes | Trazas, informes de red teaming, registro de incidentes |

### A. Fase de diseño (arquitectura y modelado preventivo)

- **Cuándo:** antes de escribir código, al definir la topología y los diagramas de flujo de datos y herramientas.
- **Qué se hace:**
  - Se ejecuta el threat modeling inicial con OWASP, MITRE ATLAS y MAESTRO para detectar fallas estructurales de diseño, por ejemplo un agente con demasiada autonomía o con acceso de escritura sin mediación.
  - Se diseña la arquitectura de gobernanza: dónde residirán los gateways, cómo operarán las políticas OPA y Rego y qué aislamiento necesitarán los servidores MCP.
  - Se aplican las funciones Govern y Map del NIST AI RMF para clasificar el perfil de riesgo del caso de uso y se define qué usos serán de alto riesgo según la EU AI Act.
  - Se completa la primera versión de la matriz de amenazas, con responsable y evidencia esperada para cada control.

### B. Fase de implementación y CI/CD (pruebas automatizadas y políticas como código)

- **Cuándo:** durante el desarrollo de prompts, la codificación de herramientas y la integración continua.
- **Qué se hace:**
  - Se integran herramientas de prueba adversarial en el pipeline (garak, PyRIT, promptfoo) para medir la robustez frente a inyecciones y fugas de datos antes de fusionar el código.
  - Se versionan y se prueban de forma unitaria las políticas como código (Rego y OPA) y los esquemas estrictos de entrada y salida (Pydantic).
  - Se auditan de forma estática las dependencias y los repositorios de las herramientas conectadas.
  - Una puerta de calidad (*gate*) previa a producción evalúa seguridad y calidad por separado, con reglas independientes, y bloquea el despliegue si no se cumplen. Seguridad y calidad no se promedian.

### C. Fase de despliegue y operación (monitoreo, red teaming y auditoría continua)

- **Cuándo:** en producción, de forma iterativa y continua.
- **Qué se hace:**
  - Se implementa observabilidad en tiempo real, con trazabilidad de agentes vía OpenInference, Langfuse o MLflow, para detectar anomalías de comportamiento y bucles infinitos.
  - Se ejecutan ejercicios periódicos de red teaming de agentes para simular inyección indirecta avanzada y evaluar la resiliencia de los guardrails.
  - Se prepara y se ensaya la respuesta a incidentes: interruptor de apagado del agente, revocación de credenciales delegadas y reporte de incidentes graves a las autoridades cuando la norma lo exige (art. 73 de la EU AI Act para los sistemas de alto riesgo).
  - Se aplican las funciones Measure y Manage del NIST AI RMF y se actualiza la matriz de amenazas cuando el agente evoluciona o incorpora herramientas nuevas.
