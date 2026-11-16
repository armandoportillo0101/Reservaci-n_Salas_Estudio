# Sistema Web de Reservación de Salas de Estudio

Aplicación web desarrollada en **Python** y **Django 5.2 LTS** mediante **Desarrollo Guiado por Pruebas (TDD)** estricto para la gestión y reservación de salas de estudio.

---

## 1. Requisitos del Sistema

- **Python**: 3.11 o superior (probado en Python 3.13).
- **Framework**: Django 5.2 LTS (`>=5.2,<5.3`).
- **Gestor de paquetes**: `pip` y módulo `venv`.
- **Base de datos**: SQLite 3 (incluida por defecto con `transaction_mode="IMMEDIATE"`) o PostgreSQL (configurable por variables de entorno).

---

## 2. Creación del Entorno Virtual e Instalación

Desde la raíz del repositorio tras realizar un clon limpio:

### En Windows (PowerShell)
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### En Linux / macOS / Git Bash
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## 3. Configuración de Variables de Entorno

Copie el archivo de ejemplo `.env.example` a `.env`:

```powershell
Copy-Item .env.example .env
```
*(En Linux/macOS: `cp .env.example .env`)*

Variables soportadas en `.env`:
- `SECRET_KEY`: Clave criptográfica de Django.
- `DEBUG`: `True` para desarrollo, `False` para producción.
- `ALLOWED_HOSTS`: Lista separada por comas (ej. `localhost,127.0.0.1`).
- `DB_ENGINE`: Por defecto `django.db.backends.sqlite3`. Para PostgreSQL use `django.db.backends.postgresql`.
- `DB_NAME`: Nombre del archivo SQLite (por defecto `db.sqlite3`) o nombre de la base de datos en PostgreSQL.
- `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`: Credenciales de conexión cuando se utiliza PostgreSQL.

> **Nota**: Si no existe el archivo `.env`, `config/settings.py` utiliza valores por defecto seguros para desarrollo y pruebas locales sobre SQLite con `OPTIONS={"transaction_mode": "IMMEDIATE", "timeout": 20}`.

---

## 4. Migraciones y Carga de Datos Iniciales

Ejecute las migraciones versionadas y el comando idempotente `cargar_salas`:

```powershell
python manage.py migrate
python manage.py cargar_salas
```

El comando `cargar_salas` registra o actualiza de forma idempotente las **4 salas obligatorias**:
1. **Sala A** — Biblioteca, planta baja | Capacidad: 4 | Activa: Sí
2. **Sala B** — Biblioteca, planta baja | Capacidad: 8 | Activa: Sí
3. **Sala C** — Biblioteca, planta alta | Capacidad: 12 | Activa: Sí
4. **Sala de mantenimiento** — Biblioteca, planta alta | Capacidad: 6 | Activa: No (Inactiva)

---

## 5. Creación o Carga de Usuarios de Prueba

- Si ya se encuentra integrado el comando de la **Persona 3** (por ejemplo, `python manage.py cargar_usuarios_prueba` o `python manage.py crear_usuarios_prueba`), ejecútelo directamente:
  ```powershell
  python manage.py cargar_usuarios_prueba
  ```
- De manera alternativa o mientras se integra la parte de la Persona 3, puede crear un usuario de prueba reproducible desde la consola de Django:
  ```powershell
  python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); u, _ = User.objects.get_or_create(username='estudiante1'); u.set_password('password123'); u.save()"
  ```
  - **Usuario**: `estudiante1`
  - **Contraseña**: `password123`

---

## 6. Ejecución del Servidor de Desarrollo

```powershell
python manage.py runserver
```

Rutas principales del módulo `reservaciones` (namespace `reservaciones`):
- Formulario de nueva reservación (`reservaciones:nueva`): `http://127.0.0.1:8000/reservaciones/nueva/`
- Listado de reservaciones (`reservaciones:lista`): `http://127.0.0.1:8000/reservaciones/`

---

## 7. Ejecución de Pruebas, Cobertura, PEP 8 y Complejidad

### 7.1 Suite de pruebas unitarias y de integración
```powershell
python manage.py test -v 2
```

### 7.2 Cobertura de código (`coverage`)
```powershell
coverage run manage.py test
coverage report -m
coverage html
```
- El resumen en texto se guarda en `evidencias/cobertura.txt` y el reporte interactivo en `htmlcov/index.html`.

### 7.3 Verificación de estilo PEP 8 (`flake8`)
```powershell
flake8 . --exclude=.venv,migrations
```
- La evidencia se almacena en `evidencias/flake8.txt`.

### 7.4 Complejidad ciclomática (`radon`)
```powershell
radon cc . -s -a
```
*(La exclusión de migraciones y directorios de entorno está configurada en `radon.cfg` para evitar falsos filtros del flag `-x` / `--max` de Radon).*
- La evidencia se almacena en `evidencias/radon.txt`.

### 7.5 Script unificado de control de calidad
En Windows (PowerShell):
```powershell
.\run_checks.ps1
```
En Linux / macOS / Git Bash:
```bash
bash ./run_checks.sh
```

---

## 8. Justificación de Exclusiones de Cobertura (`.coveragerc`)

De acuerdo con el requerimiento técnico **RT-07**, el archivo `.coveragerc` excluye **únicamente** archivos autogenerados o de arranque/configuración sin lógica de negocio del dominio:

| Archivo / Patrón excluido | Justificación técnica |
| :--- | :--- |
| `*/migrations/*` | Archivos generados automáticamente por el motor de migraciones de Django para definir el esquema de base de datos; no contienen lógica de negocio. |
| `manage.py` | Script estándar de arranque de línea de comandos generado por Django (`execute_from_command_line`). |
| `config/settings.py` | Archivo declarativo de configuración del entorno e infraestructura del proyecto (sin reglas de negocio del dominio). |
| `config/wsgi.py` | Punto de entrada estándar del servidor de aplicaciones WSGI para despliegue en producción; no se invoca durante pruebas ni contiene lógica funcional. |
| `config/asgi.py` | Punto de entrada estándar del servidor ASGI; no contiene lógica de negocio. |

Todos los demás módulos (`models.py`, `messages.py`, `exceptions.py`, `validators.py`, `services/disponibilidad.py`, `services/reservaciones.py`, `views.py`, `forms.py`, `urls.py`, `management/commands/cargar_salas.py` y `tests/`) mantienen **100% de cobertura de líneas y ramas**.
