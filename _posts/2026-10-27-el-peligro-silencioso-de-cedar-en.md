---
layout: post
title: "El peligro silencioso de Cedar en la IA Agéntica"
date: 2026-10-27 00:47:27 -0300
description: "Cómo la combinación de políticas schemaless, el operador in y la semántica de tolerancia a errores abren puertas traseras invisibles en los agentes autónomos modernos."
thumbnail: /assets/img/el-peligro-silencioso-de-cedar-en/thumb.jpg
substack_url: "https://matiaszz.substack.com/p/el-peligro-silencioso-de-cedar-en"
---

En la era de la **IA Agéntica**, donde los modelos de lenguaje (LLMs) tienen capacidad de ejecutar comandos en terminales, interactuar con APIs externas, clonar repositorios y alterar bases de datos, la capa de *Policy-as-Code* (autorización basada en políticas) se ha convertido en la última línea de defensa.

Entre los motores más adoptados destaca **Cedar** (el lenguaje declarativo de autorización de código abierto de AWS). Sin embargo, en nuestra última investigación descubrimos cómo dos propiedades de diseño perfectamente válidas según la especificación formal de Cedar pueden combinarse para producir **fallos silenciosos de tipo** ***Fail-Open*** (bypass completo de autorización) completamente invisibles para los auditores.

### 📄 Paper Completo Disponible

Puedes descargar y leer el trabajo completo en formato PDF:

Cedar Schemaless Hazards In Agentic Ai

524KB ∙ PDF file

[Download](https://matiaszz.substack.com/api/v1/file/3c453456-3bc0-4a8e-9eed-633aa4275fd9.pdf)

## **1. Hazard 1 (H1): El “Silent Policy Discard”**

El primer hallazgo crítico radica en una sutil confusión sintáctica cuando Cedar se utiliza en **modo sin esquema (*****schemaless mode*****)**:

- El operador `in` en Cedar está diseñado *exclusivamente* para **jerarquías de entidades** (por ejemplo: `principal in Group::"admins"`).
- Cuando los desarrolladores quieren verificar la pertenencia de un string en una lista de comandos prohibidos (ej. `context.command in ["rm -rf", "git push"]`), Cedar en modo *schemaless* **acepta la sintaxis sin advertencias durante el parseo**.
- Sin embargo, en tiempo de ejecución (runtime), el motor detecta un error de tipo (*“expected entity, got string”*).
- Aquí entra la regla de **Error-Ignorance** de Cedar: ante un error en una regla, el motor no lanza una excepción fatal al llamador, sino que **descarta silenciosamente esa política** de la evaluación.

**El resultado es catastrófico:** si la política descartada era una regla `forbid` pensada para bloquear comandos peligrosos y existe una regla general de `permit` posterior, **la acción peligrosa se aprueba silenciosamente** (PERMIT) sin ningún registro de alarma para el host o el agente.

**─── FLUJO DEL BYPASS: SILENT POLICY DISCARD ───**

```
[ Agente LLM ]
      │
      ▼ Solicita: Tool Execution (”git push --force”)
[ Policy Enforcement Point (PEP) ]
      │
      ▼ Consulta a Cedar Evaluator
┌────────────────────────────────────────────────────────┐
│  POLÍTICA VULNERABLE:                                  │
│  forbid(...) when {                                    │
│    context.cmd in [”git push”, “rm -rf”]  ◄── [TRAMPA] │
│  };                                                    │
└────────────────────────────────────────────────────────┘
      │
      ▼ Runtime: Type Error (”expected Entity, got String”)
      │
      ▼ Semántica de Cedar: Error-Ignorance activado
┌────────────────────────────────────────────────────────┐
│  ⚠️ LA REGLA FORBID SE DESCARTA SILENCIOSAMENTE        │
└────────────────────────────────────────────────────────┘
      │
      ▼ Evaluación cae en el “permit” por defecto
      │
[ Decisión: ALLOWED (Permit) ] ──► 💥 Comando Crítico Ejecutado
```

### **El Código: La trampa y la corrección**

**❌ Política Vulnerable (Provoca bypass silencioso en schemaless):**

```
// BUG: 'in' espera una entidad, no un set de strings.
forbid (
    principal,
    action == Action::"execute_command",
    resource
)
when {
    context.command_pattern in ["git push", "gh pr merge", "rm -rf"]
};

permit (
    principal,
    action == Action::"execute_command",
    resource
);
```

**✅ Política Segura (Utilizando métodos de conjuntos y esquema tipado):**

```
// FIX: Usar .contains() y validar esquema con 'cedar validate' en CI
forbid (
    principal,
    action == Action::"execute_command",
    resource
)
when {
    ["git push", "gh pr merge", "rm -rf"].contains(context.command_pattern)
};
```

## **2. Impacto Real y Amplificación en la Cadena de Suministro**

Esto no es un escenario teórico. Durante la investigación encontramos esta vulnerabilidad activa en producción:

- **Repositorios de alto impacto:** Confirmamos el patrón H1 en repositorios de gobernanza de agentes con más de **37.000 estrellas en GitHub** (como `wshobson/agents`) y herramientas de control de agentes (`kenhuangus/agentctl`).
- **Amplificación de plugins:** La política vulnerable se propagó idéntica y sin modificaciones a múltiples entornos de usuario a través de marketplaces y plugins para asistentes de codificación agéntica (como Claude Code).
- **Auditoría en GitHub (n=199):** Un análisis aleatorio estimó que el **43.7%** de las políticas analizadas incurrían en mal uso del operador y un **25.1%** presentaban riesgo directo de *fail-open*.
- **Divulgación Responsable:** Coordinamos con los mantenedores la publicación del aviso de seguridad oficial **GHSA-hm46-7j72-rpv9** y el parche (PR #600) que integró tests de regresión y validación estricta de esquemas.

## **3. Hazard 2 (H2): La brecha de atestación (The Attestation Gap)**

El segundo hallazgo del trabajo aborda la semántica de los atributos del contexto:

Sintácticamente, en Cedar `context.attr` se escribe exactamente igual si el atributo fue suministrado por el propio agente/llamador (**OWA: Open World Assumption**, potencialmente bajo control del atacante mediante Prompt Injection) o si fue atestado y verificado criptográficamente por la infraestructura (**CWA: Closed World Assumption** / PEP-attested).

Esta indistinción provoca que los analizadores formales basados en solucionadores SMT (como Z3) generen hasta un **65% de falsas alarmas** al no poder discernir la procedencia confiable del dato. En el paper proponemos anotaciones explícitas (`@pep_attested` vs `@caller_supplied`) respaldadas por una formalización en **Lean 4** para resolver esta ambigüedad.

## **4. Comparativa de Modelos de Políticas**

**Motor / PatrónModoComportamiento ante ErrorPostura de SeguridadCedar (Schemaless)**Sin esquema en CIDescarta la regla (Error-Ignorance)**⚠️ Fail-Open en ForbidCedar (Schema-Enforced)**Con `cedar validate`Falla en compilación / despliegue**🛡️ Fail-Closed (Preventivo)OPA / Rego**Positive-condition allowRegla no satisfecha = Deny**🛡️ Fail-ClosedOPA / Rego**Negation-as-failureFalta de asignación = No bloqueo**⚠️ Fail-Open estructural**

## **5. Lecciones para desarrolladores de Agentes de IA**

1. **Nunca despliegues Cedar en modo schemaless a producción:** Integra `cedar validate` en tus pipelines de CI/CD para detectar incompatibilidades de tipos antes de que toquen el motor de decisión.
2. **Usa métodos de conjuntos explícitos:** Para comprobar strings en listas, usa `set.contains(item)` en lugar de `item in set`.
3. **Audita las respuestas completas del evaluador:** No leas únicamente el booleano `response.allowed`; inspecciona siempre el array de errores y advertencias de evaluación devuelto por el runtime.
4. **Separa la procedencia de los datos del contexto:** No mezcles datos controlados por el modelo (como argumentos generados por el LLM) con variables verificadas por el host de ejecución sin marcas explícitas de atestación.
