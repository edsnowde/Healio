'use client'

import { useState, useRef, useEffect, useCallback } from 'react'
import {
  Mic,
  Upload,
  CheckCircle2,
  Volume2,
  MicOff,
  Lock,
  RotateCcw,
  AlertCircle,
  Globe,
} from 'lucide-react'

// ─── Types ────────────────────────────────────────────────────────────────────

interface PatientFormProps {
  onSubmit?: (formData: PatientFormData) => void
}

export interface PatientFormData {
  name: string
  age: number
  gender: string
  phone: string
  symptoms: string
}

type FieldName = keyof PatientFormData

const LOCKABLE_FIELDS: FieldName[] = ['name', 'age', 'gender', 'phone']

// ─── Validation constraints (same logic, Kannada hint text) ──────────────────

interface FieldConstraint {
  validate: (val: string | number) => boolean
  hint: string
}

const FIELD_CONSTRAINTS: Partial<Record<FieldName, FieldConstraint>> = {
  name: {
    validate: (v) => String(v).trim().length >= 2,
    hint: 'ಹೆಸರು ಕನಿಷ್ಠ 2 ಅಕ್ಷರಗಳಾಗಿರಬೇಕು',
  },
  age: {
    validate: (v) => {
      const n = Number(v)
      return Number.isInteger(n) && n >= 1 && n <= 99
    },
    hint: 'ವಯಸ್ಸು 1 ರಿಂದ 99 ರ ನಡುವೆ ಇರಬೇಕು',
  },
  gender: {
    validate: (v) => ['ಪುರುಷ', 'ಮಹಿಳೆ'].includes(String(v)),
    hint: '"ಪುರುಷ" ಅಥವಾ "ಮಹಿಳೆ" ಎಂದು ಹೇಳಿ',
  },
  phone: {
    validate: (v) => /^\d{10}$/.test(String(v).replace(/\D/g, '')),
    hint: 'ದೂರವಾಣಿ ಸಂಖ್ಯೆ ನಿಖರವಾಗಿ 10 ಅಂಕೆಗಳಾಗಿರಬೇಕು',
  },
}

// ─── Language → Web Speech API lang code ─────────────────────────────────────

const LANG_CODE: Record<string, string> = {
  Kannada: 'kn-IN',
  English: 'en-US',
  Hindi:   'hi-IN',
}

// ─── Speech abstraction ───────────────────────────────────────────────────────

interface RecognitionCallbacks {
  onInterim: (text: string) => void
  onFinal:   (text: string) => void
  onEnd:     ()             => void
  onError:   (err: string)  => void
}

function createRecognition(lang: string, callbacks: RecognitionCallbacks) {
  const SR =
    (window as any).SpeechRecognition ||
    (window as any).webkitSpeechRecognition

  if (!SR) { callbacks.onError('not_supported'); return null }

  const rec = new SR()
  rec.lang           = lang
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
      const digits = raw.replace(/\D/g, '').slice(0, 2)
      return Number(digits) || 0
    }
    case 'phone': {
      return raw.replace(/\D/g, '').slice(-10)
    }
    case 'gender': {
      const t = raw.toLowerCase().trim()
      // Kannada words
      if (t.includes('ಮಹಿಳೆ') || t.includes('ಹೆಣ್ಣು') || t.includes('female') || t.includes('महिला')) return 'ಮಹಿಳೆ'
      if (t.includes('ಪುರುಷ') || t.includes('male') || t.includes('पुरुष')) return 'ಪುರುಷ'
      // Also catch English phonetics from kn-IN STT
      if (/fe[\s-]?m(ale|ail)/.test(t) || t.includes('femail')) return 'ಮಹಿಳೆ'
      if (t.includes('male') || t.includes('mail')) return 'ಪುರುಷ'
      return ''
    }
    default:
      return raw.trim()
  }
}

// ─── Component ────────────────────────────────────────────────────────────────

export default function KannadaIntake() {
  const [formData, setFormData] = useState<PatientFormData>({
    name: '', age: 0, gender: '', phone: '', symptoms: '',
  })

  const [lockedFields,      setLockedFields]      = useState<Set<FieldName>>(new Set())
  const [fieldErrors,       setFieldErrors]       = useState<Partial<Record<FieldName, string>>>({})
  const [activeField,       setActiveField]       = useState<FieldName | null>(null)
  const [interimText,       setInterimText]       = useState('')
  const [speechSupported,   setSpeechSupported]   = useState(true)
  const [isLoading,         setIsLoading]         = useState(false)
  const [formError,         setFormError]         = useState('')
  const [extractedSymptoms, setExtractedSymptoms] = useState<string[]>([])
  const [showExtracted,     setShowExtracted]     = useState(false)
  const [waveformBars,      setWaveformBars]      = useState(Array(20).fill(0.3))
  const [selectedLanguage,  setSelectedLanguage]  = useState('Kannada')

  const recognitionRef = useRef<any>(null)
  const silenceTimer   = useRef<ReturnType<typeof setTimeout> | null>(null)
  const animationRef   = useRef<number | null>(null)
  const accFinalRef    = useRef('')

  // ── Check browser support ─────────────────────────────────────────────────
  useEffect(() => {
    const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
    if (!SR) setSpeechSupported(false)
  }, [])

  // ── Waveform animation ────────────────────────────────────────────────────
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

  // ── Unlock a locked field ──────────────────────────────────────────────────
  const unlockField = (field: FieldName) => {
    setLockedFields(prev => { const s = new Set(prev); s.delete(field); return s })
    setFormData(prev => ({ ...prev, [field]: field === 'age' ? 0 : '' }))
    setFieldErrors(prev => ({ ...prev, [field]: undefined }))
  }

  // ── startVoiceInput ────────────────────────────────────────────────────────
  const startVoiceInput = useCallback((field: FieldName) => {
    if (recognitionRef.current) { recognitionRef.current.stop(); recognitionRef.current = null }
    if (silenceTimer.current)   { clearTimeout(silenceTimer.current); silenceTimer.current = null }

    accFinalRef.current = ''
    setInterimText('')
    setActiveField(field)
    setFieldErrors(prev => ({ ...prev, [field]: undefined }))

    const langCode = LANG_CODE[selectedLanguage] ?? 'kn-IN'

    const resetSilenceTimer = (rec: any) => {
      if (silenceTimer.current) clearTimeout(silenceTimer.current)
      silenceTimer.current = setTimeout(() => rec.stop(), 2500)
    }

    const rec = createRecognition(langCode, {
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

        // ── Lockable fields: validate before locking ──────────────────────
        if (LOCKABLE_FIELDS.includes(field)) {
          const constraint = FIELD_CONSTRAINTS[field]
          if (constraint && !constraint.validate(coerced)) {
            setFieldErrors(prev => ({ ...prev, [field]: constraint.hint }))
            setFormData(prev => ({ ...prev, [field]: field === 'age' ? 0 : '' }))
            return
          }
          setFormData(prev => {
            const updated = { ...prev, [field]: coerced }
            sessionStorage.setItem('patientFormDataKn', JSON.stringify(updated))
            return updated
          })
          setLockedFields(prev => new Set([...prev, field]))
          return
        }

        // ── Symptoms field: extract keyword tags ──────────────────────────
        if (field === 'symptoms' && final) {
          const keywords = final.split(/[\s,]+/).filter(w => w.length > 2).slice(0, 5)
          setExtractedSymptoms(keywords)
          setShowExtracted(true)
        }

        setFormData(prev => {
          const updated = { ...prev, [field]: coerced }
          sessionStorage.setItem('patientFormDataKn', JSON.stringify(updated))
          return updated
        })
      },
      onError: (err) => {
        if (err === 'not_supported') setSpeechSupported(false)
        setActiveField(null)
        setInterimText('')
      },
    })

    if (!rec) return
    recognitionRef.current = rec
    rec.start()
  }, [selectedLanguage])

  // ── Manual change ─────────────────────────────────────────────────────────
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

  // ── Validate & submit ─────────────────────────────────────────────────────
  const validateForm = () => {
    if (!formData.name.trim())     { setFormError('ರೋಗಿಯ ಹೆಸರು ಅಗತ್ಯವಿದೆ'); return false }
    if (!formData.symptoms.trim()) { setFormError('ಲಕ್ಷಣಗಳು ಅಗತ್ಯವಿದೆ');    return false }
    return true
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setFormError('')
    if (!validateForm()) return
    setIsLoading(true)
    setTimeout(() => {
      // Form data ready - can be used for API call or navigation
      sessionStorage.setItem('patientFormDataKn', JSON.stringify(formData))
      setIsLoading(false)
    }, 1500)
  }

  // ─── Sub-components ────────────────────────────────────────────────────────

  const VoiceFieldMic = ({ field }: { field: FieldName }) => {
    if (!speechSupported) return (
      <span title="ಈ ಬ್ರೌಸರ್‌ನಲ್ಲಿ ಧ್ವನಿ ಬೆಂಬಲಿತವಾಗಿಲ್ಲ"
        className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-300 cursor-not-allowed">
        <MicOff size={17} />
      </span>
    )
    const isActive = activeField === field
    return (
      <button
        type="button"
        aria-label={`${field} ಗಾಗಿ ಧ್ವನಿ ನಮೂದು`}
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

  const InterimBadge = ({ field }: { field: FieldName }) =>
    activeField === field && interimText ? (
      <p className="mt-1 text-xs text-emerald-600 italic truncate pl-1">🎙 {interimText}</p>
    ) : null

  const FieldError = ({ field }: { field: FieldName }) =>
    fieldErrors[field] ? (
      <p className="mt-1 text-xs text-red-500 flex items-center gap-1 pl-1">
        <AlertCircle size={12} />{fieldErrors[field]}
      </p>
    ) : null

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
          title={`${label} ಮರು-ದಾಖಲಿಸಿ`}
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
          <RotateCcw size={11} />ಮರು-ದಾಖಲು
        </button>
      </div>
    </div>
  )

  const UnsupportedBanner = () =>
    !speechSupported ? (
      <div className="bg-amber-50 border border-amber-200 text-amber-700 p-3 rounded-xl text-sm flex items-center gap-2">
        <MicOff size={16} />
        ಧ್ವನಿ ನಮೂದು ಈ ಬ್ರೌಸರ್‌ನಲ್ಲಿ ಬೆಂಬಲಿತವಾಗಿಲ್ಲ. ದಯವಿಟ್ಟು Chrome ಅಥವಾ Edge ಬಳಸಿ.
      </div>
    ) : null

  // ─── Render ────────────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen relative overflow-hidden">

      {/* Background */}
      <div className="absolute inset-0"
        style={{ background: 'linear-gradient(135deg,#ddb9ec 50%, #ffffff 50%)' }} />
      <div className="absolute top-20 left-20 w-72 h-72 bg-emerald-200/40 rounded-full blur-3xl" />
      <div className="absolute bottom-10 right-10 w-96 h-96 bg-green-100/50 rounded-full blur-3xl" />

      <div className="relative z-10 max-w-6xl mx-auto px-6 py-16">
        <div className="grid lg:grid-cols-2 gap-14 items-center">

          {/* ── Left Hero ─────────────────────────────────────────────────── */}
          <div>
            <p className="uppercase tracking-[4px] text-emerald-700 font-semibold mb-4">
              AI ತ್ರೈಯಾಜ್ ವ್ಯವಸ್ಥೆ
            </p>
            <h1 className="text-5xl font-bold leading-tight mb-6 text-gray-900">
              ಸ್ಮಾರ್ಟ್ ರೋಗಿ ನೋಂದಣಿ <br />
              ಪ್ರಾಥಮಿಕ ಆರೋಗ್ಯಕ್ಕಾಗಿ
            </h1>
            <p className="text-lg text-gray-600 mb-8 leading-relaxed">
              ಧ್ವನಿ ಆಧಾರಿತ ಲಕ್ಷಣ ಸಂಗ್ರಹ, ಅಪಾಯ ಮೌಲ್ಯಮಾಪನ
              ಮತ್ತು ವೈದ್ಯರ ಮಾರ್ಗೀಕರಣ ಹೀಲಿಯೊ ಮೂಲಕ.
            </p>
            <div className="grid grid-cols-2 gap-5">
              <div className="bg-white/70 backdrop-blur-xl rounded-2xl p-6 shadow-lg">
                <h3 className="font-bold text-emerald-700 text-2xl">3 ಏಜೆಂಟ್ಸ್</h3>
                <p className="text-sm text-gray-600">ಸ್ವಯಂಚಾಲಿತ ತ್ರೈಯಾಜ್ ಪೈಪ್‌ಲೈನ್</p>
              </div>
              <div className="bg-white/70 backdrop-blur-xl rounded-2xl p-6 shadow-lg">
                <h3 className="font-bold text-emerald-700 text-2xl">ರಿಯಲ್ ಟೈಮ್</h3>
                <p className="text-sm text-gray-600">ಆದ್ಯತೆ ಸರದಿ ಮಾರ್ಗೀಕರಣ</p>
              </div>
            </div>
          </div>

          {/* ── Form Card ─────────────────────────────────────────────────── */}
          <div>
            <form
              onSubmit={handleSubmit}
              className="
                bg-white/85 backdrop-blur-2xl rounded-[30px]
                shadow-2xl p-10 space-y-8 border border-white/60
              "
            >
              <h2 className="text-3xl font-bold text-gray-900">ರೋಗಿ ನೋಂದಣಿ</h2>

              <UnsupportedBanner />

              {formError && (
                <div className="bg-red-50 border border-red-200 text-red-600 p-4 rounded-xl flex items-center gap-2 text-sm">
                  <AlertCircle size={16} className="shrink-0" />{formError}
                </div>
              )}

              {/* ── Personal Details ─────────────────────────────────────── */}
              <div className="space-y-3">
                <div className="flex items-center gap-2 mb-1">
                  <p className="text-xs font-bold text-gray-400 uppercase tracking-widest">
                    ವೈಯಕ್ತಿಕ ವಿವರಗಳು
                  </p>
                  <span className="text-xs text-emerald-600 font-medium">
                    — ಧ್ವನಿ ನಂತರ ಕ್ಷೇತ್ರ ಲಾಕ್ ಆಗುತ್ತದೆ
                  </span>
                </div>

                {/* Full Name */}
                <div>
                  {lockedFields.has('name') ? (
                    <LockedField field="name" label="ಹೆಸರು" value={formData.name} />
                  ) : (
                    <div className="relative">
                      <input
                        name="name"
                        value={formData.name}
                        onChange={handleChange}
                        placeholder="ಪೂರ್ಣ ಹೆಸರು — ನಿಮ್ಮ ಹೆಸರು ಹೇಳಿ"
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
                    <LockedField field="age" label="ವಯಸ್ಸು" value={formData.age} />
                  ) : (
                    <div className="relative">
                      <input
                        type="number"
                        name="age"
                        min={1} max={99}
                        value={formData.age || ''}
                        onChange={handleChange}
                        placeholder="ವಯಸ್ಸು — 1 ರಿಂದ 99 ಹೇಳಿ"
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
                    <LockedField field="gender" label="ಲಿಂಗ" value={formData.gender} />
                  ) : (
                    <div className="relative">
                      <select
                        name="gender"
                        value={formData.gender}
                        onChange={handleChange}
                        className="w-full border rounded-xl p-4 pr-12 appearance-none focus:outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-200 transition bg-white"
                      >
                        <option value="">ಲಿಂಗ ಆಯ್ಕೆ — "ಪುರುಷ" / "ಮಹಿಳೆ" ಹೇಳಿ</option>
                        <option value="ಪುರುಷ">ಪುರುಷ</option>
                        <option value="ಮಹಿಳೆ">ಮಹಿಳೆ</option>
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
                    <LockedField field="phone" label="ದೂರವಾಣಿ" value={formData.phone} />
                  ) : (
                    <div className="relative">
                      <input
                        name="phone"
                        value={formData.phone}
                        onChange={handleChange}
                        placeholder="10 ಅಂಕೆ ದೂರವಾಣಿ — ಹತ್ತು ಅಂಕೆ ಹೇಳಿ"
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

              {/* ── Language Selector ────────────────────────────────────── */}
              <div>
                <label className="block mb-2 font-semibold text-gray-700 flex items-center gap-2">
                  <Globe size={16} className="text-emerald-600" />
                  ಭಾಷೆ ಆಯ್ಕೆ
                </label>
                <select
                  value={selectedLanguage}
                  onChange={(e) => setSelectedLanguage(e.target.value)}
                  className="w-full border-2 border-emerald-200 rounded-xl p-3 focus:outline-none focus:border-emerald-500 transition bg-white"
                >
                  <option>Kannada</option>
                  <option>English</option>
                  <option>Hindi</option>
                </select>
              </div>

              {/* ── Primary Voice Symptom Intake ─────────────────────────── */}
              <div className="
                bg-gradient-to-br from-emerald-50/80 to-green-50/80
                backdrop-blur-2xl rounded-3xl
                border-2 border-emerald-200/60
                p-8 shadow-xl relative overflow-hidden
              ">
                <div className="absolute top-4 right-4 flex items-center gap-2 bg-emerald-600 text-white px-4 py-1.5 rounded-full text-xs font-semibold">
                  <Volume2 size={14} />
                  ಪ್ರಮುಖ ನೋಂದಣಿ
                </div>

                <div className="mb-6">
                  <h3 className="text-2xl font-bold text-gray-900 mb-2">
                    ಪ್ರಮುಖ ಧ್ವನಿ ಲಕ್ಷಣ ನಮೂದು
                  </h3>
                  <p className="text-emerald-700 font-medium">
                    ಕನ್ನಡ, ಇಂಗ್ಲಿಷ್ ಅಥವಾ ಹಿಂದಿಯಲ್ಲಿ ಮಾತನಾಡಿ
                  </p>
                </div>

                {/* Waveform while recording symptoms */}
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
                      ಕೇಳಲಾಗುತ್ತಿದೆ…
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
                    {activeField === 'symptoms' ? 'ಕೇಳಲಾಗುತ್ತಿದೆ… (ನಿಲ್ಲಿಸಲು ಒತ್ತಿ)' : 'ಧ್ವನಿ ದಾಖಲಿಸಲು ಆರಂಭಿಸಿ'}
                  </button>
                </div>

                {/* Status chips */}
                <div className="flex flex-wrap gap-3">
                  {[
                    { icon: <CheckCircle2 size={16} />, label: 'ಧ್ವನಿ ರಿಂದ ಪಠ್ಯ'     },
                    { icon: <Mic          size={16} />, label: 'ಧ್ವನಿ-ಮೊದಲ ಕ್ಷೇತ್ರಗಳು' },
                    { icon: <CheckCircle2 size={16} />, label: 'AI ಲಕ್ಷಣ ವಿಶ್ಲೇಷಣೆ'   },
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

              {/* ── Extracted Symptoms Preview ───────────────────────────── */}
              {showExtracted && extractedSymptoms.length > 0 && (
                <div className="
                  bg-gradient-to-r from-green-50 to-emerald-50
                  border-l-4 border-emerald-600
                  rounded-xl p-6 shadow-md
                ">
                  <h4 className="font-bold text-emerald-900 mb-3 flex items-center gap-2">
                    <CheckCircle2 size={20} className="text-emerald-600" />
                    ಪತ್ತೆಯಾದ ಲಕ್ಷಣಗಳು
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

              {/* ── Agentic Flow Steps ───────────────────────────────────── */}
              <div className="grid md:grid-cols-3 gap-4">
                {[
                  { n: 1, title: 'ಧ್ವನಿ ನೋಂದಣಿ',   sub: 'ಲಕ್ಷಣ ಸಂಗ್ರಹ'     },
                  { n: 2, title: 'AI ವಿಶ್ಲೇಷಣೆ',   sub: 'ಲಕ್ಷಣ ವಿಶ್ಲೇಷಣೆ'  },
                  { n: 3, title: 'ತ್ರೈಯಾಜ್ ಮಾರ್ಗೀಕರಣ', sub: 'ಆದ್ಯತೆ ನಿಯೋಜನೆ' },
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

              {/* ── Alternative Input Methods ────────────────────────────── */}
              <div>
                <h3 className="text-lg font-bold text-gray-900 mb-4">
                  ಪರ್ಯಾಯ ನಮೂದು ವಿಧಾನಗಳು
                </h3>
                <div className="grid md:grid-cols-2 gap-5">

                  {/* Upload */}
                  <div className="
                    border-2 border-dashed border-emerald-300 rounded-2xl
                    p-8 text-center
                    hover:border-emerald-500 hover:bg-emerald-50/30
                    transition bg-white/60 backdrop-blur-sm
                  ">
                    <Upload className="mx-auto mb-4 text-emerald-600" size={32} />
                    <p className="font-bold text-gray-900">ವೈದ್ಯಕೀಯ ಚಿತ್ರ ಅಪ್ಲೋಡ್</p>
                    <p className="text-sm text-gray-600 mt-1">Gemini Vision ನೋಂದಣಿ</p>
                    <p className="text-xs text-gray-500 mt-2">ಪ್ರಿಸ್ಕ್ರಿಪ್ಷನ್, ರಾಶ್, ಗಾಯ, ಸ್ಕ್ಯಾನ್</p>
                  </div>

                  {/* Text backup */}
                  <div className="
                    border-2 border-dashed border-gray-300 rounded-2xl
                    p-6 text-center
                    hover:border-gray-400 hover:bg-gray-50/30
                    transition bg-white/60 backdrop-blur-sm
                  ">
                    <p className="text-sm font-semibold text-gray-600 mb-3">
                      ಬ್ಯಾಕಪ್ ಪಠ್ಯ ಲಕ್ಷಣ ನಮೂದು
                    </p>
                    <div className="relative">
                      <textarea
                        name="symptoms"
                        value={formData.symptoms}
                        onChange={handleChange}
                        rows={4}
                        placeholder="ಅಥವಾ ಲಕ್ಷಣಗಳನ್ನು ಇಲ್ಲಿ ಬರೆಯಿರಿ…"
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
                        aria-label="ಲಕ್ಷಣಗಳಿಗಾಗಿ ಧ್ವನಿ ನಮೂದು"
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

              {/* ── Submit ───────────────────────────────────────────────── */}
              <button
                type="submit"
                disabled={isLoading}
                className="
                  w-full py-4 rounded-2xl
                  bg-emerald-600 hover:bg-emerald-700
                  text-white font-bold text-lg shadow-lg
                  transition disabled:opacity-60
                "
              >
                {isLoading ? 'AI ವಿಶ್ಲೇಷಣೆ ನಡೆಯುತ್ತಿದೆ…' : 'ತ್ರೈಯಾಜ್ ಸಲ್ಲಿಸಿ'}
              </button>

              <p className="text-center text-xs text-gray-500">
                ಸುರಕ್ಷಿತ ಮತ್ತು PHC ಅನುಸರಣಾ ಆರೋಗ್ಯ ನೋಂದಣಿ
              </p>
            </form>
          </div>

        </div>
      </div>
    </div>
  )
}