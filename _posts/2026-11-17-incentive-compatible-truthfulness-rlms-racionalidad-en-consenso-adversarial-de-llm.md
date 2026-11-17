---
layout: post
title: "Veracidad como equilibrio: RLMS y la frontera de abstención en el consenso adversarial de LLM"
date: 2026-11-17 03:30:00 -0300
description: "Análisis detallado del paper «Incentive-Compatible Truthfulness»: por qué un LLM entrenado para ser servicial pierde dinero en un protocolo con slashing, y qué cambia si se lo alinea con señales de mercado."
thumbnail: /assets/img/incentive-compatible-truthfulness-rlms-racionalidad-en-consenso-adversarial-de-llm/thumb.jpg
tags: [rlms, grpo, alineación, teoría-de-juegos, consenso]
---

Este artículo analiza el paper **«Incentive-Compatible Truthfulness: Engineering Rationality in Adversarial LLM Consensus via Reinforcement Learning from Market Signals (RLMS)»** (versión del 9 de diciembre de 2025). El texto completo está disponible en OpenReview: [paper completo (PDF)](https://openreview.net/pdf?id=2oOLWuZVQV). Primero resumo el planteo, luego la formalización y la arquitectura, después los resultados con sus cifras, y cierro con una lectura del alcance de la evidencia.

## Tesis

Los modelos de lenguaje ajustados con RLHF optimizan la utilidad conversacional. En un protocolo de consenso con incentivos económicos, esa propiedad se vuelve un defecto. El paper la llama **Stubborn Compliance** (cumplimiento obstinado): la tendencia del modelo a satisfacer la instrucción aunque su propio conocimiento latente indique que la solicitud es insegura o inconsistente.

En un sistema con *staking* y *slashing*, un agente que aprueba una transición de estado inválida (por ejemplo, código malicioso) no comete solo una falla de seguridad: pierde capital. De ahí la tesis central: la veracidad de un agente autónomo no se trata como virtud abstracta sino como **estrategia de equilibrio en un juego de incentivos asimétricos**.

La propuesta, **Reinforcement Learning from Market Signals (RLMS)**, sustituye la recompensa de un modelo entrenado con preferencias humanas por el retorno de un entorno económico. La implementación es una arquitectura de doble proceso:

- **Sistema 1:** una política generativa ajustada por *fine-tuning*.
- **Sistema 2:** una envoltura de evaluación de riesgo, entrenada con Group Relative Policy Optimization (GRPO), que estima la utilidad esperada de actuar frente a abstenerse.

## El juego formal

La interacción entre un agente LLM y el protocolo se modela como un juego bayesiano Γ = ⟨N, Ω, A, T, u⟩:

- **N**: el conjunto de agentes.
- **Ω**: el espacio de prompts x. Cada x tiene una validez verdadera y(x) ∈ {−1, 1} (maliciosa o falsa frente a segura o verdadera).
- **A = {−1, 0, 1}**: rechazar, abstenerse, aprobar.

El pago del agente depende de una recompensa **R** por acertar y una penalización de *slashing* **S** por errar. Abstenerse no cuesta ni paga:

| Acción | Resultado | Pago |
|---|---|---|
| Votar y coincidir con la validez real | acierto | +R |
| Votar y no coincidir | error | −S |
| Abstenerse (a = 0) | sin voto | 0 |

El supuesto clave es que el costo del error es asimétrico: **S ≫ R**, modelado como S = λ·R con λ ≥ 4.

## La frontera de abstención

Si P(y|x) es la creencia interna del agente sobre la validez del prompt, la utilidad esperada de votar es:

```
E[U_votar]     = P(y|x)·R − (1 − P(y|x))·S
E[U_abstener]  = 0
```

Un agente racional vota si y solo si E[U_votar] > E[U_abstener]. Despejando se obtiene el **Teorema 2.1 (umbral de racionalidad)**: el agente actúa si y solo si

```
P(y|x) > τ = S / (S + R) = λ / (λ + 1)
```

Con λ = 4 el umbral es τ = 0,8. En el experimento (R = 50, S = 250, es decir λ = 5) es τ ≈ 0,833. Cuanto más caro es el error, más cerca de 1 sube el umbral y más conviene abstenerse.

El paper sostiene que los LLM calibrados por entropía cruzada para minimizar la perplejidad rara vez respetan este umbral y muestran exceso de confianza fuera de distribución. RLMS busca alinear las log-probabilidades de la política con esa superficie de riesgo económico.

## Arquitectura en tres fases

**Fase 1: SFT de dominio financiero.** El modelo base (Llama-3-8B) se ajusta con un corpus de lógica financiera, vulnerabilidades de contratos inteligentes y escenarios de teoría de juegos. Esto define la «superficie de capacidad» del modelo.

**Fase 2: GRPO.** El paper elige GRPO en lugar de PPO porque elimina el crítico: la línea base se estima a partir del promedio de un grupo de G salidas muestreadas para cada prompt, lo que evita duplicar la memoria. La ventaja de cada salida se normaliza dentro del grupo:

```
A_i = ( R(o_i) − media({R(o_j)}) ) / desvío({R(o_j)})
```

El objetivo usa el cociente de probabilidades con *clipping* de PPO. La recompensa combina tres indicadores:

```
R(o) = α·I_formato + β·I_seguridad + γ·I_racionalidad
```

I_racionalidad penaliza la inconsistencia entre la cadena de razonamiento y el veredicto final. Apunta a la conducta sicofántica en la que el modelo identifica un riesgo y aun así genera el código. El resultado esperado es una «cadena de pensamiento de seguridad» latente.

**Fase 3: envoltura en inferencia.** Una técnica de *prefix forcing* inyecta la secuencia `[SAFETY ANALYSIS]` en el decodificador. La salida se interpreta de forma determinista (Algoritmo 1):

| Señal en la cadena de razonamiento | Voto |
|---|---|
| `[UNSAFE]` | −1 (rechazar) |
| `[SAFE]` | +1 (aprobar) |
| `[AMBIGUOUS]` | 0 (abstenerse) |

La decisión final no la toma el texto libre del modelo, sino un parser sobre la señal. La abstención es así un resultado de primera clase y no un fallo del formato.

## Evaluación: el «Battle Royale»

La validación es una simulación de Monte Carlo de **T = 50 rondas** de votación de consenso:

- **Economía:** riqueza inicial W₀ = 1000, R = 50, S = 250 (λ = 5).
- **Conjunto de evaluación:** 50 prompts. 40 % maliciosos (contratos tipo Ponzi, bots de *wash trading*, *keyloggers*), 40 % seguros (derivaciones matemáticas, consultas SQL, teoría financiera) y 20 % difusos (zonas grises, como la elusión fiscal agresiva), pensados para poner a prueba la frontera de abstención.
- **Políticas comparadas:** el sicofante ingenuo (Llama-3-Instruct, siempre vota +1), el paranoico ingenuo (siempre vota −1 en prompts técnicos) y el agente racional (GRPO con envoltura).

Resultados que reporta el paper:

| Política | Resultado |
|---|---|
| Sicofante ingenuo | Quiebra (W ≤ 0) en la ronda 8, por repetidos eventos de *slashing* |
| Paranoico ingenuo | Sobrevive pero no crece: curva de capital estancada por el costo de oportunidad de rechazar prompts seguros (el «impuesto de alineación») |
| Racional (RLMS) | W₅₀ ≈ 2520; clasifica correctamente el 98 % de los prompts seguros y se abstiene en el 90 % de los difusos |

**Ablación sobre el vector de *wash trading*.** Aísla el aporte de la envoltura de inferencia:

| Modelo | ¿Se dispara el análisis? | ¿Rechaza? | Resultado |
|---|---|---|---|
| SFT base | No | No | *Slashing* |
| Solo GRPO | Sí | Parcial | Riesgo |
| GRPO + envoltura | Sí | Sí | Solvencia |

Solo GRPO ya activa el análisis, pero el rechazo es parcial. La envoltura es la que convierte la señal en conducta.

**Generalización fuera de distribución.** Con ataques ausentes del entrenamiento (por ejemplo, algoritmos de *smurfing*), el modelo emitió igualmente `[UNSAFE]`, lo que el paper interpreta como una representación general de «ilegalidad financiera» y no como memorización de exploits concretos. También observó una **disociación razonamiento-acción** en tareas puramente semánticas (análisis de uso de información privilegiada): la cadena de razonamiento identificaba el delito, pero el voto final quedaba ambiguo. El «gradiente de rechazo» sería más empinado en generación de código que en clasificación de lenguaje natural.

## Lectura del alcance de la evidencia

Un análisis formal exige separar lo que el paper demuestra de lo que sugiere.

1. **El resultado teórico es sólido y acotado.** El umbral τ = λ/(λ+1) sale directamente de comparar utilidades esperadas. Vale si las creencias P(y|x) están calibradas. El paper reconoce que los LLM típicos no lo están, y **no mide la calibración** del agente entrenado. El texto dice que RLMS «busca alinear» la política con esa superficie, no que lo haya verificado con una métrica de calibración.
2. **«Señales de mercado» son simuladas.** La recompensa de entrenamiento se construye con indicadores de formato, seguridad y racionalidad evaluados sobre las salidas, y el propio texto las llama señales de mercado *simuladas*. El entorno económico es un modelo de pagos, no un protocolo en producción.
3. **La evaluación es pequeña.** Son 50 prompts, 50 rondas y una sola configuración económica (λ = 5). El texto no informa el número de repeticiones de la simulación, las semillas ni intervalos de confianza. Además, el 98 % de aciertos sobre prompts seguros no se puede obtener con 20 prompts en una sola corrida (serían 19,6), de modo que probablemente agrega varias corridas, algo que el texto no detalla.
4. **No hay comparación con otros métodos de alineación.** Los baselines son dos políticas de conducta fija. No se compara contra un modelo alineado con RLHF o DPO con umbral de confianza, que sería el contrafactual relevante para atribuir el beneficio a RLMS y no solo a abstenerse.
5. **Los términos de equilibrio piden cautela.** La conclusión habla de «estrategia evolutivamente estable» y la introducción de «equilibrio de Nash». Lo que el paper deriva es una regla de decisión individual (maximizar utilidad esperada), no un equilibrio del juego entre múltiples agentes que se adaptan. Esa extensión queda en la agenda futura.

Estas observaciones no invalidan la contribución. Delimitan qué respalda la evidencia: una formalización clara de por qué la abstención es racional bajo pagos asimétricos y una prueba de concepto de que la envoltura en inferencia traduce la señal en conducta.

## Relación con RLMS-Shield

El umbral de abstención y el marco de pagos reaparecen en el paper aceptado en IEEE TPS 2026 (RLMS-Shield), que lo aplica a la auditoría de jueces en *red-teaming* automático y lo evalúa también con datos reales. Lo analicé en [«Aceptaron nuestro paper en IEEE TPS 2026»](/posts/2026/aceptaron-nuestro-paper-en-ieee-tps/). Son experimentos distintos y sus cifras no son comparables entre sí: allí el agente racional termina con 1350 de riqueza y los baselines quiebran en las rondas 3 y 9, mientras que en este paper el sicofante quiebra en la ronda 8 y el agente racional llega a unos 2520. Para el problema general de que el optimizador explote un proxy, ver [reward hacking y penalización KL](/posts/2026/reward-hacking-por-que-el-optimizador-explota-el-proxy/).

## Trabajo futuro

El paper propone tres vectores:

- **Interpretabilidad mecanicista de la veracidad.** Hipótesis: existe una «dirección de rechazo» lineal en el flujo residual. Con PCA sobre activaciones de la capa L, comparando prompts maliciosos y seguros, se aislaría un «vector de verdad» para hacer *steering* y ajustar el umbral τ sin reentrenar.
- **Robustez adversarial (RL contra RL).** Una política atacante entrenada con PPO para maximizar la probabilidad de que el agente racional emita tokens inseguros, frente a una política defensora que minimiza la divergencia KL respecto de las restricciones de seguridad. Se espera que ese entrenamiento de equilibrio cierre la brecha de generalización fuera de distribución.
- **Consenso con *commit-reveal*.** Para evitar el *mirror voting* (copiar el voto de pares con alta reputación), cada agente publica c_i = SHA256(v_i ‖ r_i) con un nonce aleatorio r_i. Así el consenso agrega verificaciones independientes, que es la condición de independencia estadística del teorema del jurado de Condorcet.

## Conclusión

El paper sostiene que la veracidad incentivo-compatible no es una propiedad emergente de la escala sino una propiedad **de ingeniería**, resultado del diseño de mecanismo. Su aporte más reutilizable es conceptual: cuando el error cuesta λ veces lo que paga el acierto, abstenerse deja de ser una falla y pasa a ser la decisión correcta por debajo de un umbral de confianza explícito. Queda pendiente la evidencia que lo sostenga a escala: calibración medida, más repeticiones, baselines de alineación comparables y un equilibrio multiagente derivado.

## Referencias principales del paper

- Christiano et al. (2017). *Deep Reinforcement Learning from Human Preferences.* NeurIPS.
- Shao et al. (2024). *DeepSeekMath* (introduce GRPO). arXiv:2402.03300.
- Sharma et al. (2023). *Towards Understanding Sycophancy in Language Models.* arXiv:2310.13548.
- Hanson (2013). *Shall we vote on values, but bet on beliefs?* Journal of Political Philosophy.
- Rafailov et al. (2023). *Direct Preference Optimization.* NeurIPS.
- Bai et al. (2022). *Constitutional AI.* arXiv:2212.08073.
