# Lista de Verificación de Revisión Cruzada: Persona 1 → Persona 2

**Estado global de la revisión**: **PENDIENTE** *(en espera de que exista el código implementado por la Persona 2; no rellenar hasta entonces)*.

| # | Criterio de verificación | Archivos / Componentes a revisar de Persona 2 | Estado | Observaciones |
| :-: | :--- | :--- | :---: | :--- |
| 1 | **Sin reglas de negocio duplicadas (RT-03)** | `forms.py`, `views.py`, plantillas HTML y cualquier archivo JS. Verificar que toda validación de dominio invoque a `reservaciones/validators.py` o `reservaciones/services/`. | PENDIENTE | |
| 2 | **Nombres y convenciones consistentes (PEP 8 / RT-08)** | Nombres de funciones, clases, variables, rutas (`reservaciones:nueva`, `reservaciones:lista`, etc.) e IDs de campos en plantillas (`id_sala`, `id_fecha`, `id_hora_inicio`, `id_hora_fin`, `id_asistentes`, `id_proposito`). | PENDIENTE | |
| 3 | **Complejidad ciclomática ≤ 10 (RT-09)** | Ejecutar `radon cc . -s -a` sobre los formularios, vistas y servicios agregados por la Persona 2 y comprobar que ningún bloque supere 10. | PENDIENTE | |
| 4 | **Cobertura del 100% (RT-07)** | Ejecutar `coverage run manage.py test` y `coverage report -m` verificando 100% de líneas y ramas en los archivos funcionales de la Persona 2. | PENDIENTE | |
| 5 | **Protección CSRF, método POST y autorización (RT-12)** | Verificar que toda operación que modifique datos (como cancelación de reservación) use exclusivamente `POST`, incluya `{% csrf_token %}` y valide autenticación/propiedad en el servidor. | PENDIENTE | |
| 6 | **Uso de mensajes centralizados (`messages.py`)** | Comprobar que todos los mensajes mostrados o validados provengan de las constantes definidas en `reservaciones/messages.py`, sin cadenas literales repetidas. | PENDIENTE | |
