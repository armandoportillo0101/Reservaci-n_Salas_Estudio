# Bitácora TDD Consolidada del Equipo (Entregable E-09 — T81)

Esta bitácora consolida los **11 ciclos de Desarrollo Guiado por Pruebas (TDD)** ejecutados por los tres integrantes del equipo (**Persona 1: Armando — Backend HU-01**, **Persona 2: Guillermo Elizarraras — Formularios, Interfaz y Cancelación HU-02**, **Persona 3: Chuycastanedar — Usuarios de Prueba, BDD y Rendimiento**).

Cada incremento siguió estrictamente los 6 pasos metodológicos:
1. Escribir la prueba automatizada antes del código funcional (`test:`).
2. Ejecutar la prueba y conservar la evidencia de fallo en **Rojo** por la razón esperada (`evidencias/tdd/*_rojo.txt`).
3. Implementar el código mínimo necesario (`feat:`).
4. Ejecutar la suite completa para confirmar estado en **Verde** sin regresiones (`evidencias/tdd/*_verde.txt`).
5. Refactorizar manteniendo **PEP 8** (`flake8` = 0 errores), **complejidad ciclomática $\le 10$** (`radon` promedio **A**) y **100% de cobertura** (`coverage`).

---

## Tabla General de Ciclos TDD (01 al 11) con Commits del Repositorio

| Ciclo | Integrante | Funcionalidad / Casos de Prueba Cubiertos | Evidencia Rojo / Verde (`evidencias/tdd/`) | Commit Rojo (`test:`) | Commit Verde (`feat:`) | Refactor / Cierre |
| :---: | :---: | :--- | :--- | :---: | :---: | :---: |
| **01** | Persona 1 (`Armando`) | Modelos `Sala` y `Reservacion`, estados (`VIGENTE`, `CANCELADA`) y `CheckConstraint` en BD (`hora_fin > hora_inicio`, `asistentes >= 1`, `capacidad >= 1`). | [`01_modelos_rojo.txt`](tdd/01_modelos_rojo.txt) / [`01_modelos_verde.txt`](tdd/01_modelos_verde.txt) | `2e8d084` | `eafe975` | `70d409c` |
| **02** | Persona 1 (`Armando`) | Comando idempotente `cargar_salas` con las 4 salas iniciales obligatorias (`Sala A`, `Sala B`, `Sala C` activas y `Sala de mantenimiento` inactiva). | [`02_datos_iniciales_rojo.txt`](tdd/02_datos_iniciales_rojo.txt) / [`02_datos_iniciales_verde.txt`](tdd/02_datos_iniciales_verde.txt) | `9351058` | `59e6dad` | `70d409c` |
| **03** | Persona 1 (`Armando`) | Validadores reutilizables (`validators.py`): horario (`08:00`–`19:00`, fin $\le$ `20:00`), duración (`30`–`120` min, límites `29, 30, 120, 121`), fecha (`hoy` inyectable), asistentes, capacidad, propósito y sala activa. | [`03_validadores_rojo.txt`](tdd/03_validadores_rojo.txt) / [`03_validadores_verde.txt`](tdd/03_validadores_verde.txt) | `6e9252c` | `c1d4e35` | `70d409c` |
| **04** | Persona 1 (`Armando`) | Servicio `disponibilidad.py`: detección de traslapes (`RN-06`) solo contra reservaciones `VIGENTES` (`RN-07`, `RN-14`) y horarios adyacentes (`UT-08`, `UT-09`, `UT-10`). | [`04_disponibilidad_rojo.txt`](tdd/04_disponibilidad_rojo.txt) / [`04_disponibilidad_verde.txt`](tdd/04_disponibilidad_verde.txt) | `afe1e8e` | `27fd4b2` | `70d409c` |
| **05** | Persona 1 (`Armando`) | Servicio `crear_reservacion` (`services/reservaciones.py`): `UT-01`, `UT-04`, `UT-07`, `UT-08`, `UT-09`, `UT-10` y límites `EXT-04` a `EXT-08`. | [`05_crear_reservacion_rojo.txt`](tdd/05_crear_reservacion_rojo.txt) / [`05_crear_reservacion_verde.txt`](tdd/05_crear_reservacion_verde.txt) | `868bb08` | `1a4726d` | `70d409c` |
| **06** | Persona 1 (`Armando`) | Protección contra condiciones de carrera (`RN-08`, `IT-01`) con `TransactionTestCase` y 2 hilos simultáneos (`transaction.atomic()` + `select_for_update()`). | [`06_concurrencia_it01_rojo.txt`](tdd/06_concurrencia_it01_rojo.txt) / [`06_concurrencia_it01_verde.txt`](tdd/06_concurrencia_it01_verde.txt) | `a99ee21` | `ce4da41` | `70d409c` |
| **07** | Persona 1 (`Armando`) | Vista `nueva_reservacion` (`reservaciones:nueva`), pruebas `UT-11` (acceso anónimo redirige a login) y `UT-12` (`POST` válido crea `VIGENTE` y redirige con mensaje de éxito). | [`07_vista_nueva_reservacion_rojo.txt`](tdd/07_vista_nueva_reservacion_rojo.txt) / [`07_vista_nueva_reservacion_verde.txt`](tdd/07_vista_nueva_reservacion_verde.txt) | `a01777a` | `cc1822b` | `692cff7` |
| **08** | Persona 2 (`Guillermo Elizarraras`) | Formulario `ReservacionForm` (`T18`, `T19`, `T20`, `T33`–`T35`): salas activas, pruebas `UT-02`, `UT-03`, `UT-05`, `UT-06`, límites `EXT-01`..`EXT-03` e integración `agregar_error_dominio` delegando a `validators.py` (`RT-03`). | [`08_formulario_reservacion_rojo.txt`](tdd/08_formulario_reservacion_rojo.txt) / [`08_formulario_reservacion_verde.txt`](tdd/08_formulario_reservacion_verde.txt) | `e084baf` | `ebf3aff` | `100% cov` |
| **09** | Persona 2 (`Guillermo Elizarraras`) | Servicio `cancelar_reservacion` y `puede_cancelar_reservacion` (`T21`, `T22`, `T26`, `T36`–`T38`, `T40`): reloj inyectable (`ahora`), pruebas `UT-13`..`UT-17`, `UT-20` y `EXT-09` (`61`, `60` y `59` min). | [`09_servicio_cancelacion_rojo.txt`](tdd/09_servicio_cancelacion_rojo.txt) / [`09_servicio_cancelacion_verde.txt`](tdd/09_servicio_cancelacion_verde.txt) | `233fd1d` | `61aeb6e` | `100% cov` |
| **10** | Persona 2 (`Guillermo Elizarraras`) | Vistas y plantillas de cancelación, confirmación previa y listado/historial (`T23`–`T25`, `T39`, `T41`): pruebas `UT-18`, `UT-19`, `EXT-10` y `EXT-11` (`POST` con CSRF, `403` sin filtrar datos ajenos, trazabilidad en historial). | [`10_vistas_cancelacion_lista_rojo.txt`](tdd/10_vistas_cancelacion_lista_rojo.txt) / [`10_vistas_cancelacion_lista_verde.txt`](tdd/10_vistas_cancelacion_lista_verde.txt) | `b39fa20` | `24b7328` | `100% cov` |
| **11** | Persona 3 (`Chuycastanedar`) | Comando idempotente `cargar_usuarios_prueba` (`T12`) para crear usuarios reproducibles de BDD (`propietario`, `otro_usuario`) y lote de 50 usuarios de JMeter (`usuario_perf_01`..`50`). | [`11_usuarios_prueba_rojo.txt`](tdd/11_usuarios_prueba_rojo.txt) / [`11_usuarios_prueba_verde.txt`](tdd/11_usuarios_prueba_verde.txt) | `847f718` | `5771ce1` | `a8c49b1` / `6cd4454` |

---

## Resumen Final de Verificación de la Suite

- **Total de pruebas unitarias y de integración ejecutadas:** `52` pruebas (`OK`).
- **Cobertura de código (`coverage report -m`):** **100%** (`954` sentencias, `0` faltantes; `86` ramas, `0` parciales) — [`evidencias/cobertura.txt`](cobertura.txt).
- **Cumplimiento PEP 8 (`flake8 . --exclude=.venv,migrations`):** **0 errores** — [`evidencias/flake8.txt`](flake8.txt).
- **Complejidad Ciclomática (`radon cc . -s -a`):** Promedio **A (1.79)**, máximo **6** ($\le 10$) — [`evidencias/radon.txt`](radon.txt).
- **Escenarios BDD (`behave`):** `2 features passed, 13 scenarios passed, 69 steps passed` (`CA-01` a `CA-11`) — [`evidencias/bdd_ca01_a_ca11.txt`](bdd_ca01_a_ca11.txt).
