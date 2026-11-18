# Guion de Demostración Funcional en Vivo (Entregable E-10 — T82)

Este documento describe los pasos exactos para preparar la base de datos limpia con los datos iniciales obligatorios y demostrar en vivo las dos historias de usuario (**HU-01: Registrar una reservación** y **HU-02: Cancelar una reservación vigente**) durante la revisión.

---

## 1. Preparación Previa a la Demostración (1 minuto)

Ejecutar en la terminal desde la raíz del proyecto para garantizar una base de datos limpia con las 4 salas obligatorias y las cuentas de prueba listas:

```bash
source .venv/bin/activate
python manage.py migrate
python manage.py shell -c "from reservaciones.models import Reservacion; Reservacion.objects.all().delete()"
python manage.py cargar_salas
python manage.py cargar_usuarios_prueba
python manage.py runserver 127.0.0.1:8000
```

Abrir en el navegador: **http://127.0.0.1:8000/**

---

## 2. Flujo 1 — Autenticación y Registro de Reservación (`HU-01`: `CA-01` a `CA-05`)

1. **Inicio de sesión (`RT-04`):**
   - Al entrar a `http://127.0.0.1:8000/`, el sistema redirige automáticamente a `/accounts/login/`.
   - Ingresar con `propietario` / `TestPass123!` y pulsar **Ingresar al sistema**.
2. **Exploración del formulario (`FL1-01`, `FL1-02`):**
   - Hacer clic en **+ Nueva Reservación** (`/reservaciones/nueva/`).
   - Mostrar que el selector **Sala** únicamente lista las 3 salas activas (`Sala A`, `Sala B`, `Sala C`) y excluye `Sala de mantenimiento` (`RN-01`).
3. **Demostración de validaciones y conservación de datos (`FL1-06`, `CA-03`, `CA-04`):**
   - Seleccionar `Sala A` (capacidad máxima 4), fecha de mañana, horario `10:00` a `11:00`, escribir `5` en **Asistentes** y propósito `"Sesión de estudio grupal para examen extraordinario"`.
   - Pulsar **Reservar sala**: observar el mensaje `"El número de asistentes supera la capacidad de la sala."` y comprobar que todos los datos capturados se conservan en el formulario.
4. **Registro exitoso (`CA-01`):**
   - Corregir **Asistentes** a `3` y pulsar **Reservar sala**.
   - El sistema redirige a **Mis Reservaciones e Historial** (`/reservaciones/`), muestra la alerta verde `"Reservación registrada correctamente."` y presenta la reservación con insignia **`VIGENTE`**.
5. **Rechazo de horario traslapado (`CA-02`):**
   - Ir nuevamente a **+ Nueva Reservación**, elegir `Sala A`, la misma fecha de mañana, horario `10:30` a `11:30`, `2` asistentes y propósito `"Segundo intento en horario traslapado"`.
   - Pulsar **Reservar sala**: observar el mensaje `"La sala no está disponible en el horario solicitado."`.

---

## 3. Flujo 2 — Cancelación de Reservación y Trazabilidad (`HU-02`: `CA-07` a `CA-11`)

1. **Verificación de botón condicional y confirmación previa (`FL2-02`, `FL2-03`):**
   - En **Mis Reservaciones e Historial** (`/reservaciones/`), ubicar la reservación vigente de mañana (`10:00 - 11:00`). Como faltan más de 60 minutos para su inicio, aparece el botón rojo **Cancelar**.
   - Pulsar **Cancelar**: el sistema lleva a la pantalla de confirmación previa (`/reservaciones/<id>/confirmar-cancelacion/`) mostrando el resumen completo de la reservación.
2. **Confirmación de cancelación y trazabilidad en el historial (`CA-07`, `CA-11`):**
   - Pulsar **Confirmar cancelación** (envío `POST` con protección CSRF).
   - Observar el mensaje `"Reservación cancelada correctamente."`.
   - Verificar en la tabla que el registro **no fue eliminado** (`RN-12`), su estado cambió a **`CANCELADA`**, el botón de cancelar desapareció y la columna **Fecha de Cancelación** muestra la fecha y hora exacta en que se efectuó la operación (`RN-13`, `CA-11`).
3. **Comprobación de liberación del horario (`RN-07`, `RN-14`, `UT-20`):**
   - Ir a **+ Nueva Reservación** y registrar nuevamente `Sala A` en la misma fecha de mañana de `10:00` a `11:00` con `2` asistentes.
   - Comprobar que ahora el sistema **sí permite** registrar la nueva reservación con estado **`VIGENTE`**, coexistiendo en la tabla con el registro histórico **`CANCELADA`**.
