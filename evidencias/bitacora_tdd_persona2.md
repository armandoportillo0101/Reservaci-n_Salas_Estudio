# Bitácora TDD — Persona 2 (Formularios, Interfaz, Cancelación HU-02 y BDD CA-07 a CA-11)

Esta bitácora documenta los ciclos **Rojo → Verde → Refactor** ejecutados durante la construcción incremental de la parte correspondiente a la **Persona 2**, integrada directamente sobre el núcleo de **Persona 1**. Las salidas completas de consola de cada fase se encuentran en `evidencias/tdd/`.

| Ciclo | Prueba / Incremento | Evidencia Rojo / Verde | Commit Rojo (`test:`) | Commit Verde (`feat:`) |
| :---: | :--- | :--- | :---: | :---: |
| **08** | Formulario `ReservacionForm` (`T18`, `T19`, `T20`, `T33`, `T34`, `T35`): filtrado exclusivo de salas activas, pruebas `UT-02`, `UT-03`, `UT-05`, `UT-06`, límites `EXT-01`..`EXT-03` e integración `agregar_error_dominio` delegando toda regla a `reservaciones/validators.py` (`RT-03`). | `08_formulario_reservacion_rojo.txt` / `08_formulario_reservacion_verde.txt` | `e084baf` | `ebf3aff` |
| **09** | Servicio `cancelar_reservacion` y `puede_cancelar_reservacion` (`T21`, `T22`, `T26`, `T36`–`T38`, `T40`): reloj inyectable (`ahora`), pruebas `UT-13`..`UT-17`, `UT-20` y `EXT-09` (`61`, `60` y `59` min). | `09_servicio_cancelacion_rojo.txt` / `09_servicio_cancelacion_verde.txt` | `233fd1d` | `61aeb6e` |
| **10** | Vistas y plantillas de cancelación, confirmación previa y listado/historial (`T23`, `T24`, `T25`, `T39`, `T41`): pruebas `UT-18`, `UT-19`, `EXT-10` y `EXT-11` (`POST` con CSRF, `403` sin revelar datos sensibles e ID inexistente `404`). | `10_vistas_cancelacion_lista_rojo.txt` / `10_vistas_cancelacion_lista_verde.txt` | `b39fa20` | `24b7328` |
| **11** | Escenarios BDD `CA-07` a `CA-11` (`T54`–`T59`) con Behave y Selenium Headless, junto con `CA-01` a `CA-06` y pruebas de rendimiento JMeter. | `evidencias/bdd_ca01_a_ca11.txt` | `847f718` | `a8c49b1` |
