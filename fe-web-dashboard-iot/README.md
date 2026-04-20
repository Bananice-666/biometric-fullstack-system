# Biometrics Dashboard

Frontend en React + TypeScript para registrar rostros e iniciar sesión usando la cámara del navegador.

## Flujo

- `Registrarte` abre la cámara, captura un frame del rostro y envía los puntos faciales al backend para enrolarlo.
- `Iniciar sesión` abre la cámara, captura un frame y valida el rostro contra lo guardado en la base de datos.
- El panel también muestra el estado de la cámara, la sesión activa y la lista de sujetos almacenados.

## Ejecutar

```powershell
npm install
npm run dev
```

Por defecto el frontend prueba `http://localhost:8000` y `http://192.168.18.191:8000`.
Si quieres usar otras URLs, define `VITE_BIOMETRY_API_URL` con una o varias direcciones separadas por coma.
