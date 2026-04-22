# Biometric Fullstack System

Repositorio: `Bananice-666/biometric-fullstack-system`  
Rama: `main`

Sistema **full-stack** de biometría facial compuesto por:
- **Backend** (Python + FastAPI): API para enrolar, verificar, identificar y administrar sujetos biométricos, con persistencia en MongoDB.
- **Frontend** (React + TypeScript): dashboard web que usa la cámara del navegador para capturar rostros y operar contra la API.
- **Orquestación**: `docker-compose.yml` para levantar ambos servicios.

## Composición de lenguajes (aprox.)
- Python
- TypeScript

---

## Estructura del repositorio

En la raíz:

- `docker-compose.yml`  
- `be-service-boimetrics-ali/` (backend)  
- `fe-web-dashboard-iot/` (frontend)

---

## Ejecución con Docker Compose

El archivo `docker-compose.yml` define:

- `backend`
  - `build: ./be-service-boimetrics-ali`
  - `ports: "8000:8000"`

- `frontend`
  - `build: ./fe-web-dashboard-iot`
  - `ports: "5173:5173"`
  - `depends_on: backend`

### Levantar todo
Desde la raíz:

```bash
docker compose up --build
```

### URLs
- Backend: `http://localhost:8000`
- Frontend: `http://localhost:5173`

---

## Backend (FastAPI): `be-service-boimetrics-ali/`

### Descripción
Servicio backend en Python para biometría facial con FastAPI.

Incluye:
- **Enrolamiento** de sujetos con una imagen.
- **Verificación** facial (1:1) contra una identidad registrada.
- **Identificación** (1:N) contra todas las plantillas almacenadas.
- Persistencia en **MongoDB Atlas** usando la base de datos `biometrics`.
- Capa de servicio desacoplada para poder reemplazar el motor por un modelo real más adelante.

> Nota técnica (según README): el motor actual extrae un vector normalizado y una rejilla de **64 puntos faciales** sobre la imagen procesada. Eso se guarda en MongoDB y se usa para comparación por **similitud coseno**.

### Stack declarado
- Python 3.8+
- FastAPI
- Uvicorn
- Pillow
- NumPy
- PyMongo

### Instalación (local)
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Configuración MongoDB (variables de entorno)
Definir:

- `MONGODB_URI` (cadena de conexión a Atlas)
- `MONGODB_DB_NAME` (opcional; por defecto `biometrics`)

Ejemplo (PowerShell):
```powershell
$env:MONGODB_URI="mongodb+srv://<usuario>:<clave>@<cluster>/<params>"
$env:MONGODB_DB_NAME="biometrics"
```

### Ejecutar backend
```powershell
uvicorn app.main:app --reload
```

API disponible en:
- `http://127.0.0.1:8000`

### Endpoints documentados
- `GET /health`
- `POST /api/v1/enroll`
- `POST /api/v1/verify`
- `POST /api/v1/identify`
- `GET /api/v1/subjects`
- `GET /api/v1/subjects/{subject_id}`
- `DELETE /api/v1/subjects/{subject_id}`

---

## Frontend (React + TypeScript): `fe-web-dashboard-iot/`

### Descripción
Frontend en React + TypeScript para registrar rostros e iniciar sesión usando la cámara del navegador.

### Flujo (según README)
- **Registrarte**: abre la cámara, captura un frame del rostro y envía los puntos faciales al backend para enrolarlo.
- **Iniciar sesión**: abre la cámara, captura un frame y valida el rostro contra lo guardado en la base de datos.
- El panel muestra el estado de la cámara, la sesión activa y la lista de sujetos almacenados.

### Ejecutar frontend
```powershell
npm install
npm run dev
```

### Configuración de URL(s) del backend
Por defecto el frontend prueba:
- `http://localhost:8000`
- `http://192.168.18.191:8000`

Para usar otras URLs, definir:
- `VITE_BIOMETRY_API_URL` con una o varias direcciones separadas por coma.

Ejemplo:
```bash
# una URL
VITE_BIOMETRY_API_URL=http://localhost:8000

# varias URLs
VITE_BIOMETRY_API_URL=http://localhost:8000,http://192.168.18.191:8000
```

---

## Próximas mejoras de documentación (opcional)
Si quieres “documentación completa” a nivel de API, se puede ampliar con:
- Ejemplos `curl`/Postman por endpoint (`enroll`, `verify`, `identify`, etc.).
- Esquemas de request/response.
- Sección de troubleshooting (cámara, CORS, variables de entorno, MongoDB).
- Diagrama simple de arquitectura y flujo de datos (captura → extracción → persistencia → comparación).
