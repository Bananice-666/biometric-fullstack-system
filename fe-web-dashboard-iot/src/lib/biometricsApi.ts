const DEFAULT_API_BASE_URLS = ['http://localhost:8000', 'http://192.168.18.191:8000']

export type HealthResponse = {
  status: string
  service: string
  version: string
}

export type EnrollmentResponse = {
  subject_id: string
  template_id: string
  similarity_baseline: number
  feature_vector_size: number
  face_points_count: number
  enrolled_at: string
  samples: number
}

export type VerificationResponse = {
  subject_id: string
  verified: boolean
  similarity: number
  threshold: number
  matched_template_id?: string | null
  checked_at: string
}

export type IdentificationMatch = {
  subject_id: string
  template_id: string
  similarity: number
}

export type IdentificationResponse = {
  matched: boolean
  threshold: number
  checked_at: string
  best_match?: IdentificationMatch | null
}

export type SubjectSummary = {
  subject_id: string
  enrolled_at: string
  samples: number
  updated_at: string
}

type ApiErrorBody = {
  detail?: string
  message?: string
}

function getApiBaseUrls() {
  const configuredUrls = import.meta.env.VITE_BIOMETRY_API_URL?.split(',').map((value:any) => value.trim()).filter(Boolean)

  return configuredUrls && configuredUrls.length > 0 ? configuredUrls : DEFAULT_API_BASE_URLS
}

async function fetchFromApi(path: string, init?: RequestInit) {
  const urls = getApiBaseUrls()
  let lastError: unknown = null

  for (const baseUrl of urls) {
    try {
      return await fetch(`${baseUrl}${path}`, init)
    } catch (error) {
      lastError = error
    }
  }

  throw lastError instanceof Error ? lastError : new Error('No se pudo conectar con ningún backend configurado.')
}

async function readErrorMessage(response: Response) {
  try {
    const payload = (await response.json()) as ApiErrorBody
    return payload.detail || payload.message || response.statusText
  } catch {
    return response.statusText || 'Unexpected API error'
  }
}

async function getJson<T>(path: string): Promise<T> {
  const response = await fetchFromApi(path)

  if (!response.ok) {
    throw new Error(await readErrorMessage(response))
  }

  return (await response.json()) as T
}

async function postFormData<T>(path: string, formData: FormData): Promise<T> {
  const response = await fetchFromApi(path, {
    method: 'POST',
    body: formData,
  })

  if (!response.ok) {
    throw new Error(await readErrorMessage(response))
  }

  return (await response.json()) as T
}

async function deleteJson<T>(path: string): Promise<T> {
  const response = await fetchFromApi(path, {
    method: 'DELETE',
  })

  if (!response.ok) {
    throw new Error(await readErrorMessage(response))
  }

  return (await response.json()) as T
}

export const biometricsApi = {
  health: () => getJson<HealthResponse>('/api/v1/health'),
  listSubjects: () => getJson<SubjectSummary[]>('/api/v1/subjects'),
  enroll: (subjectId: string, capture: Blob) => {
    const formData = new FormData()
    formData.append('subject_id', subjectId)
    formData.append('image', capture, 'camera-capture.jpg')
    return postFormData<EnrollmentResponse>('/api/v1/enroll', formData)
  },
  verify: (subjectId: string, capture: Blob, threshold: number) => {
    const formData = new FormData()
    formData.append('subject_id', subjectId)
    formData.append('image', capture, 'camera-capture.jpg')
    formData.append('threshold', String(threshold))
    return postFormData<VerificationResponse>('/api/v1/verify', formData)
  },
  identify: (capture: Blob, threshold: number) => {
    const formData = new FormData()
    formData.append('image', capture, 'camera-capture.jpg')
    formData.append('threshold', String(threshold))
    return postFormData<IdentificationResponse>('/api/v1/identify', formData)
  },
  deleteSubject: (subjectId: string) =>
    deleteJson<{ deleted: boolean }>(`/api/v1/subjects/${encodeURIComponent(subjectId)}`),
}