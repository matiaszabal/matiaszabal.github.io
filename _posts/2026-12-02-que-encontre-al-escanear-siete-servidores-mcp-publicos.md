---
layout: post
title: "Qué encontré al escanear siete servidores MCP públicos"
date: 2026-12-02 05:30:00 -0300
description: "Un escaneo estático de siete repositorios, qué encontró, qué no puede decir y por qué una corrección tras un aviso externo no es lo mismo que un control continuo."
thumbnail: /assets/img/que-encontre-al-escanear-siete-servidores-mcp-publicos/thumb.jpg
---

El 3 de septiembre de 2026 hice un primer escaneo de **siete repositorios públicos de servidores MCP**: uno de referencia oficial y seis comunitarios o de terceros. No nombro a los proyectos comunitarios: el objetivo es entender el método y sus límites, no señalar a nadie.

## Qué hice

Un escaneo **estático**, sin ejecutar nada:

- Patrones de riesgo en el código: ejecución de comandos de shell sin sanitizar, `eval`, secretos escritos en el código y recorrido de rutas (*path traversal*).
- Revisión de las descripciones de herramientas y recursos en busca de *tool poisoning*, es decir, instrucciones ocultas dirigidas al modelo.

## Qué salió

| Grupo | Archivos escaneados | Hallazgos | Veredicto |
|---|---|---|---|
| Servidor de referencia oficial | 90 | 0 (2 falsos positivos por la palabra «base64») | Limpio |
| Servidor comunitario grande | 346 | 17, todos falsos positivos | Limpio |
| Servidor de un proveedor | 58 | 0 | Limpio |
| Tres servidores chicos (5 a 14 archivos) | 5 a 14 cada uno | 0 | Limpios, con poca cobertura |
| Un servidor comunitario con un aviso previo | 14 | 0 | **Remediado** |

Los 17 falsos positivos del servidor grande eran nombres de campo como `client_secret` o tokens de prueba en archivos de test, no secretos reales. Un patrón demasiado amplio genera ruido, y en un repositorio grande ese ruido se multiplica.

## El caso más interesante no es un bug nuevo

Uno de los servidores comunitarios había tenido una **inyección de comandos** divulgada públicamente por otro investigador, con una puntuación de gravedad alta: una herramienta armaba un comando de shell concatenando un valor sin sanitizar, de modo que una inyección de prompt podía colar metacaracteres y ejecutar código en el equipo. Al momento del aviso no había versión corregida.

Al revisar el estado actual del código confirmé que se corrigió bien:

- Dejó de ejecutar el comando por una vía que interpreta el shell y pasa a invocar el programa con los argumentos como lista.
- Valida con expresiones regulares explícitas los valores que recibe antes de usarlos.
- El archivo temporal usa un nombre aleatorio, no uno controlable por quien llama, lo que cierra también el recorrido de rutas.

La remediación es correcta. Lo que **no** vi es evidencia de un chequeo continuo que la hubiera detectado antes: la corrección llegó después de que alguien de afuera lo encontró y lo reportó. Una revisión de seguridad única no dice nada sobre lo que ese código puede volver a introducir en la próxima versión.

## Qué no dice este escaneo

- **Ningún repositorio del lote tiene hoy una vulnerabilidad estática explotable de las que busqué.** Eso no equivale a que sean seguros.
- Los repositorios chicos pesan menos: con 5 a 14 archivos hay poca superficie para que aparezca algo.
- No hice pruebas dinámicas: no levanté los servidores para atacarlos en ejecución.
- No revisé los permisos que declara cada servidor ni cuánto acceso piden de más.
- Una muestra de siete, elegida por mí, no es representativa del ecosistema.

## Qué es opinión y qué no

- Los resultados son del escaneo del 3/09/2026 y pueden haber cambiado.
- Que el riesgo real esté más en desarrolladores individuales con poco tráfico que en proyectos conocidos es una **hipótesis** que este caso sugiere, no una conclusión: con una muestra tan chica no se puede afirmar.
- Que haga falta un chequeo continuo es mi posición de investigación, coherente con el tema de mi doctorado.
