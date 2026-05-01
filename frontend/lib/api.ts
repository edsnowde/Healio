// ─── Healio API client ────────────────────────────────────────────────────────
// Connects to the FastAPI backend on port 8080.
// All field names match the exact JSON the backend returns.

const API_BASE = process.env.NEXT_PUBLIC_API_URL

// ─── Types that mirror the backend's actual response shapes ───────────────────

export interface TriageRequest {
  /** Raw symptom description (voice or text) — sent as "text" to /triage */
  text: string
  /** Patient name — optional, backend extracts it from text if omitted */
  name?: string
  /** Audio language: kn-IN (Kannada), hi-IN (Hindi), en-IN (English) */
  audio_language?: string
}

/** Exact shape of POST /triage response from the FastAPI backend */
export interface TriageResponse {
  success: boolean
  pipeline: string
  patient_id: string
  queue_id: string
  surveillance_id: string
  triage_color: 'Red' | 'Yellow' | 'Green'
  risk_score: number                  // 0.0 – 1.0
  chief_complaint: string
  assigned_doctor: string
  assigned_department: string
  requires_anm_confirmation: boolean
  agents_executed: Record<string, string>
  session_id: string
  timestamp: string
}

/** Shape of a document from the `patient_queue/` Firestore collection */
export interface QueuePatient {
  id: string                          // Firestore doc ID
  patient_id: string                  // Reference to patients/{patient_id}
  name: string                        // Patient name — NEW!
  chief_complaint: string
  symptoms: string[]
  triage_color: 'Red' | 'Yellow' | 'Green'
  risk_score: number                  // 0.0 – 1.0
  assigned_doctor: string
  assigned_department: string
  requires_anm_confirmation: boolean
  urgent_flag: boolean
  status: 'waiting' | 'in_consultation' | 'completed'
  timestamp: string
}

/** Shape of a document from the `detected_clusters/` Firestore collection */
export interface ClusterDoc {
  id: string
  symptoms: string[]
  patient_count: number
  confidence: number                  // 0.0 – 1.0
  severity: 'medium' | 'high'
  action_required: boolean
  status: string
  time_window_hours: number
  timestamp: string
  location?: string                   // PHC location name
  latitude?: number                   // NEW: Map coordinates
  longitude?: number                  // NEW: Map coordinates
}

/** Shape of a document from `outbreak_surveillance/` */
export interface SurveillanceDoc {
  id: string
  patient_id: string
  symptoms_anonymized: string[]
  symptom_signature: string
  severity_category: string
  triage_color: 'Red' | 'Yellow' | 'Green'
  location: string
  timestamp: string
}

// ─── API calls ────────────────────────────────────────────────────────────────

/**
 * POST /triage — runs all 3 agents, writes to Firestore, returns triage result.
 * The backend accepts `text` (symptom description) and optional `name`.
 */
export async function submitTriage(req: TriageRequest): Promise<TriageResponse> {
  console.log('📡 [API] submitTriage called with request:', req)
  const res = await fetch(`${API_BASE}/triage`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
  console.log('📡 [API] submitTriage response status:', res.status)
  if (!res.ok) {
    const err = await res.text()
    throw new Error(`Triage API error ${res.status}: ${err}`)
  }
  return res.json()
}

/**
 * GET /queue — returns all current patients in the queue (ordered by priority).
 * Used as a fallback; the dashboard primarily uses Firestore onSnapshot.
 */
export async function fetchQueue(): Promise<QueuePatient[]> {
  const res = await fetch(`${API_BASE}/queue`)
  if (!res.ok) throw new Error(`Queue API error ${res.status}`)
  return res.json()
}

/**
 * GET /surveillance/clusters — returns active detected outbreak clusters.
 */
export async function fetchClusters(): Promise<ClusterDoc[]> {
  const res = await fetch(`${API_BASE}/surveillance/clusters`)
  if (!res.ok) throw new Error(`Cluster API error ${res.status}`)
  const data = await res.json()
  // Backend returns { success, active_clusters, cluster_count, timestamp }
  return Array.isArray(data?.active_clusters) ? data.active_clusters : []
}

/**
 * PATCH /queue/patient/{id} — update patient status.
 */
export async function updatePatientStatus(
  patientId: string,
  status: 'waiting' | 'in_consultation' | 'completed'
): Promise<void> {
  await fetch(`${API_BASE}/queue/patient/${patientId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status }),
  })
}

/**
 * POST /analyze/with-multimodal — submit patient data WITH images/videos (Gemini Vision)
 */
export async function submitMultimodalTriage(data: {
  text?: string
  name?: string
  images?: File[]
  videos?: File[]
}): Promise<TriageResponse> {
  const formData = new FormData()
  
  if (data.text) formData.append('text_input', data.text)
  if (data.name) formData.append('name', data.name)
  
  console.log('📡 [API] submitMultimodalTriage FormData:')
  console.log('  text_input:', data.text)
  console.log('  name:', data.name)
  console.log('  images:', data.images?.length || 0)
  console.log('  videos:', data.videos?.length || 0)
  
  // Append images
  if (data.images && data.images.length > 0) {
    data.images.forEach((img) => {
      formData.append('images', img)
    })
  }
  
  // Append videos
  if (data.videos && data.videos.length > 0) {
    data.videos.forEach((vid) => {
      formData.append('videos', vid)
    })
  }
  
  const res = await fetch(`${API_BASE}/analyze/with-multimodal`, {
    method: 'POST',
    body: formData,
    // Don't set Content-Type header — browser will set it with multipart/form-data boundary
  })
  console.log('📡 [API] submitMultimodalTriage response status:', res.status)
  
  if (!res.ok) {
    const err = await res.text()
    throw new Error(`Multimodal API error ${res.status}: ${err}`)
  }
  
  return res.json()
}
