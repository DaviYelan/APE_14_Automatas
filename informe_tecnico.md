# Informe Técnico — Práctica Nro. 12

**Asignatura:** Teoría de Autómatas y Computabilidad Avanzada
**Práctica:** Analizador léxico, sintáctico. LLM y PLN
**Compilador elegido:** Contexto 1 — Compilador de Ecuaciones de Primer Grado (NLP-Math)
**Docente:** José O. Guamán Q.
**Facultad:** FEIRNNR — Carrera de Computación — UNL

---

## 1. Descripción general de la solución

Se implementó un mini-compilador cuya fase de análisis léxico combina dos
estrategias complementarias bajo el patrón de diseño **Strategy**:

1. **`AutomataStrategy`**: simula un Autómata Finito Determinista (AFD)
   mediante expresiones regulares compiladas en un único patrón maestro
   con grupos nombrados. Reconoce los tokens "duros" o simbólicos del
   lenguaje: `VAR`, `NUMERO`, `OP_SUMA` (`+`), `OP_RESTA` (`-`) y
   `OP_ASIGNACION` (`=`). Todo fragmento que no encaja en estos patrones
   se clasifica como `TEXTO_LN` y queda pendiente de interpretación
   semántica.

2. **`LLMStrategy`**: actúa como un "Tokenizador Normalizador" apoyado en
   un LLM servido por Ollama. Recibe cada fragmento `TEXTO_LN` (por
   ejemplo "más", "es igual a") y lo traduce a su token formal
   equivalente (`OP_SUMA`, `OP_ASIGNACION`), validando que la respuesta
   pertenezca al catálogo oficial de tokens antes de aceptarla.

El componente `LexerEngine` orquesta ambas estrategias: ejecuta primero
el AFD de forma síncrona (es CPU-bound y prácticamente instantáneo) y
luego despacha **todos los fragmentos `TEXTO_LN` en paralelo** mediante
`ThreadPoolExecutor`, demostrando concurrencia real durante las
consultas al LLM (operación I/O-bound).

### Diseño de tokens oficiales

| Token            | Descripción                              | Origen   |
|------------------|-------------------------------------------|----------|
| `VAR`            | Variable matemática (una letra: x, y, z)  | AFD      |
| `NUMERO`         | Entero o decimal                          | AFD      |
| `OP_SUMA`        | Operador de suma (+)                      | AFD/LLM  |
| `OP_RESTA`       | Operador de resta (-)                     | AFD/LLM  |
| `OP_ASIGNACION`  | Operador de igualdad (=)                  | AFD/LLM  |
| `TEXTO_LN`       | Fragmento crudo en lenguaje natural        | AFD      |
| `DESCONOCIDO`    | El LLM no pudo clasificar el fragmento     | LLM      |

---

## 2. Evidencia de ejecución concurrente

Entrada de prueba: `2x más 5 es igual a 13`

```
[AFD][Hilo-AFD] Tokenización formal completada en 0.062 ms -> 6 tokens crudos
[LexerEngine] AFD produjo 4 tokens formales y detectó 2 fragmentos en
lenguaje natural para enviar al LLM.
[LLM][ThreadPoolExecutor-0_0] Fragmento='más' -> OP_SUMA (94.2 ms)
[LLM][ThreadPoolExecutor-0_1] Fragmento='es igual a' -> OP_ASIGNACION (101.7 ms)
[LexerEngine] Hilos activos durante el análisis: ['Hilo-AFD',
'ThreadPoolExecutor-0_0', 'ThreadPoolExecutor-0_1']
[LexerEngine] Tiempo total léxico: 108.43 ms
```

El AFD resuelve la parte formal en menos de 1 milisegundo en el hilo
principal (`Hilo-AFD`). Los dos fragmentos en lenguaje natural se envían
simultáneamente a hilos distintos del `ThreadPoolExecutor`
(`ThreadPoolExecutor-0_0` y `ThreadPoolExecutor-0_1`), de modo que el
tiempo total se aproxima al tiempo de la consulta LLM más lenta, **no**
a la suma de ambas consultas — confirmando el comportamiento esperado
en la sección 6 de la guía.

### Tabla de observaciones

| Compilador elegido: NLP-Math | Tokens AFD (Sintácticos) | Tokens LLM (Semánticos/NLN) | Hilos concurrentes activos | Tiempo Total Léxico (ms) |
|---|---|---|---|---|
| Prueba 1: `2x más 5 es igual a 13` | NUMERO, VAR, NUMERO, NUMERO | OP_SUMA, OP_ASIGNACION | Hilo-AFD, ThreadPoolExecutor-0_0, ThreadPoolExecutor-0_1 | ~100–150 |
| Prueba 2: `x menos 3 es igual a 7` | VAR, NUMERO, NUMERO | OP_RESTA, OP_ASIGNACION | Hilo-AFD, ThreadPoolExecutor-0_0, ThreadPoolExecutor-0_1 | ~100–150 |
| Prueba 3: `3y más 4 es igual a 22` | NUMERO, VAR, NUMERO, NUMERO | OP_SUMA, OP_ASIGNACION | Hilo-AFD, ThreadPoolExecutor-0_0, ThreadPoolExecutor-0_1 | ~100–150 |

*Nota: los tiempos exactos dependen del hardware y de la latencia real
del modelo Ollama en ejecución; los valores mostrados son referenciales
obtenidos en pruebas locales con `llama3.2:1b`.*

---

## 3. Respuestas a las preguntas de control

### 3.1. ¿Por qué los compiladores tradicionales (ej. GCC) no usan un LLM en la fase léxica, y por qué en un DSL híbrido sí es justificable?

Los compiladores tradicionales como GCC procesan lenguajes formales con
gramáticas completamente no ambiguas, definidas por especificaciones
estrictas (el estándar C, C++, etc.). Un AFD/expresión regular resuelve
esa tokenización en tiempo lineal, de forma determinista, reproducible
y sin coste de inferencia. Introducir un LLM ahí añadiría latencia,
no-determinismo (la misma entrada podría tokenizarse distinto entre
ejecuciones) y una dependencia externa innecesaria, sin ningún beneficio,
ya que no existe ambigüedad léxica que resolver.

En cambio, un DSL híbrido como el de esta práctica acepta **lenguaje
natural mezclado con símbolos formales** (números, operadores). Las
palabras "más" o "es igual a" no tienen una forma léxica fija: pueden
expresarse de muchas maneras ("sumado a", "más", "y", "equivale a"), lo
cual es un problema de *comprensión semántica*, no de reconocimiento de
patrones puros. Ahí el LLM aporta valor real: actúa como una capa de
normalización semántica antes de que el parser formal reciba tokens
limpios y predecibles. El AFD sigue resolviendo todo lo que sí es
determinista (números, variables, símbolos), preservando velocidad y
confiabilidad donde corresponde.

### 3.2. Si el LLM devuelve un token fuera del catálogo oficial (ej. `OP_MULTIPLICACION` cuando solo se aceptan suma y resta), ¿en qué fase fallará y cómo se debe manejar?

Si no se valida la respuesta del LLM, el error se propagaría hasta la
**fase de análisis sintáctico (parser)**: el parser recibiría un token
que no aparece en su gramática (no tiene una regla de producción para
`OP_MULTIPLICACION`), y fallaría ahí con un error de sintaxis poco claro,
mezclando responsabilidades entre la capa léxica y la sintáctica.

La solución implementada en `LLMStrategy._parsear_respuesta()` resuelve
esto **en la propia fase léxica**: se mantiene un conjunto explícito
`_TOKENS_SEMANTICOS_VALIDOS` y cualquier respuesta del LLM que no
pertenezca a él se reclasifica inmediatamente como `DESCONOCIDO`. Esto
traslada el fallo a un punto temprano, predecible y con información
clara (`DESCONOCIDO` en vez de un error de parsing críptico), permitiendo
que capas posteriores decidan cómo reaccionar (rechazar la entrada,
pedir aclaración al usuario, etc.) sin contaminar la gramática formal
del parser con tokens no soportados.

### 3.3. Si el AFD no tuviera el patrón `TEXTO_LN` y simplemente ignorara las palabras, ¿qué problema presentaría el flujo de tokens hacia el Parser?

Si las palabras en lenguaje natural se descartaran silenciosamente, el
flujo de tokens hacia el parser quedaría **incompleto y semánticamente
roto**: para la entrada `2x más 5 es igual a 13`, en vez de recibir
`NUMERO(2) VAR(x) OP_SUMA NUMERO(5) OP_ASIGNACION NUMERO(13)`, el parser
recibiría únicamente `NUMERO(2) VAR(x) NUMERO(5) NUMERO(13)` — sin
operadores. El parser no tendría forma de saber si esos números deben
sumarse, restarse o cómo se relacionan, y probablemente fallaría con un
error de "token inesperado" o, peor, generaría una interpretación
incorrecta sin lanzar ningún error (un fallo silencioso, el más peligroso
en compiladores). El patrón `TEXTO_LN` es indispensable porque preserva
esos fragmentos para que el LLM los traduzca, evitando pérdida de
información estructural del lenguaje de entrada.

### 3.4. ¿Por qué la llamada al LLM es una operación "I/O-Bound" y cómo soluciona el `ThreadPoolExecutor` el cuello de botella sin violar el GIL?

La llamada al LLM (`OllamaClient.generate`) realiza una petición HTTP
hacia el servicio Ollama y espera su respuesta. Durante esa espera, el
hilo de Python no está realizando cómputo activo de CPU: está bloqueado
esperando datos de la red/disco (donde corre el modelo). Esto la
clasifica como una operación **I/O-bound**, no CPU-bound.

El **GIL (Global Interpreter Lock)** de Python impide que dos hilos
ejecuten bytecode Python simultáneamente, lo cual sí sería un problema
real para tareas CPU-bound (cómputo puro). Sin embargo, durante una
operación de I/O —como una petición de red con la librería `requests`—
el intérprete **libera el GIL** mientras el hilo espera la respuesta del
sistema operativo. Esto permite que otros hilos del `ThreadPoolExecutor`
avancen y realicen sus propias peticiones de red en ese mismo intervalo,
logrando concurrencia real (aunque no paralelismo de cómputo) sin violar
ninguna restricción del GIL. Por eso `ThreadPoolExecutor` es la
herramienta correcta aquí: para I/O-bound, hilos son suficientes y
mucho más livianos que procesos (que sí serían necesarios para evitar
el GIL en tareas CPU-bound).

### 3.5. Si no se usa el patrón Strategy y todo el código (AFD + LLM) se escribe en una sola función secuencial, ¿cuál es el impacto en mantenibilidad al cambiar el modelo LLM de GPT-3.5 a Llama-3?

Sin el patrón Strategy, la lógica de tokenización regex y la lógica de
llamada al LLM estarían entrelazadas en una única función: condicionales,
parseo de respuesta, manejo de errores y regex todo mezclado. Cambiar de
proveedor LLM (de GPT-3.5 a Llama-3, o de Llama-3 a cualquier otro
modelo futuro) obligaría a **modificar directamente esa función
monolítica**, con alto riesgo de romper accidentalmente la lógica del
AFD que convive en el mismo bloque de código. Cada cambio de proveedor
requeriría re-testear todo el pipeline léxico completo, no solo la parte
LLM.

Con el patrón Strategy implementado (`AutomataStrategy` y `LLMStrategy`
como clases independientes que implementan la interfaz común
`TokenizerStrategy`), cambiar de modelo implica modificar **únicamente**
`OllamaClient` (o crear una nueva clase, ej. `OpenAIClient`, e inyectarla
en `LLMStrategy` vía su constructor) sin tocar `AutomataStrategy` ni
`LexerEngine`. El bajo acoplamiento reduce el radio de impacto de
cualquier cambio, facilita las pruebas unitarias (se puede mockear
`OllamaClient` sin levantar Ollama real, como se hizo durante el
desarrollo de este proyecto) y permite escalar a más estrategias futuras
(por ejemplo, una tercera estrategia basada en reglas heurísticas) sin
reescribir el motor léxico.

---

## 4. Arquitectura del proyecto

```
backend/
├── strategies/
│   ├── base_strategy.py      # Interfaz Strategy (TokenizerStrategy)
│   ├── automata_strategy.py  # AFD vía expresiones regulares
│   ├── llm_strategy.py       # Tokenizador semántico vía Ollama
│   └── lexer_engine.py       # Orquestador: AFD + ThreadPoolExecutor
├── services/
│   └── ollama_client.py      # Cliente HTTP desacoplado hacia Ollama
├── models/
│   └── token.py              # Modelo de datos Token (contrato común)
└── main.py                   # API FastAPI

frontend/
├── index.html / styles.css / app.js   # UI estática (sin frameworks)
├── config.js                          # Inyectado en runtime (puerto backend)
└── entrypoint.sh                      # Genera config.js desde .env
```

## 5. Conclusiones

El sistema demuestra de forma práctica cómo combinar un análisis léxico
formal (determinista, rápido, basado en AFD/regex) con un análisis
semántico asistido por LLM (flexible, tolerante a variaciones del
lenguaje natural, pero no determinista) bajo una arquitectura desacoplada
mediante el patrón Strategy. La ejecución concurrente vía
`ThreadPoolExecutor` resuelve el cuello de botella de latencia inherente
a las consultas LLM, validando empíricamente los conceptos de operaciones
I/O-bound y el comportamiento del GIL de Python en escenarios de
concurrencia basada en hilos.
