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

Si el backend no está en `http://localhost:8000`, define `VITE_BIOMETRY_API_URL` con la URL correcta.
