# Resumen e Interpretación de Pruebas de Rendimiento y Concurrencia (Apache JMeter — E-08)

Este documento presenta el resumen de métricas exportadas (`T70`), la interpretación técnica de resultados y cuellos de botella (`T71`) y la evidencia de integridad transaccional en base de datos (`T68`) correspondientes a los escenarios obligatorios **PERF-01**, **PERF-02** y **PERF-03**.

---

## 1. Archivos de Evidencia Generados (`E-08`)

- **Plan de pruebas ejecutable:** [`jmeter/plan_pruebas_reservaciones.jmx`](../jmeter/plan_pruebas_reservaciones.jmx) (`T63`, `T69`)
- **Datos parametrizados sin traslape (90 registros):** [`jmeter/datos_perf02.csv`](../jmeter/datos_perf02.csv) (`T64`, `T69`)
- **Bitácora cruda de muestras (`.jtl`):** [`jmeter/resultados.jtl`](../jmeter/resultados.jtl) (`T69`)
- **Reporte HTML interactivo y JSON de estadísticas:** [`evidencias/jmeter_reporte_html/index.html`](jmeter_reporte_html/index.html) y [`evidencias/jmeter_reporte_html/statistics.json`](jmeter_reporte_html/statistics.json) (`T69`)
- **Verificación de ausencia de traslapes en Base de Datos tras `PERF-03`:** [`evidencias/jmeter_verificacion_bd_perf03.txt`](jmeter_verificacion_bd_perf03.txt) (`T68`)

---

## 2. Tabla Resumen de Resultados (`T70` / `EVP-4`)

| Escenario / Transacción | Muestras (`# Samples`) | Promedio (`Average`) | Mediana (`Median`) | Percentil 90 (`p90`) | Percentil 95 (`p95`) | Percentil 99 (`p99`) | Throughput (`req/s`) | % Error (`KO %`) | Criterio Esperado | Resultado |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- | :---: |
| **PERF-01:** `GET /reservaciones/` (50 usuarios, 5 iteraciones) | 250 | 2.26 ms | 1.0 ms | 4.0 ms | **7.0 ms** | 23.0 ms | 189.83 req/s | **0.0%** | Error $< 1\%$; $p95 \le 1500\text{ ms}$ | ✅ **CUMPLE** |
| **PERF-02:** `POST /reservaciones/nueva/` sin conflicto (30 usuarios, 3 iteraciones) | 90 | 9.02 ms | 5.5 ms | 16.0 ms | **24.0 ms** | 104.0 ms | 91.19 req/s | **0.0%** | Error $< 1\%$; $p95 \le 2000\text{ ms}$ | ✅ **CUMPLE** |
| **PERF-03:** `POST /reservaciones/nueva/` concurrente (10 repeticiones $\times$ 2 hilos simultáneos) | 20 | 5.95 ms | 6.0 ms | 7.0 ms | **7.0 ms** | 7.0 ms | 16.08 req/s | **0.0%** | Nunca persisten 2 vigentes traslapadas | ✅ **CUMPLE** |
| **Total Consolidado** | **360** | **4.16 ms** | **2.0 ms** | **9.0 ms** | **14.0 ms** | **36.0 ms** | **93.82 req/s** | **0.0%** | Todos los umbrales cumplidos | ✅ **CUMPLE** |

---

## 3. Interpretación de Resultados y Análisis de Cuellos de Botella (`T71` / `EVP-5`)

1. **Comportamiento en Lectura (`PERF-01` — Consulta de listado e historial):**
   - El listado del usuario (`GET /reservaciones/`) registró un tiempo promedio de **2.26 ms** y un percentil 95 de **7.0 ms** (muy por debajo del límite máximo de $1500\text{ ms}$) con **0.0% de errores**.
   - **Optimización aplicada:** El uso de `select_related("sala")` en `lista_reservaciones` (`reservaciones/views.py`) evita el problema de consultas $N+1$ al renderizar el nombre y ubicación de la sala en cada fila del historial.

2. **Comportamiento en Escritura Parametrizada (`PERF-02` — Registro sin conflicto):**
   - El registro de 90 reservaciones parametrizadas mediante `jmeter/datos_perf02.csv` obtuvo un promedio de **9.02 ms**, percentil 90 de **16.0 ms** y percentil 95 de **24.0 ms** (frente al umbral máximo de $2000\text{ ms}$), con **0.0% de errores**.
   - **Cuello de botella identificado:** El percentil 99 sube a **104.0 ms** debido a la serialización de transacciones de escritura en SQLite (`OPTIONS={"transaction_mode": "IMMEDIATE", "timeout": 20}`). Cuando múltiples hilos coinciden en el inicio de `with transaction.atomic():`, SQLite encola las transacciones de escritura de manera secuencial. Aun así, el tiempo de bloqueo por transacción es de apenas ~3–8 ms, por lo que la cola se drena sin acercarse al timeout de 20 s ni degradar el $p95$. En un despliegue con PostgreSQL, `SELECT ... FOR UPDATE` sobre `Sala` bloquea únicamente la fila de la sala específica permitiendo escrituras paralelas entre distintas salas (`Sala A`, `Sala B` y `Sala C`).

3. **Control de Concurrencia (`PERF-03` y verificación de Base de Datos `T68`):**
   - En las **10 repeticiones controladas** con disparo simultáneo sobre la misma sala (`Sala A`), misma fecha y mismo horario (`14:00`–`15:00`), la primera transacción en adquirir el bloqueo registró la reservación con estado `VIGENTE` y la segunda transacción observó de inmediato el registro confirmado y recibió la respuesta controlada `"La sala no está disponible en el horario solicitado."`.
   - La auditoría SQL post-ejecución ([`evidencias/jmeter_verificacion_bd_perf03.txt`](jmeter_verificacion_bd_perf03.txt)) demostró **0 pares de reservaciones vigentes traslapadas** en toda la tabla `reservaciones_reservacion`.
