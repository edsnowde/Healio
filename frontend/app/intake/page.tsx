'use client'

import { useState, useRef, useEffect, useCallback } from 'react'
import Link from 'next/link'
import {
  Mic,
  Upload,
  CheckCircle2,
  Volume2,
  MicOff,
  Lock,
  RotateCcw,
  AlertCircle,
  ArrowRight,
  Building2,
  User,
} from 'lucide-react'
import { submitTriage, submitMultimodalTriage, type TriageResponse } from '@/lib/api'

// ─── Types ────────────────────────────────────────────────────────────────────

export interface PatientFormData {
  name: string
  age: number
  gender: string
  phone: string
  symptoms: string
  audioLanguage: string  // NEW: Kannada/Hindi/English for voice input
}

type FieldName = keyof PatientFormData

// Personal fields that lock after a valid voice capture
const LOCKABLE_FIELDS: FieldName[] = ['name', 'age', 'gender', 'phone']

// ─── Validation constraints ───────────────────────────────────────────────────

interface FieldConstraint {
  validate: (val: string | number) => boolean
  hint: string
}

const FIELD_CONSTRAINTS: Partial<Record<FieldName, FieldConstraint>> = {
  name: {
    validate: (v) => String(v).trim().length >= 2,
    hint: 'Name must be at least 2 characters',
  },
  age: {
    validate: (v) => {
      const n = Number(v)
      return Number.isInteger(n) && n >= 1 && n <= 99
    },
    hint: 'Age must be a 1 or 2 digit number (1–99)',
  },
  gender: {
    validate: (v) => ['Male', 'Female'].includes(String(v)),
    hint: 'Please say "male" or "female"',
  },
  phone: {
    validate: (v) => /^\d{10}$/.test(String(v).replace(/\D/g, '')),
    hint: 'Phone must be exactly 10 digits',
  },
}

// ─── Speech Abstraction Layer ─────────────────────────────────────────────────
// • Language is now DYNAMIC — uses the selected audioLanguage from form state
// • Replace createRecognition() body entirely to swap in Google Cloud Speech-to-Text.
//   The onInterim / onFinal / onEnd / onError contract stays the same — no UI changes needed.

interface RecognitionCallbacks {
  onInterim: (text: string) => void
  onFinal:   (text: string) => void
  onEnd:     ()             => void
  onError:   (err: string)  => void
}

function createRecognition(callbacks: RecognitionCallbacks, lang: string = 'en-US') {
  const SR =
    (window as any).SpeechRecognition ||
    (window as any).webkitSpeechRecognition

  if (!SR) {
    callbacks.onError('not_supported')
    return null
  }

  const rec = new SR()
  rec.lang           = lang  // ← Now uses passed language parameter!
  rec.continuous     = true
  rec.interimResults = true

  rec.onresult = (event: any) => {
    let interim = ''
    let final   = ''
    for (let i = event.resultIndex; i < event.results.length; i++) {
      const t = event.results[i][0].transcript
      if (event.results[i].isFinal) final   += t
      else                           interim += t
    }
    if (interim) callbacks.onInterim(interim)
    if (final)   callbacks.onFinal(final)
  }

  rec.onerror = (e: any) => callbacks.onError(e.error)
  rec.onend   = ()       => callbacks.onEnd()

  return rec
}

// ─── Coerce raw transcript → typed field value ────────────────────────────────

function coerceField(field: FieldName, raw: string): PatientFormData[FieldName] {
  switch (field) {
    case 'age': {
      // Strip non-digits, keep max 2 digits
      const digits = raw.replace(/\D/g, '').slice(0, 2)
      return Number(digits) || 0
    }
    case 'phone': {
      // Strip non-digits, take last 10
      return raw.replace(/\D/g, '').slice(-10)
    }
    case 'gender': {
      const t = raw.toLowerCase().trim()
      // Female checked FIRST so "female"/"femail" is never partially matched as "male"
      // Covers: "female", "femail", "fe male", "fe mail" (common STT variants)
      if (/fe[\s-]?m(ale|ail)/.test(t) || t.includes('female') || t.includes('femail')) return 'Female'
      // Male covers: "male", "mail" (very common STT mishearing)
      if (t.includes('male') || t.includes('mail')) return 'Male'
      return ''   // empty -> fails validation -> not locked
    }
    default:
      return raw.trim()
  }
}

// ─── Component ────────────────────────────────────────────────────────────────

export default function PatientForm() {

  const [formData, setFormData] = useState<PatientFormData>({
    name: '', age: 0, gender: '', phone: '', symptoms: '', audioLanguage: 'kn-IN',
  })

  // Triage result from the backend after successful submission
  const [triageResult, setTriageResult] = useState<TriageResponse | null>(null)

  // Fields locked after successful voice capture
  const [lockedFields,      setLockedFields]      = useState<Set<FieldName>>(new Set())
  // Per-field constraint errors shown after a failed attempt
  const [fieldErrors,       setFieldErrors]       = useState<Partial<Record<FieldName, string>>>({})

  const [activeField,       setActiveField]       = useState<FieldName | null>(null)
  const [interimText,       setInterimText]       = useState('')
  const [speechSupported,   setSpeechSupported]   = useState(true)
  const [isLoading,         setIsLoading]         = useState(false)
  const [formError,         setFormError]         = useState('')
  const [extractedSymptoms, setExtractedSymptoms] = useState<string[]>([])
  const [showExtracted,     setShowExtracted]     = useState(false)
  const [waveformBars,      setWaveformBars]      = useState(Array(20).fill(0.3))
  const [uploadedImages,    setUploadedImages]    = useState<File[]>([])
  const [uploadingImages,   setUploadingImages]   = useState(false)
  const [uploadedVideos,    setUploadedVideos]    = useState<File[]>([])

  const recognitionRef = useRef<any>(null)
  const silenceTimer   = useRef<ReturnType<typeof setTimeout> | null>(null)
  const animationRef   = useRef<number | null>(null)
  const accFinalRef    = useRef('')   // accumulates final transcript chunks within one session
  const cameraInputRef = useRef<HTMLInputElement>(null)  // for camera capture on mobile
  const galleryInputRef = useRef<HTMLInputElement>(null) // for gallery/file selection
  const videoInputRef = useRef<HTMLInputElement>(null)   // for video upload

  // ── Check browser support on mount ──────────────────────────────────────────
  useEffect(() => {
    const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
    if (!SR) setSpeechSupported(false)
  }, [])

  // ── Waveform animation while a field is being recorded ──────────────────────
  useEffect(() => {
    if (activeField) {
      const animate = () => {
        setWaveformBars(prev => prev.map(() => Math.random() * 0.9 + 0.1))
        animationRef.current = requestAnimationFrame(animate)
      }
      animationRef.current = requestAnimationFrame(animate)
    } else {
      if (animationRef.current) cancelAnimationFrame(animationRef.current)
      setWaveformBars(Array(20).fill(0.3))
    }
    return () => { if (animationRef.current) cancelAnimationFrame(animationRef.current) }
  }, [activeField])

  // ── Unlock a locked field so the user can re-record ─────────────────────────
  const unlockField = (field: FieldName) => {
    setLockedFields(prev => { const s = new Set(prev); s.delete(field); return s })
    setFormData(prev => ({ ...prev, [field]: field === 'age' ? 0 : '' }))
    setFieldErrors(prev => ({ ...prev, [field]: undefined }))
  }

  // ── startVoiceInput — the single voice bridge for every field ────────────────

  const startVoiceInput = useCallback((field: FieldName) => {
    // Stop any running session
    if (recognitionRef.current) { recognitionRef.current.stop(); recognitionRef.current = null }
    if (silenceTimer.current)   { clearTimeout(silenceTimer.current); silenceTimer.current = null }

    accFinalRef.current = ''
    setInterimText('')
    setActiveField(field)
    setFieldErrors(prev => ({ ...prev, [field]: undefined }))

    const resetSilenceTimer = (rec: any) => {
      if (silenceTimer.current) clearTimeout(silenceTimer.current)
      // 2.5 s pause → auto-stop
      silenceTimer.current = setTimeout(() => rec.stop(), 2500)
    }

    const rec = createRecognition({
      onInterim: (text) => {
        setInterimText(text)
        resetSilenceTimer(rec!)
      },
      onFinal: (text) => {
        accFinalRef.current += (accFinalRef.current ? ' ' : '') + text
        const coerced = coerceField(field, accFinalRef.current)
        setFormData(prev => ({ ...prev, [field]: coerced }))
        setInterimText('')
        resetSilenceTimer(rec!)
      },
      onEnd: () => {
        setActiveField(null)
        setInterimText('')
        if (silenceTimer.current) clearTimeout(silenceTimer.current)

        const final   = accFinalRef.current
        const coerced = coerceField(field, final)

        // ── Lockable personal fields: validate before locking ────────────────
        if (LOCKABLE_FIELDS.includes(field)) {
          const constraint = FIELD_CONSTRAINTS[field]
          if (constraint && !constraint.validate(coerced)) {
            // Bad input — show hint, clear field, let user try again
            setFieldErrors(prev => ({ ...prev, [field]: constraint.hint }))
            setFormData(prev => ({ ...prev, [field]: field === 'age' ? 0 : '' }))
            return
          }
          // Valid → commit and lock
          setFormData(prev => {
            const updated = { ...prev, [field]: coerced }
            sessionStorage.setItem('patientFormData', JSON.stringify(updated))
            return updated
          })
          setLockedFields(prev => new Set([...prev, field]))
          return
        }

        // ── Symptoms field: extract keyword tags ─────────────────────────────
        if (field === 'symptoms' && final) {
          const keywords = final
            .split(/[\s,]+/)
            .filter(w => w.length > 3)
            .slice(0, 5)
          setExtractedSymptoms(keywords)
          setShowExtracted(true)
        }

        setFormData(prev => {
          const updated = { ...prev, [field]: coerced }
          sessionStorage.setItem('patientFormData', JSON.stringify(updated))
          return updated
        })
      },
      onError: (err) => {
        if (err === 'not_supported') setSpeechSupported(false)
        setActiveField(null)
        setInterimText('')
      },
    }, formData.audioLanguage)  // ← PASS SELECTED LANGUAGE HERE!

    if (!rec) return
    recognitionRef.current = rec
    rec.start()
  }, [formData.audioLanguage])  // ← ADD LANGUAGE TO DEPENDENCY ARRAY

  // ── Manual text / select change (non-locked fields only) ────────────────────

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target
    if (lockedFields.has(name as FieldName)) return
    setFormData(prev => ({
      ...prev,
      [name]: name === 'age' ? (value === '' ? 0 : Number(value)) : value,
    }))
  }

  // ── Form validation & submit ─────────────────────────────────────────────────

  const validateForm = () => {
    if (!formData.name.trim())     { setFormError('Patient name is required'); return false }
    if (!formData.symptoms.trim()) { setFormError('Symptoms are required');    return false }
    return true
  }

  // ── Image upload handler ───────────────────────────────────────────────────

  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || [])
    if (files.length > 0) {
      setUploadedImages(prev => [...prev, ...files])
    }
  }

  // ── Remove image from upload list ──────────────────────────────────────────

  const removeImage = (index: number) => {
    setUploadedImages(prev => prev.filter((_, i) => i !== index))
  }

  // ── Handle video upload ────────────────────────────────────────────────
  const handleVideoUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || [])
    if (files.length > 0) {
      setUploadedVideos(prev => [...prev, ...files])
    }
  }

  // ── Remove video from upload list ──────────────────────────────────────
  const removeVideo = (index: number) => {
    setUploadedVideos(prev => prev.filter((_, i) => i !== index))
  }

  // ── Unified Submit Handler (intelligently routes text-only or multimodal) ────────────────────

  const handleSubmitForTriage = async (e: React.FormEvent) => {
    e.preventDefault()
    setFormError('')
    setTriageResult(null)

    // Validate required fields
    if (!validateForm()) return

    const hasMedia = uploadedImages.length > 0 || uploadedVideos.length > 0

    // Build the text payload
    const text = [
      formData.symptoms,
      formData.name ? `my name is ${formData.name}` : '',
      formData.age  ? `I am ${formData.age} years old` : '',
      formData.gender ? `gender ${formData.gender}` : '',
    ].filter(Boolean).join('. ')

    // DEBUG: Log what's being sent
    console.log('🔍 DEBUG - Submitting form with:')
    console.log('  formData.name:', formData.name)
    console.log('  formData.symptoms:', formData.symptoms)
    console.log('  formData.age:', formData.age)
    console.log('  formData.gender:', formData.gender)
    console.log('  text:', text)
    console.log('  hasMedia:', hasMedia)

    if (hasMedia) {
      // ── Route to Multimodal endpoint (images/videos with text) ──────────────
      setUploadingImages(true)
      try {
        console.log('📤 Sending to /analyze/with-multimodal with:')
        console.log('  text:', text)
        console.log('  name:', formData.name)
        console.log('  images:', uploadedImages.length)
        console.log('  videos:', uploadedVideos.length)
        const result = await submitMultimodalTriage({
          text,
          name: formData.name || undefined,
          images: uploadedImages,
          videos: uploadedVideos.length > 0 ? uploadedVideos : undefined,
        })
        setTriageResult(result as unknown as TriageResponse)
        setUploadedImages([])
        setUploadedVideos([])
        setTimeout(() => {
          document.getElementById('triage-result-card')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
        }, 100)
      } catch (err: any) {
        setFormError(err?.message || 'Media submission failed. Check backend logs.')
      } finally {
        setUploadingImages(false)
      }
    } else {
      // ── Route to Text-only endpoint (no images/videos) ─────────────────────
      setIsLoading(true)
      try {
        console.log('📤 Sending to /triage with:')
        console.log('  text:', text)
        console.log('  name:', formData.name)
        console.log('  audio_language:', formData.audioLanguage)
        const result = await submitTriage({ 
          text, 
          name: formData.name || undefined,
          audio_language: formData.audioLanguage
        })
        setTriageResult(result)
        setTimeout(() => {
          document.getElementById('triage-result-card')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
        }, 100)
      } catch (err: any) {
        setFormError(err?.message || 'Submission failed. Is the backend running on port 8080?')
      } finally {
        setIsLoading(false)
      }
    }
  }

  // ─── Reusable sub-components ─────────────────────────────────────────────────

  /** Mic button — absolutely positioned inside a relative wrapper */
  const VoiceFieldMic = ({ field }: { field: FieldName }) => {
    if (!speechSupported) return (
      <span title="Speech not supported in this browser"
        className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-300 cursor-not-allowed">
        <MicOff size={17} />
      </span>
    )
    const isActive = activeField === field
    return (
      <button
        type="button"
        aria-label={`Voice input for ${field}`}
        onClick={() => isActive ? recognitionRef.current?.stop() : startVoiceInput(field)}
        className="
          absolute right-3 top-1/2 -translate-y-1/2
          w-8 h-8 rounded-full flex items-center justify-center
          transition-all duration-200 hover:scale-110
          focus:outline-none focus:ring-2 focus:ring-emerald-400
        "
        style={{
          background: isActive
            ? 'linear-gradient(135deg,#059669,#10b981)'
            : 'rgba(209,250,229,0.8)',
          boxShadow: isActive ? '0 0 0 4px rgba(16,185,129,0.25)' : 'none',
        }}
      >
        <Mic size={14} className={isActive ? 'text-white animate-pulse' : 'text-emerald-600'} />
      </button>
    )
  }

  /** Live interim transcript below the active field */
  const InterimBadge = ({ field }: { field: FieldName }) =>
    activeField === field && interimText ? (
      <p className="mt-1 text-xs text-emerald-600 italic truncate pl-1">🎙 {interimText}</p>
    ) : null

  /** Validation error below a field */
  const FieldError = ({ field }: { field: FieldName }) =>
    fieldErrors[field] ? (
      <p className="mt-1 text-xs text-red-500 flex items-center gap-1 pl-1">
        <AlertCircle size={12} />{fieldErrors[field]}
      </p>
    ) : null

  /** Read-only locked display with a Re-record button */
  const LockedField = ({
    field, label, value,
  }: { field: FieldName; label: string; value: string | number }) => (
    <div className="
      flex items-center justify-between
      border-2 border-emerald-400 bg-emerald-50/60
      rounded-xl px-4 py-3 gap-2 shadow-sm
    ">
      <div className="flex items-center gap-2 min-w-0">
        <Lock size={13} className="text-emerald-600 shrink-0" />
        <span className="text-xs font-semibold text-emerald-600 shrink-0 uppercase tracking-wide">
          {label}
        </span>
        <span className="font-bold text-gray-900 truncate">{String(value)}</span>
      </div>
      <div className="flex items-center gap-2 shrink-0">
        <CheckCircle2 size={16} className="text-emerald-500" />
        <button
          type="button"
          title={`Re-record ${label}`}
          onClick={() => unlockField(field)}
          className="
            flex items-center gap-1
            text-xs text-red-500 hover:text-red-700
            bg-red-50 hover:bg-red-100
            border border-red-200 hover:border-red-300
            rounded-full px-2.5 py-1
            transition font-semibold
          "
        >
          <RotateCcw size={11} />Re-record
        </button>
      </div>
    </div>
  )

  /** Graceful fallback banner when browser doesn't support speech */
  const UnsupportedBanner = () =>
    !speechSupported ? (
      <div className="bg-amber-50 border border-amber-200 text-amber-700 p-3 rounded-xl text-sm flex items-center gap-2">
        <MicOff size={16} />
        Voice input is not supported in this browser. Please use Chrome or Edge, or type your answers manually below.
      </div>
    ) : null

  // ─── Render ───────────────────────────────────────────────────────────────────

  return (
    <div className="min-h-screen relative overflow-hidden">

      {/* Diagonal split background */}
      <div className="absolute inset-0"
        style={{ background: 'linear-gradient(135deg,#ddb9ec 50%, #ffffff 50%)' }} />
      <div className="absolute top-20 left-20 w-72 h-72 bg-emerald-200/40 rounded-full blur-3xl" />
      <div className="absolute bottom-10 right-10 w-96 h-96 bg-green-100/50 rounded-full blur-3xl" />

      <div className="relative z-10 max-w-6xl mx-auto px-6 py-16">
        <div className="grid lg:grid-cols-2 gap-14 items-center">

          {/* ── Left Hero ─────────────────────────────────────────────────────── */}
          <div>
            <p className="uppercase tracking-[4px] text-emerald-700 font-semibold mb-4">
              AI TRIAGE SYSTEM
            </p>
            <h1 className="text-5xl font-bold leading-tight mb-6 text-gray-900">
              Smart Patient Intake <br />
              for Modern Primary Care
            </h1>
            <p className="text-lg text-gray-600 mb-8 leading-relaxed">
              Multimodal symptom intake, intelligent risk prioritization
              and real-time patient routing powered by Healio.
            </p>
            <div className="grid grid-cols-2 gap-5">
              <div className="bg-white/70 backdrop-blur-xl rounded-2xl p-6 shadow-lg">
                <h3 className="font-bold text-emerald-700 text-2xl">3 Agents</h3>
                <p className="text-sm text-gray-600">Autonomous Triage Pipeline</p>
              </div>
              <div className="bg-white/70 backdrop-blur-xl rounded-2xl p-6 shadow-lg">
                <h3 className="font-bold text-emerald-700 text-2xl">Real-Time</h3>
                <p className="text-sm text-gray-600">Priority Queue Routing</p>
              </div>
            </div>
          </div>

          {/* ── Form Card ─────────────────────────────────────────────────────── */}
          <div>
            <form
              onSubmit={handleSubmitForTriage}
              className="
                bg-white/85 backdrop-blur-2xl rounded-[30px]
                shadow-2xl p-10 space-y-8 border border-white/60
              "
            >
              <h2 className="text-3xl font-bold text-gray-900">Patient Intake</h2>

              <UnsupportedBanner />

              {formError && (
                <div className="bg-red-50 border border-red-200 text-red-600 p-4 rounded-xl flex items-center gap-2 text-sm">
                  <AlertCircle size={16} className="shrink-0" />{formError}
                </div>
              )}

              {/* ── Personal Details ──────────────────────────────────────────── */}
              <div className="space-y-3">
                <div className="flex items-center gap-2 mb-1">
                  <p className="text-xs font-bold text-gray-400 uppercase tracking-widest">
                    Personal Details
                  </p>
                  <span className="text-xs text-emerald-600 font-medium">
                    — fields lock after voice capture
                  </span>
                </div>

                {/* Full Name */}
                <div>
                  {lockedFields.has('name') ? (
                    <LockedField field="name" label="Name" value={formData.name} />
                  ) : (
                    <div className="relative">
                      <input
                        name="name"
                        value={formData.name}
                        onChange={handleChange}
                        placeholder="Full Name — say your name"
                        className="w-full border rounded-xl p-4 pr-12 focus:outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-200 transition"
                      />
                      <VoiceFieldMic field="name" />
                    </div>
                  )}
                  <InterimBadge field="name" />
                  <FieldError    field="name" />
                </div>

                {/* Age */}
                <div>
                  {lockedFields.has('age') ? (
                    <LockedField field="age" label="Age" value={formData.age} />
                  ) : (
                    <div className="relative">
                      <input
                        type="number"
                        name="age"
                        min={1} max={99}
                        value={formData.age || ''}
                        onChange={handleChange}
                        placeholder="Age — say a 1 or 2 digit number (1–99)"
                        className="w-full border rounded-xl p-4 pr-12 focus:outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-200 transition"
                      />
                      <VoiceFieldMic field="age" />
                    </div>
                  )}
                  <InterimBadge field="age" />
                  <FieldError    field="age" />
                </div>

                {/* Gender */}
                <div>
                  {lockedFields.has('gender') ? (
                    <LockedField field="gender" label="Gender" value={formData.gender} />
                  ) : (
                    <div className="relative">
                      <select
                        name="gender"
                        value={formData.gender}
                        onChange={handleChange}
                        className="w-full border rounded-xl p-4 pr-12 appearance-none focus:outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-200 transition bg-white"
                      >
                        <option value="">Select Gender — or say "male" / "female"</option>
                        <option>Male</option>
                        <option>Female</option>
                      </select>
                      <VoiceFieldMic field="gender" />
                    </div>
                  )}
                  <InterimBadge field="gender" />
                  <FieldError    field="gender" />
                </div>

                {/* Phone */}
                <div>
                  {lockedFields.has('phone') ? (
                    <LockedField field="phone" label="Phone" value={formData.phone} />
                  ) : (
                    <div className="relative">
                      <input
                        name="phone"
                        value={formData.phone}
                        onChange={handleChange}
                        placeholder="10-digit phone — say all ten digits"
                        maxLength={10}
                        className="w-full border rounded-xl p-4 pr-12 focus:outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-200 transition"
                      />
                      <VoiceFieldMic field="phone" />
                    </div>
                  )}
                  <InterimBadge field="phone" />
                  <FieldError    field="phone" />
                </div>
              </div>

              {/* ── Primary Voice Symptom Intake ──────────────────────────────── */}
              <div className="
                bg-gradient-to-br from-emerald-50/80 to-green-50/80
                backdrop-blur-2xl rounded-3xl
                border-2 border-emerald-200/60
                p-8 shadow-xl relative overflow-hidden
              ">
                <div className="absolute top-4 right-4 flex items-center gap-2 bg-emerald-600 text-white px-4 py-1.5 rounded-full text-xs font-semibold">
                  <Volume2 size={14} />
                  Primary Intake
                </div>

                {/* Language selector - NEW! */}
                <div className="mb-6 pb-6 border-b border-emerald-200">
                  <h4 className="text-sm font-bold text-gray-700 mb-3">Voice Language</h4>
                  <div className="flex gap-2 flex-wrap">
                    {[
                      { code: 'kn-IN', label: '🇮🇳 Kannada', flag: '🔤' },
                      { code: 'hi-IN', label: '🇮🇳 Hindi', flag: '🔤' },
                      { code: 'en-IN', label: '🇮🇳 English', flag: '🔤' }
                    ].map(({ code, label }) => (
                      <button
                        key={code}
                        type="button"
                        onClick={() => setFormData(prev => ({ ...prev, audioLanguage: code }))}
                        className={`
                          px-4 py-2 rounded-lg font-semibold text-sm transition
                          border-2
                          ${formData.audioLanguage === code
                            ? 'bg-emerald-600 text-white border-emerald-600'
                            : 'bg-white text-gray-700 border-gray-300 hover:border-emerald-300'
                          }
                        `}
                      >
                        {label}
                      </button>
                    ))}
                  </div>
                  <p className="text-xs text-gray-500 mt-2">Select language before recording voice input</p>
                </div>

                <div className="mb-6">
                  <h3 className="text-2xl font-bold text-gray-900 mb-2">
                    Primary Symptom Intake (Voice)
                  </h3>
                  <p className="text-emerald-700 font-medium">
                    Speak your symptoms naturally
                  </p>
                </div>

                {/* Waveform while symptoms recording */}
                {activeField === 'symptoms' && (
                  <div className="mb-8 p-6 bg-white/70 rounded-2xl">
                    <div className="flex items-end justify-center gap-1 h-16">
                      {waveformBars.map((height, idx) => (
                        <div
                          key={idx}
                          className="w-1.5 bg-gradient-to-t from-emerald-500 to-green-400 rounded-full transition-all duration-75"
                          style={{ height: `${Math.max(height * 60, 8)}px`, opacity: 0.7 + height * 0.3 }}
                        />
                      ))}
                    </div>
                    <p className="text-center mt-4 text-emerald-700 font-semibold animate-pulse">
                      Listening…
                    </p>
                    {interimText && (
                      <p className="text-center mt-2 text-sm text-emerald-600 italic">
                        "{interimText}"
                      </p>
                    )}
                  </div>
                )}

                {/* Big record button */}
                <div className="mb-8">
                  <button
                    type="button"
                    onClick={() =>
                      activeField === 'symptoms'
                        ? recognitionRef.current?.stop()
                        : startVoiceInput('symptoms')
                    }
                    disabled={!speechSupported}
                    className="
                      w-full py-6 px-8
                      bg-gradient-to-r from-emerald-600 to-green-600
                      hover:from-emerald-700 hover:to-green-700
                      disabled:from-gray-400 disabled:to-gray-400
                      text-white font-bold text-lg rounded-2xl
                      transition shadow-lg
                      flex items-center justify-center gap-3 group
                    "
                  >
                    <Mic size={24} className={activeField === 'symptoms' ? 'animate-pulse' : 'group-hover:scale-110 transition'} />
                    {activeField === 'symptoms' ? 'Listening… (tap to stop)' : 'Start Recording'}
                  </button>
                </div>

                {/* Status chips */}
                <div className="flex flex-wrap gap-3">
                  {[
                    { icon: <CheckCircle2 size={16} />, label: 'Speech to Text'    },
                    { icon: <Mic          size={16} />, label: 'Voice-first Fields' },
                    { icon: <CheckCircle2 size={16} />, label: 'AI Symptom Parsing' },
                  ].map(({ icon, label }) => (
                    <div key={label} className="
                      inline-flex items-center gap-2
                      bg-white/80 border border-emerald-200
                      rounded-full px-4 py-2
                      text-sm font-semibold text-emerald-700
                    ">{icon}{label}</div>
                  ))}
                </div>
              </div>

              {/* ── Extracted Symptoms Preview ────────────────────────────────── */}
              {showExtracted && extractedSymptoms.length > 0 && (
                <div className="
                  bg-gradient-to-r from-green-50 to-emerald-50
                  border-l-4 border-emerald-600
                  rounded-xl p-6 shadow-md
                ">
                  <h4 className="font-bold text-emerald-900 mb-3 flex items-center gap-2">
                    <CheckCircle2 size={20} className="text-emerald-600" />
                    Extracted Symptoms
                  </h4>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                    {extractedSymptoms.map((symptom, idx) => (
                      <div key={idx} className="
                        bg-white border border-emerald-200 rounded-lg
                        px-3 py-2 text-sm font-semibold text-emerald-700
                        flex items-center gap-2
                      ">
                        <CheckCircle2 size={14} />{symptom}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* ── Agentic Flow Steps ────────────────────────────────────────── */}
              <div className="grid md:grid-cols-3 gap-4">
                {[
                  { n: 1, title: 'Voice Intake',   sub: 'Symptom Collection'  },
                  { n: 2, title: 'AI Extraction',  sub: 'Symptom Analysis'    },
                  { n: 3, title: 'Triage Routing', sub: 'Priority Assignment'  },
                ].map(({ n, title, sub }) => (
                  <div key={n} className="
                    bg-gradient-to-br from-emerald-100/60 to-green-100/60
                    border border-emerald-200/80 rounded-xl p-4 text-center
                  ">
                    <div className="inline-flex items-center justify-center w-10 h-10 rounded-full bg-emerald-600 text-white font-bold mb-3">{n}</div>
                    <h4 className="font-bold text-gray-900 text-sm">{title}</h4>
                    <p className="text-xs text-gray-600 mt-1">{sub}</p>
                  </div>
                ))}
              </div>

              {/* ── Alternative Input Methods ─────────────────────────────────── */}
              <div>
                <h3 className="text-lg font-bold text-gray-900 mb-4">
                  Alternative Input Methods
                </h3>
                <div className="grid md:grid-cols-2 gap-5">

                  {/* Upload — FIXED: Now with separate camera & gallery options */}
                  <div className="space-y-4">
                    {/* Camera input (hidden) */}
                    <input
                      ref={cameraInputRef}
                      type="file"
                      accept="image/*"
                      capture="environment"
                      onChange={handleImageUpload}
                      className="hidden"
                      aria-label="Take photo with camera"
                    />
                    
                    {/* Gallery input (hidden) */}
                    <input
                      ref={galleryInputRef}
                      type="file"
                      multiple
                      accept="image/*"
                      onChange={handleImageUpload}
                      className="hidden"
                      aria-label="Upload images from gallery"
                    />

                    {/* Camera button */}
                    <button
                      type="button"
                      onClick={() => cameraInputRef.current?.click()}
                      className="
                        w-full border-2 border-dashed border-blue-300 rounded-2xl
                        p-6 text-center
                        hover:border-blue-500 hover:bg-blue-50/30
                        transition bg-white/60 backdrop-blur-sm
                        cursor-pointer
                      "
                    >
                      <p className="text-3xl mb-2">📷</p>
                      <p className="font-bold text-gray-900">Take Photo with Camera</p>
                      <p className="text-xs text-gray-500 mt-1">Capture medical images in real-time</p>
                    </button>

                    {/* Gallery button */}
                    <button
                      type="button"
                      onClick={() => galleryInputRef.current?.click()}
                      className="
                        w-full border-2 border-dashed border-emerald-300 rounded-2xl
                        p-6 text-center
                        hover:border-emerald-500 hover:bg-emerald-50/30
                        transition bg-white/60 backdrop-blur-sm
                        cursor-pointer
                      "
                    >
                      <p className="text-3xl mb-2">🖼️</p>
                      <p className="font-bold text-gray-900">Upload from Gallery</p>
                      <p className="text-xs text-gray-500 mt-1">Select existing images</p>
                    </button>

                    {/* Video input (hidden) - NEW! */}
                    <input
                      ref={videoInputRef}
                      type="file"
                      multiple
                      accept="video/*"
                      onChange={handleVideoUpload}
                      className="hidden"
                      aria-label="Upload clinical videos"
                    />

                    {/* Video upload button - NEW! */}
                    <button
                      type="button"
                      onClick={() => videoInputRef.current?.click()}
                      className="
                        w-full border-2 border-dashed border-red-300 rounded-2xl
                        p-6 text-center
                        hover:border-red-500 hover:bg-red-50/30
                        transition bg-white/60 backdrop-blur-sm
                        cursor-pointer
                      "
                    >
                      <p className="text-3xl mb-2">🎥</p>
                      <p className="font-bold text-gray-900">Upload Clinical Videos</p>
                      <p className="text-xs text-gray-500 mt-1">Add video evidence of symptoms</p>
                    </button>

                    {/* Show uploaded image previews */}
                    {uploadedImages.length > 0 && (
                      <div className="mt-4 space-y-3">
                        <p className="text-sm font-semibold text-emerald-700">
                          📸 {uploadedImages.length} image(s) selected:
                        </p>
                        <div className="grid grid-cols-2 gap-3">
                          {uploadedImages.map((file, idx) => (
                            <div
                              key={idx}
                              className="
                                relative bg-white border border-emerald-200 rounded-lg p-2
                                text-xs text-gray-700 font-semibold truncate
                                flex items-center justify-between gap-2
                              "
                            >
                              <span className="truncate">{file.name}</span>
                              <button
                                type="button"
                                onClick={() => removeImage(idx)}
                                className="text-red-500 hover:text-red-700 shrink-0"
                              >
                                ✕
                              </button>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Show uploaded video previews - NEW! */}
                    {uploadedVideos.length > 0 && (
                      <div className="mt-4 space-y-3">
                        <p className="text-sm font-semibold text-red-700">
                          🎥 {uploadedVideos.length} video(s) selected:
                        </p>
                        <div className="grid grid-cols-2 gap-3">
                          {uploadedVideos.map((file, idx) => (
                            <div
                              key={idx}
                              className="
                                relative bg-white border border-red-200 rounded-lg p-2
                                text-xs text-gray-700 font-semibold truncate
                                flex items-center justify-between gap-2
                              "
                            >
                              <span className="truncate">{file.name}</span>
                              <button
                                type="button"
                                onClick={() => removeVideo(idx)}
                                className="text-red-500 hover:text-red-700 shrink-0"
                              >
                                ✕
                              </button>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Text backup — auto-filled by symptom voice */}
                  <div className="
                    border-2 border-dashed border-gray-300 rounded-2xl
                    p-6 text-center
                    hover:border-gray-400 hover:bg-gray-50/30
                    transition bg-white/60 backdrop-blur-sm
                  ">
                    <p className="text-sm font-semibold text-gray-600 mb-3">
                      Backup Text Symptom Entry
                    </p>
                    <div className="relative">
                      <textarea
                        name="symptoms"
                        value={formData.symptoms}
                        onChange={handleChange}
                        rows={4}
                        placeholder="Or describe symptoms in text…"
                        className="
                          w-full border rounded-xl p-3 pr-10 text-sm
                          bg-white/80 focus:outline-none
                          focus:border-emerald-500 focus:ring-2 focus:ring-emerald-200
                          transition resize-none
                        "
                      />
                      {/* Mic on textarea corner */}
                      <button
                        type="button"
                        aria-label="Voice input for symptoms"
                        onClick={() =>
                          activeField === 'symptoms'
                            ? recognitionRef.current?.stop()
                            : startVoiceInput('symptoms')
                        }
                        disabled={!speechSupported}
                        className="absolute right-3 top-3 w-8 h-8 rounded-full flex items-center justify-center transition-all hover:scale-110"
                        style={{
                          background: activeField === 'symptoms'
                            ? 'linear-gradient(135deg,#059669,#10b981)'
                            : 'rgba(209,250,229,0.8)',
                          boxShadow: activeField === 'symptoms'
                            ? '0 0 0 4px rgba(16,185,129,0.25)' : 'none',
                        }}
                      >
                        <Mic size={14} className={activeField === 'symptoms' ? 'text-white animate-pulse' : 'text-emerald-600'} />
                      </button>
                    </div>
                  </div>
                </div>
              </div>

              {/* ── Submit ───────────────────────────────────────────────────── */}
              <button
                type="submit"
                disabled={isLoading || uploadingImages}
                className="
                  w-full py-4 rounded-2xl
                  bg-emerald-600 hover:bg-emerald-700
                  text-white font-bold text-lg shadow-lg
                  transition disabled:opacity-60
                "
              >
                {isLoading || uploadingImages 
                  ? (uploadedImages.length > 0 || uploadedVideos.length > 0
                      ? '🔄 Analyzing with Gemini Vision…'
                      : '🤖 Agents Evaluating…')
                  : 'Submit For Triage'}
              </button>

              <p className="text-center text-xs text-gray-500">
                Encrypted &amp; PHC compliant intake workflow
              </p>

            </form>

            {/* ── Triage Result Card (appears below form after submission) ── */}
            {triageResult && (
              <div
                id="triage-result-card"
                className={`mt-8 rounded-3xl border-2 p-8 shadow-2xl ${
                  triageResult.triage_color === 'Red'
                    ? 'bg-red-50 border-red-400'
                    : triageResult.triage_color === 'Yellow'
                    ? 'bg-yellow-50 border-yellow-400'
                    : 'bg-green-50 border-green-400'
                }`}
              >
                {/* Priority banner */}
                <div className="flex items-center gap-3 mb-6">
                  <span className="text-5xl">
                    {triageResult.triage_color === 'Red'    ? '🔴' :
                     triageResult.triage_color === 'Yellow' ? '🟡' : '🟢'}
                  </span>
                  <div>
                    <p className="text-xs font-bold uppercase tracking-widest text-gray-500">Triage Priority</p>
                    <h3 className={`text-3xl font-black ${
                      triageResult.triage_color === 'Red'    ? 'text-red-700' :
                      triageResult.triage_color === 'Yellow' ? 'text-yellow-700' : 'text-green-700'
                    }`}>{triageResult.triage_color.toUpperCase()}</h3>
                  </div>
                  <div className="ml-auto text-right">
                    <p className="text-xs text-gray-500 font-semibold">Risk Score</p>
                    <p className={`text-4xl font-black ${
                      triageResult.triage_color === 'Red'    ? 'text-red-600' :
                      triageResult.triage_color === 'Yellow' ? 'text-yellow-600' : 'text-green-600'
                    }`}>{Math.round(triageResult.risk_score * 100)}%</p>
                  </div>
                </div>

                {/* Chief complaint */}
                <div className="mb-4 bg-white/70 rounded-2xl p-4">
                  <p className="text-xs font-bold text-gray-500 uppercase mb-1">Chief Complaint</p>
                  <p className="font-semibold text-gray-900">{triageResult.chief_complaint}</p>
                </div>

                {/* Doctor + Department */}
                <div className="grid grid-cols-2 gap-3 mb-4">
                  <div className="bg-white/70 rounded-2xl p-4">
                    <p className="text-xs font-bold text-gray-500 uppercase mb-1 flex items-center gap-1">
                      <User size={12} /> Doctor
                    </p>
                    <p className="font-bold text-gray-900">{triageResult.assigned_doctor}</p>
                  </div>
                  <div className="bg-white/70 rounded-2xl p-4">
                    <p className="text-xs font-bold text-gray-500 uppercase mb-1 flex items-center gap-1">
                      <Building2 size={12} /> Department
                    </p>
                    <p className="font-bold text-gray-900">{triageResult.assigned_department}</p>
                  </div>
                </div>

                {/* ANM confirmation banner */}
                {triageResult.requires_anm_confirmation && (
                  <div className="mb-4 bg-red-100 border border-red-300 rounded-2xl p-4 flex items-start gap-3">
                    <AlertCircle size={20} className="text-red-600 flex-shrink-0 mt-0.5" />
                    <div>
                      <p className="font-bold text-red-800">ANM Confirmation Required</p>
                      <p className="text-sm text-red-700 mt-0.5">
                        High-priority patient — ANM must confirm before the doctor alert fires.
                      </p>
                    </div>
                  </div>
                )}

                {/* IDs */}
                <div className="bg-white/50 rounded-xl p-3 mb-6 font-mono text-xs text-gray-500 space-y-1">
                  <p><span className="font-bold">Patient ID:</span> {triageResult.patient_id}</p>
                  <p><span className="font-bold">Queue ID:</span>   {triageResult.queue_id}</p>
                  <p><span className="font-bold">Session:</span>    {triageResult.session_id}</p>
                </div>

                {/* Navigation */}
                <div className="flex gap-3">
                  <Link
                    href="/dashboard"
                    className="flex-1 flex items-center justify-center gap-2 py-3 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-2xl transition"
                  >
                    Go to Dashboard <ArrowRight size={16} />
                  </Link>
                  <button
                    type="button"
                    onClick={() => {
                      setTriageResult(null)
                      setFormData({ name: '', age: 0, gender: '', phone: '', symptoms: '', audioLanguage: 'kn-IN' })
                      setLockedFields(new Set())
                    }}
                    className="px-6 py-3 bg-white border border-gray-300 hover:bg-gray-50 text-gray-700 font-semibold rounded-2xl transition"
                  >
                    New Patient
                  </button>
                </div>
              </div>
            )}

          </div>

        </div>
      </div>
    </div>
  )
}
