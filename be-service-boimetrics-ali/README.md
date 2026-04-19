# Facial Biometrics Backend

Servicio backend en Python para biometría facial con FastAPI.

## Qué incluye

- Enrolamiento de sujetos con una imagen.
- Verificación facial contra una identidad registrada.
- Identificación 1:N contra todas las plantillas almacenadas.
- Persistencia en MongoDB Atlas usando la base de datos `biometrics`.
- Capa de servicio desacoplada para reemplazar el motor por un modelo real más adelante.

## Stack

- Python 3.8+
- FastAPI
- Uvicorn
- Pillow
- NumPy
- PyMongo

## Instalación

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Configuración MongoDB

Define la variable de entorno `MONGODB_URI` con tu cadena de conexión Atlas. La base de datos usada por defecto es `biometrics` y la colección es `face_subjects`.

```powershell
$env:MONGODB_URI="mongodb+srv://<usuario>:<clave>@<cluster>/<params>"
$env:MONGODB_DB_NAME="biometrics"
```

## Ejecutar

```powershell
uvicorn app.main:app --reload
```

La API queda disponible en `http://127.0.0.1:8000`.

## Endpoints

- `GET /health`
- `POST /api/v1/enroll`
- `POST /api/v1/verify`
- `POST /api/v1/identify`
- `GET /api/v1/subjects`
- `GET /api/v1/subjects/{subject_id}`
- `DELETE /api/v1/subjects/{subject_id}`

## Notas

El motor actual extrae un vector normalizado y una rejilla de 64 puntos faciales sobre la imagen procesada. Eso se guarda en MongoDB y se usa para la comparación por similitud coseno. Si después quieres, puedo cambiarlo por landmarks reales con MediaPipe.
