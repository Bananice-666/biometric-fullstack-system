import { useEffect, useMemo, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import {
  biometricsApi,
  type EnrollmentResponse,
  type HealthResponse,
  type IdentificationResponse,
  type SubjectSummary,
} from './lib/biometricsApi'
import './App.css'

type ActiveSession = {
  subjectId: string
  templateId: string
  similarity: number
  checkedAt: string
}

function App() {
  const videoRef = useRef<HTMLVideoElement | null>(null)
  const cameraStreamRef = useRef<MediaStream | null>(null)

  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [subjects, setSubjects] = useState<SubjectSummary[]>([])
  const [loadingSubjects, setLoadingSubjects] = useState(false)
  const [healthLoading, setHealthLoading] = useState(true)
  const [busyAction, setBusyAction] = useState<'auth' | 'delete' | null>(null)
  const [mode, setMode] = useState<'register' | 'login'>('login')
  const [cameraStatus, setCameraStatus] = useState<'starting' | 'ready' | 'error'>('starting')
  const [cameraMessage, setCameraMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  const [registerSubjectId, setRegisterSubjectId] = useState('')
  const [registerResult, setRegisterResult] = useState<EnrollmentResponse | null>(null)

  const [loginThreshold, setLoginThreshold] = useState('0.86')
  const [loginResult, setLoginResult] = useState<IdentificationResponse | null>(null)
  const [activeSession, setActiveSession] = useState<ActiveSession | null>(null)

  const apiStatus = useMemo(() => {
    if (healthLoading) {
      return 'Conectando al backend...'
    }

    if (!health) {
      return 'Backend no disponible'
    }

    return `${health.service} · ${health.version}`
  }, [health, healthLoading])

  useEffect(() => {
    void loadInitialData()
  }, [])

  useEffect(() => {
    void startCamera()

    return () => {
      stopCamera()
    }
  }, [])

  async function loadInitialData() {
    setError(null)
    setHealthLoading(true)
    setLoadingSubjects(true)

    try {
      const [healthResponse, subjectsResponse] = await Promise.all([
        biometricsApi.health(),
        biometricsApi.listSubjects(),
      ])

      setHealth(healthResponse)
      setSubjects(subjectsResponse)
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : 'No se pudo conectar al backend')
      setHealth(null)
      setSubjects([])
    } finally {
      setHealthLoading(false)
      setLoadingSubjects(false)
    }
  }

  async function refreshSubjects() {
    setLoadingSubjects(true)

    try {
      setSubjects(await biometricsApi.listSubjects())
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : 'No se pudo cargar la lista de sujetos')
    } finally {
      setLoadingSubjects(false)
    }
  }

  async function startCamera() {
    setCameraStatus('starting')
    setCameraMessage(null)

    if (!navigator.mediaDevices?.getUserMedia) {
      setCameraStatus('error')
      setCameraMessage('Tu navegador no soporta acceso a cámara.')
      return
    }

    try {
      stopCamera()

      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: 'user',
        },
        audio: false,
      })

      cameraStreamRef.current = stream

      const video = videoRef.current
      if (!video) {
        stream.getTracks().forEach((track) => track.stop())
        throw new Error('No se pudo inicializar la vista previa de la cámara.')
      }

      video.srcObject = stream
      await video.play()
      setCameraStatus('ready')
    } catch (cameraError) {
      setCameraStatus('error')
      setCameraMessage(
        cameraError instanceof Error
          ? cameraError.message
          : 'No se pudo acceder a la cámara. Revisa permisos y vuelve a intentar.',
      )
    }
  }

  function stopCamera() {
    cameraStreamRef.current?.getTracks().forEach((track) => track.stop())
    cameraStreamRef.current = null

    const video = videoRef.current
    if (video) {
      video.srcObject = null
    }
  }

  async function captureCameraFrame() {
    const video = videoRef.current

    if (!video || cameraStatus !== 'ready') {
      throw new Error('La cámara todavía no está lista.')
    }

    if (video.videoWidth === 0 || video.videoHeight === 0) {
      throw new Error('No se detecta una imagen válida en la cámara.')
    }

    const canvas = document.createElement('canvas')
    canvas.width = video.videoWidth
    canvas.height = video.videoHeight

    const context = canvas.getContext('2d')
    if (!context) {
      throw new Error('No se pudo preparar la captura de cámara.')
    }

    context.drawImage(video, 0, 0, canvas.width, canvas.height)

    return await new Promise<Blob>((resolve, reject) => {
      canvas.toBlob(
        (blob) => {
          if (!blob) {
            reject(new Error('No se pudo convertir la captura de cámara.'))
            return
          }

          resolve(blob)
        },
        'image/jpeg',
        0.92,
      )
    })
  }

  async function handleRegister(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    if (!registerSubjectId.trim()) {
      setError('Escribe un subject_id para registrarte.')
      return
    }

    setBusyAction('auth')
    setError(null)
    setSuccess(null)

    try {
      const capture = await captureCameraFrame()
      const result = await biometricsApi.enroll(registerSubjectId.trim(), capture)
      setRegisterResult(result)
      setMode('login')
      setSuccess(`Registraste a ${result.subject_id}. Ya puedes iniciar sesión con tu rostro.`)
      await refreshSubjects()
    } catch (registerError) {
      setError(registerError instanceof Error ? registerError.message : 'Error al registrarte')
    } finally {
      setBusyAction(null)
    }
  }

  async function handleLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    const threshold = Number(loginThreshold)
    if (Number.isNaN(threshold)) {
      setError('El threshold de inicio de sesión debe ser numérico.')
      return
    }

    setBusyAction('auth')
    setError(null)
    setSuccess(null)

    try {
      const capture = await captureCameraFrame()
      const result = await biometricsApi.identify(capture, threshold)
      setLoginResult(result)

      if (!result.matched || !result.best_match) {
        setActiveSession(null)
        setError('No se reconoció tu rostro. Intenta otra vez con buena luz y mirando a la cámara.')
        return
      }

      setActiveSession({
        subjectId: result.best_match.subject_id,
        templateId: result.best_match.template_id,
        similarity: result.best_match.similarity,
        checkedAt: result.checked_at,
      })
      setSuccess(`Sesión iniciada para ${result.best_match.subject_id}.`)
    } catch (loginError) {
      setError(loginError instanceof Error ? loginError.message : 'Error al iniciar sesión')
    } finally {
      setBusyAction(null)
    }
  }

  function handleLogout() {
    setActiveSession(null)
    setLoginResult(null)
    setSuccess('Sesión cerrada.')
  }

  async function handleDelete(subjectId: string) {
    setBusyAction('delete')
    setError(null)
    setSuccess(null)

    try {
      await biometricsApi.deleteSubject(subjectId)
      setSuccess(`Se eliminó el sujeto ${subjectId}.`)
      await refreshSubjects()
    } catch (deleteError) {
      setError(deleteError instanceof Error ? deleteError.message : 'Error al eliminar el sujeto')
    } finally {
      setBusyAction(null)
    }
  }

  return (
    <main className="dashboard-shell">
      <section className="hero-panel">
        <div>
          <p className="eyebrow">Biometría facial</p>
          <h1>Iniciar sesión o registrarte con la cámara en vivo</h1>
          <p className="lede">
            Si te registras, la cámara guarda los puntos faciales en la base de datos. Si
            inicias sesión, la cámara compara tu rostro con lo almacenado y valida la sesión.
          </p>
        </div>

        <div className="status-card">
          <span className={`status-dot ${health ? 'online' : 'offline'}`} />
          <div>
            <strong>{apiStatus}</strong>
            <p>{health ? `Estado: ${health.status}` : 'Revisa que el backend esté corriendo en localhost:8000.'}</p>
          </div>
          <button className="ghost-button" onClick={() => void loadInitialData()} type="button">
            Refrescar
          </button>
        </div>
      </section>

      <section className="panel camera-panel">
        <div className="panel-heading camera-heading">
          <div>
            <p className="eyebrow">Cámara</p>
            <h2>Vista previa en vivo</h2>
          </div>
          <div className={`camera-status ${cameraStatus}`}>
            {cameraStatus === 'ready' && 'Activa'}
            {cameraStatus === 'starting' && 'Iniciando'}
            {cameraStatus === 'error' && 'Error'}
          </div>
        </div>

        <div className="camera-frame">
          <video ref={videoRef} autoPlay muted playsInline className="camera-video" />
          {cameraStatus !== 'ready' && (
            <div className="camera-overlay">
              <strong>Permite el acceso a la cámara y coloca tu rostro frente al lente.</strong>
              <p>{cameraMessage || 'La captura se tomará del video activo antes de enviar.'}</p>
            </div>
          )}
        </div>

        <div className="camera-actions">
          <button className="ghost-button" onClick={() => void startCamera()} type="button">
            {cameraStatus === 'starting' ? 'Conectando...' : 'Reiniciar cámara'}
          </button>
          <p>Se usará el frame actual de la cámara para registrarte o validar tu sesión.</p>
        </div>
      </section>

      <section className="summary-grid">
        <article className="metric-card">
          <span>Sujetos</span>
          <strong>{subjects.length}</strong>
          <p>{loadingSubjects ? 'Cargando...' : 'Lista sincronizada con /subjects'}</p>
        </article>
        <article className="metric-card">
          <span>Modo activo</span>
          <strong>{mode === 'register' ? 'Registrar' : 'Sesión'}</strong>
          <p>{mode === 'register' ? 'Guardar puntos faciales' : 'Validar rostro guardado'}</p>
        </article>
        <article className="metric-card">
          <span>Registro</span>
          <strong>{registerResult ? 'OK' : 'Pendiente'}</strong>
          <p>{registerResult ? registerResult.subject_id : 'Aún no has registrado un rostro.'}</p>
        </article>
        <article className="metric-card">
          <span>Sesión</span>
          <strong>{activeSession ? 'Activa' : 'Cerrada'}</strong>
          <p>{activeSession ? activeSession.subjectId : 'Valida tu rostro para iniciar sesión.'}</p>
        </article>
      </section>

      {(error || success) && (
        <section className="feedback-row" aria-live="polite">
          {error && <div className="feedback error">{error}</div>}
          {success && <div className="feedback success">{success}</div>}
        </section>
      )}

      <section className="panel auth-panel">
        <div className="panel-heading auth-heading">
          <div>
            <p className="eyebrow">Acceso</p>
            <h2>{mode === 'register' ? 'Registrarte' : 'Iniciar sesión'}</h2>
          </div>

          <div className="mode-switch" role="tablist" aria-label="Modo de acceso">
            <button
              aria-pressed={mode === 'register'}
              className={mode === 'register' ? 'mode-button active' : 'mode-button'}
              onClick={() => setMode('register')}
              type="button"
            >
              Registrarte
            </button>
            <button
              aria-pressed={mode === 'login'}
              className={mode === 'login' ? 'mode-button active' : 'mode-button'}
              onClick={() => setMode('login')}
              type="button"
            >
              Iniciar sesión
            </button>
          </div>
        </div>

        <form className="auth-form" onSubmit={mode === 'register' ? handleRegister : handleLogin}>
          {mode === 'register' ? (
            <>
              <label>
                Nombre o ID de registro
                <input
                  autoComplete="username"
                  onChange={(event) => setRegisterSubjectId(event.target.value)}
                  placeholder="persona-001"
                  value={registerSubjectId}
                />
              </label>

              <p className="panel-hint">
                Coloca tu rostro frente a la cámara para guardar los puntos faciales en la base de datos.
              </p>

              <button disabled={busyAction === 'auth' || cameraStatus !== 'ready'} type="submit">
                {busyAction === 'auth' ? 'Registrando...' : 'Registrarte'}
              </button>

              {registerResult && (
                <pre className="result-block">{JSON.stringify(registerResult, null, 2)}</pre>
              )}
            </>
          ) : (
            <>
              <label>
                Threshold de validación
                <input
                  inputMode="decimal"
                  onChange={(event) => setLoginThreshold(event.target.value)}
                  placeholder="0.86"
                  value={loginThreshold}
                />
              </label>

              <p className="panel-hint">
                Mira a la cámara y el sistema comparará tu rostro con lo registrado para iniciar sesión.
              </p>

              <div className="auth-actions">
                <button disabled={busyAction === 'auth' || cameraStatus !== 'ready'} type="submit">
                  {busyAction === 'auth' ? 'Validando...' : 'Iniciar sesión'}
                </button>

                <button className="ghost-button" disabled={!activeSession} onClick={handleLogout} type="button">
                  Cerrar sesión
                </button>
              </div>

              {loginResult && <pre className="result-block">{JSON.stringify(loginResult, null, 2)}</pre>}
              {activeSession && (
                <div className="session-card">
                  <strong>Sesión validada</strong>
                  <p>
                    {activeSession.subjectId} · similitud {activeSession.similarity.toFixed(3)} · template{' '}
                    {activeSession.templateId} · {new Date(activeSession.checkedAt).toLocaleString()}
                  </p>
                </div>
              )}
            </>
          )}
        </form>
      </section>

      <section className="panel subjects-panel">
        <div className="panel-heading subjects-header">
          <div>
            <p className="eyebrow">Registry</p>
            <h2>GET /api/v1/subjects</h2>
          </div>
          <button className="ghost-button" onClick={() => void refreshSubjects()} type="button">
            Actualizar lista
          </button>
        </div>

        {subjects.length === 0 ? (
          <p className="empty-state">No hay sujetos enrolados todavía.</p>
        ) : (
          <div className="subjects-list">
            {subjects.map((subject) => (
              <article key={subject.subject_id} className="subject-row">
                <div>
                  <strong>{subject.subject_id}</strong>
                  <p>{subject.samples} sample(s) · updated {new Date(subject.updated_at).toLocaleString()}</p>
                </div>
                <div className="subject-actions">
                  <span>Enrolled {new Date(subject.enrolled_at).toLocaleString()}</span>
                  <button
                    className="danger-button"
                    disabled={busyAction === 'delete'}
                    onClick={() => void handleDelete(subject.subject_id)}
                    type="button"
                  >
                    Eliminar
                  </button>
                </div>
              </article>
            ))}
          </div>
        )}
      </section>
    </main>
  )
}

export default App
