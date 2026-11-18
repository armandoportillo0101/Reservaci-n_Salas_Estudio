# Sistema Web de Reservación de Salas de Estudio

Aplicación web desarrollada en **Python** y **Django 5.2 LTS** mediante **Desarrollo Guiado por Pruebas (TDD)** y **Desarrollo Guiado por Comportamiento (BDD)** para la reservación y cancelación de salas de estudio.

---

## 1. Requisitos del Sistema

- **Python**: 3.11 o superior (probado en Python 3.13 y 3.14).
- **Framework**: Django 5.2 LTS (`>=5.2,<5.3`).
- **Automatización BDD**: `behave` y `selenium` (modo headless Chrome/Chromium/Brave).
- **Pruebas de Rendimiento**: Apache JMeter 5.6+.
- **Base de datos**: SQLite 3 (incluida por defecto con `transaction_mode="IMMEDIATE"`) o PostgreSQL (configurable por variables de entorno).

---

## 2. Creación del Entorno Virtual e Instalación

Desde la raíz del repositorio tras realizar un clon limpio:

### En Linux / macOS / Git Bash
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### En Windows (PowerShell)
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

---

## 3. Configuración de Variables de Entorno

Copie el archivo de ejemplo `.env.example` a `.env`:

```bash
cp .env.example .env
```

Variables soportadas en `.env`:
- `SECRET_KEY`: Clave criptográfica de Django.
- `DEBUG`: `True` para desarrollo, `False` para producción / pruebas de carga.
- `ALLOWED_HOSTS`: Lista separada por comas (ej. `localhost,127.0.0.1`).
- `DB_ENGINE`: Por defecto `django.db.backends.sqlite3`. Para PostgreSQL use `django.db.backends.postgresql`.
- `DB_NAME`: Nombre del archivo SQLite (por defecto `db.sqlite3`) o nombre de la base de datos en PostgreSQL.
- `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`: Credenciales de conexión cuando se utiliza PostgreSQL.

---

## 4. Migraciones, Salas Iniciales y Usuarios de Prueba (`T09` y `T12`)

Ejecute las migraciones versionadas y los dos comandos idempotentes de carga inicial:

```bash
python manage.py migrate
python manage.py cargar_salas
python manage.py cargar_usuarios_prueba
```

### 4.1 Salas iniciales cargadas (`cargar_salas`)
1. **Sala A** — Biblioteca, planta baja | Capacidad: 4 | Activa: Sí
2. **Sala B** — Biblioteca, planta baja | Capacidad: 8 | Activa: Sí
3. **Sala C** — Biblioteca, planta alta | Capacidad: 12 | Activa: Sí
4. **Sala de mantenimiento** — Biblioteca, planta alta | Capacidad: 6 | Activa: No (Inactiva)

### 4.2 Credenciales de usuarios de prueba (`cargar_usuarios_prueba`)
- **Usuario propietario (BDD y Demo):** `propietario` / `TestPass123!`
- **Segundo usuario (BDD y Demo):** `otro_usuario` / `TestPass123!`
- **Lote de 50 usuarios para JMeter (`PERF-01` a `PERF-03`):** `usuario_perf_01` a `usuario_perf_50` / `TestPass123!`

---

## 5. Ejecución del Servidor de Desarrollo y Rutas

```bash
python manage.py runserver
```

Rutas principales del sistema:
- Raíz (`/`): Redirige automáticamente al listado de reservaciones (`/reservaciones/`).
- Inicio de sesión (`login`): `http://127.0.0.1:8000/accounts/login/`
- Listado e historial de reservaciones (`reservaciones:lista`): `http://127.0.0.1:8000/reservaciones/`
- Formulario de nueva reservación (`reservaciones:nueva`): `http://127.0.0.1:8000/reservaciones/nueva/`
- Confirmación previa de cancelación (`reservaciones:confirmar_cancelacion`): `http://127.0.0.1:8000/reservaciones/<id>/confirmar-cancelacion/`
- Ejecución de cancelación por POST (`reservaciones:cancelar`): `http://127.0.0.1:8000/reservaciones/<id>/cancelar/`

---

## 6. Ejecución de Pruebas Unitarias, Cobertura, PEP 8 y Complejidad

### 6.1 Suite de pruebas unitarias y de integración (51 pruebas: HU-01 + Formularios + HU-02 + Comandos)
```bash
python manage.py test -v 2
```

### 6.2 Cobertura de código (`coverage` — 100% sentencias y ramas)
```bash
coverage run manage.py test
coverage report -m --fail-under=100
coverage html
```
- El resumen en texto se guarda en `evidencias/cobertura.txt` y el reporte HTML en `htmlcov/index.html`.

### 6.3 Verificación de estilo PEP 8 (`flake8`)
```bash
flake8 . --exclude=.venv,migrations
```
- La evidencia limpia se almacena en `evidencias/flake8.txt`.

### 6.4 Complejidad ciclomática (`radon`)
```bash
radon cc . -s -a
```
- La evidencia se almacena en `evidencias/radon.txt` (promedio **A**, ningún método o función supera 10).

### 6.5 Script unificado de verificación (`T76`)
```bash
bash ./run_checks.sh
```
*(En Windows PowerShell: `.\run_checks.ps1`)*

---

## 7. Automatización BDD con Behave y Selenium Headless (`E-04` / `T80`)

Los 11 criterios de aceptación obligatorios (**`CA-01` a `CA-06`** en `features/reservaciones.feature` y **`CA-07` a `CA-11`** en `features/cancelaciones.feature`) se ejecutan desde la interfaz web mediante un navegador headless:

```bash
behave
```

También puede ejecutar cada historia de usuario por separado:
```bash
behave features/reservaciones.feature
behave features/cancelaciones.feature
```

- La salida completa de los 2 features (13 escenarios / 69 pasos aprobados) se encuentra en `evidencias/bdd_ca01_a_ca11.txt`.

---

## 8. Pruebas de Rendimiento y Concurrencia con Apache JMeter (`E-08` / `T80`)

### 8.1 Archivos incluidos
- **Plan de pruebas `.jmx`:** `jmeter/plan_pruebas_reservaciones.jmx`
  - **Grupo 1 (`PERF-01`):** 50 usuarios virtuales, subida (`ramp-up`) de 30 s, 5 iteraciones de `GET /reservaciones/` tras autenticar con extracción de CSRF.
  - **Grupo 2 (`PERF-02`):** 30 usuarios virtuales, subida de 30 s, 3 iteraciones de `POST /reservaciones/nueva/` parametrizadas mediante CSV sin traslape.
  - **Grupo 3 (`PERF-03`):** Solicitudes `POST /reservaciones/nueva/` simultáneas para la misma sala y horario sincronizadas con `Synchronizing Timer` (10 repeticiones controladas).
- **Datos parametrizados CSV:** `jmeter/datos_perf02.csv` (90 combinaciones únicas sin traslape).
- **Resultados y evidencias:**
  - Bitácora de muestras: `jmeter/resultados.jtl`
  - Reporte HTML de JMeter: `evidencias/jmeter_reporte_html/index.html`
  - Resumen e interpretación de cuellos de botella: `evidencias/jmeter_resumen_e_interpretacion.md`
  - Verificación en BD post-`PERF-03` (0 traslapes vigentes): `evidencias/jmeter_verificacion_bd_perf03.txt`

### 8.2 Cómo abrir el plan en JMeter GUI o generar el reporte desde terminal
1. Preparar la instancia estable con `DEBUG=False`, salas y usuarios de prueba:
   ```bash
   python manage.py migrate
   python manage.py cargar_salas
   python manage.py cargar_usuarios_prueba
   DEBUG=False python manage.py runserver 127.0.0.1:8000 --noreload
   ```
2. Para abrir el plan en la interfaz gráfica de JMeter:
   ```bash
   jmeter -t jmeter/plan_pruebas_reservaciones.jmx
   ```
3. Para ejecutar en modo no-GUI y generar el reporte HTML:
   ```bash
   jmeter -n -t jmeter/plan_pruebas_reservaciones.jmx -l jmeter/resultados.jtl -e -o evidencias/jmeter_reporte_html
   ```

---

## 9. Justificación de Exclusiones de Cobertura (`.coveragerc`)

De acuerdo con el requerimiento técnico **RT-07**, el archivo `.coveragerc` excluye **únicamente** archivos autogenerados o de arranque/configuración sin lógica de negocio del dominio:

| Archivo / Patrón excluido | Justificación técnica |
| :--- | :--- |
| `*/migrations/*` | Archivos generados automáticamente por el motor de migraciones de Django para definir el esquema de base de datos; no contienen lógica de negocio. |
| `manage.py` | Script estándar de arranque de línea de comandos generado por Django (`execute_from_command_line`). |
| `config/settings.py` | Archivo declarativo de configuración del entorno e infraestructura del proyecto (sin reglas de negocio del dominio). |
| `config/wsgi.py` | Punto de entrada estándar del servidor de aplicaciones WSGI para despliegue en producción; no se invoca durante pruebas ni contiene lógica funcional. |
| `config/asgi.py` | Punto de entrada estándar del servidor ASGI; no contiene lógica de negocio. |

Todos los demás módulos (`models.py`, `messages.py`, `exceptions.py`, `validators.py`, `services/disponibilidad.py`, `services/reservaciones.py`, `services/cancelaciones.py`, `views.py`, `forms.py`, `urls.py`, `management/commands/cargar_salas.py`, `management/commands/cargar_usuarios_prueba.py` y `tests/`) mantienen **100% de cobertura de líneas y ramas**.
