'use client'

import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import Link from 'next/link'
import { doc, getDoc } from 'firebase/firestore'
import { db } from '@/lib/firebase'
import { ArrowLeft, Clock, AlertCircle, CheckCircle, AlertTriangle } from 'lucide-react'

interface PatientData {
  [key: string]: any
}

export default function PatientDetailPage() {
  const params = useParams()
  const patientId = params.id as string
  
  const [patient, setPatient] = useState<PatientData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchPatient = async () => {
      try {
        setLoading(true)
        const patientRef = doc(db, 'patients', patientId)
        const patientSnap = await getDoc(patientRef)
        
        if (patientSnap.exists()) {
          setPatient(patientSnap.data())
          console.log('✅ Patient data fetched:', patientSnap.data())
        } else {
          setError('Patient not found in database')
        }
      } catch (err: any) {
        console.error('❌ Error fetching patient:', err)
        setError(err.message || 'Failed to fetch patient data')
      } finally {
        setLoading(false)
      }
    }

    if (patientId) {
      fetchPatient()
    }
  }, [patientId])

  const getPriorityIcon = (color: string) => {
    const icons: Record<string, JSX.Element> = {
      Red: <AlertCircle className="w-6 h-6 text-red-600" />,
      Yellow: <AlertTriangle className="w-6 h-6 text-yellow-500" />,
      Green: <CheckCircle className="w-6 h-6 text-green-600" />,
    }
    return icons[color] || icons.Green
  }

  const formatValue = (value: any): string => {
    if (value === null || value === undefined) return 'N/A'
    if (typeof value === 'object') return JSON.stringify(value, null, 2)
    if (typeof value === 'boolean') return value ? 'Yes' : 'No'
    return String(value)
  }

  const formatDate = (dateString: string): string => {
    try {
      const date = new Date(dateString)
      return date.toLocaleString('en-IN', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: true
      })
    } catch {
      return dateString
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 py-12 px-6">
        <div className="max-w-6xl mx-auto">
          <div className="bg-white rounded-xl shadow-lg p-12 text-center">
            <div className="animate-spin w-12 h-12 border-4 border-emerald-200 border-t-emerald-600 rounded-full mx-auto mb-4"></div>
            <p className="text-gray-600 font-medium">Loading patient details...</p>
          </div>
        </div>
      </div>
    )
  }

  if (error || !patient) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 py-12 px-6">
        <div className="max-w-6xl mx-auto">
          <Link href="/dashboard" className="inline-flex items-center gap-2 text-emerald-600 hover:text-emerald-700 mb-6 font-semibold">
            <ArrowLeft size={18} /> Back to Dashboard
          </Link>
          <div className="bg-red-50 border border-red-200 rounded-xl shadow-lg p-8">
            <AlertCircle className="w-12 h-12 text-red-600 mx-auto mb-4" />
            <p className="text-center text-red-700 font-medium">{error || 'Patient not found'}</p>
          </div>
        </div>
      </div>
    )
  }

  const triageColor = patient.agent2_triage_color || 'Green'
  const riskScore = patient.agent2_risk_score || 0

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 py-12 px-6">
      <div className="max-w-6xl mx-auto">
        
        {/* Back button */}
        <Link href="/dashboard" className="inline-flex items-center gap-2 text-emerald-600 hover:text-emerald-700 mb-6 font-semibold">
          <ArrowLeft size={18} /> Back to Dashboard
        </Link>

        {/* Header Card */}
        <div className={`rounded-xl shadow-lg p-8 mb-8 ${
          triageColor === 'Red' ? 'bg-red-50 border-2 border-red-400' :
          triageColor === 'Yellow' ? 'bg-yellow-50 border-2 border-yellow-400' :
          'bg-green-50 border-2 border-green-400'
        }`}>
          <div className="flex items-start justify-between mb-6">
            <div>
              <h1 className="text-4xl font-bold text-gray-900 mb-2">{patient.name || 'Unknown Patient'}</h1>
              <p className="text-gray-600 font-mono text-sm">ID: {patientId}</p>
            </div>
            <div className="text-right">
              <div className="flex items-center gap-3 justify-end mb-3">
                {getPriorityIcon(triageColor)}
                <div>
                  <p className="text-xs text-gray-600 font-semibold">TRIAGE PRIORITY</p>
                  <p className={`text-3xl font-black ${
                    triageColor === 'Red' ? 'text-red-600' :
                    triageColor === 'Yellow' ? 'text-yellow-600' :
                    'text-green-600'
                  }`}>{triageColor}</p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-xs text-gray-600 font-semibold">RISK SCORE</p>
                <p className={`text-2xl font-bold ${
                  triageColor === 'Red' ? 'text-red-600' :
                  triageColor === 'Yellow' ? 'text-yellow-600' :
                  'text-green-600'
                }`}>{Math.round(riskScore * 100)}%</p>
              </div>
            </div>
          </div>

          <div className="grid md:grid-cols-3 gap-4">
            <div className="bg-white/70 rounded-lg p-4">
              <p className="text-xs font-bold text-gray-600 mb-1">Status</p>
              <p className="font-semibold text-gray-900">{patient.status || 'Unknown'}</p>
            </div>
            <div className="bg-white/70 rounded-lg p-4">
              <p className="text-xs font-bold text-gray-600 mb-1">Created At</p>
              <p className="font-semibold text-gray-900 text-sm">{formatDate(patient.created_at || '')}</p>
            </div>
            <div className="bg-white/70 rounded-lg p-4">
              <p className="text-xs font-bold text-gray-600 mb-1">Session ID</p>
              <p className="font-mono text-xs text-gray-900 truncate">{patient.session_id || 'N/A'}</p>
            </div>
          </div>
        </div>

        {/* Chief Complaint Section */}
        <div className="bg-white rounded-xl shadow-lg p-8 mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-4 flex items-center gap-2">
            <AlertCircle size={24} className="text-orange-600" />
            Chief Complaint
          </h2>
          <p className="text-lg text-gray-800 bg-orange-50 border border-orange-200 rounded-lg p-6">
            {patient.agent1_chief_complaint || 'No chief complaint recorded'}
          </p>
        </div>

        {/* Symptoms & Duration */}
        <div className="grid md:grid-cols-2 gap-8 mb-8">
          <div className="bg-white rounded-xl shadow-lg p-8">
            <h3 className="text-xl font-bold text-gray-900 mb-4">Symptoms</h3>
            <div className="space-y-2">
              {Array.isArray(patient.agent1_symptoms) && patient.agent1_symptoms.length > 0 ? (
                patient.agent1_symptoms.map((symptom: string, idx: number) => (
                  <div key={idx} className="flex items-center gap-2 bg-emerald-50 border border-emerald-200 rounded-lg p-3">
                    <CheckCircle size={16} className="text-emerald-600 flex-shrink-0" />
                    <span className="text-gray-800">{symptom}</span>
                  </div>
                ))
              ) : (
                <p className="text-gray-500 italic">No symptoms recorded</p>
              )}
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-lg p-8">
            <h3 className="text-xl font-bold text-gray-900 mb-4">Duration & Severity</h3>
            <div className="space-y-4">
              <div className="bg-gray-50 rounded-lg p-4">
                <p className="text-sm font-semibold text-gray-600 mb-1">Duration</p>
                <p className="text-lg font-bold text-gray-900">{patient.agent1_duration || 'Unknown'}</p>
              </div>
              <div className="bg-gray-50 rounded-lg p-4">
                <p className="text-sm font-semibold text-gray-600 mb-1">Severity</p>
                <p className="text-lg font-bold text-gray-900 capitalize">{patient.agent1_severity || 'Unknown'}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Agent Analysis */}
        <div className="grid md:grid-cols-2 gap-8 mb-8">
          {/* Agent 1 Output */}
          <div className="bg-white rounded-xl shadow-lg p-8">
            <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
              <span className="inline-flex items-center justify-center w-8 h-8 bg-blue-600 text-white rounded-full text-sm font-bold">1</span>
              Agent 1: Intake Analysis
            </h3>
            <div className="space-y-3 text-sm">
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <p className="text-xs font-bold text-blue-700 mb-2">Additional Info</p>
                <p className="text-gray-800 font-mono text-xs max-h-32 overflow-auto">
                  {formatValue(patient.agent1_additional_info)}
                </p>
              </div>
              {patient.agent1_multimodal_findings && Object.keys(patient.agent1_multimodal_findings).length > 0 && (
                <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                  <p className="text-xs font-bold text-purple-700 mb-2">Multimodal Findings</p>
                  <p className="text-gray-800 font-mono text-xs max-h-32 overflow-auto">
                    {formatValue(patient.agent1_multimodal_findings)}
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Agent 2 Output */}
          <div className="bg-white rounded-xl shadow-lg p-8">
            <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
              <span className="inline-flex items-center justify-center w-8 h-8 bg-purple-600 text-white rounded-full text-sm font-bold">2</span>
              Agent 2: Clinical Reasoning
            </h3>
            <div className="space-y-3 text-sm">
              <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                <p className="text-xs font-bold text-purple-700 mb-2">Reasoning</p>
                <p className="text-gray-800">{patient.agent2_reasoning || 'No reasoning provided'}</p>
              </div>
              {Array.isArray(patient.agent2_clinical_signals) && patient.agent2_clinical_signals.length > 0 && (
                <div className="bg-pink-50 border border-pink-200 rounded-lg p-4">
                  <p className="text-xs font-bold text-pink-700 mb-2">Clinical Signals</p>
                  {patient.agent2_clinical_signals.map((signal: string, idx: number) => (
                    <p key={idx} className="text-gray-800 text-xs mb-1">• {signal}</p>
                  ))}
                </div>
              )}
              {Array.isArray(patient.agent2_red_flags) && patient.agent2_red_flags.length > 0 && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                  <p className="text-xs font-bold text-red-700 mb-2">🚨 Red Flags</p>
                  {patient.agent2_red_flags.map((flag: string, idx: number) => (
                    <p key={idx} className="text-red-800 text-xs mb-1 font-semibold">• {flag}</p>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Agent 3 Routing */}
        <div className="bg-white rounded-xl shadow-lg p-8 mb-8">
          <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
            <span className="inline-flex items-center justify-center w-8 h-8 bg-green-600 text-white rounded-full text-sm font-bold">3</span>
            Agent 3: Routing & Handoff
          </h3>
          <div className="grid md:grid-cols-2 gap-4">
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <p className="text-xs font-bold text-green-700 mb-1">Assigned Doctor</p>
              <p className="text-lg font-bold text-gray-900">{patient.agent3_assigned_doctor || 'Unassigned'}</p>
            </div>
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <p className="text-xs font-bold text-green-700 mb-1">Department</p>
              <p className="text-lg font-bold text-gray-900">{patient.agent3_assigned_department || 'General'}</p>
            </div>
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <p className="text-xs font-bold text-green-700 mb-1">Queue Position</p>
              <p className="text-lg font-bold text-gray-900">{patient.agent3_queue_position || 'N/A'}</p>
            </div>
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <p className="text-xs font-bold text-green-700 mb-1">Estimated Wait</p>
              <p className="text-lg font-bold text-gray-900">{patient.agent3_estimated_wait_mins || 'N/A'} mins</p>
            </div>
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <p className="text-xs font-bold text-green-700 mb-1">ANM Confirmation</p>
              <p className="text-lg font-bold text-gray-900">{patient.agent3_requires_anm ? '✅ Required' : '❌ Not Required'}</p>
            </div>
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <p className="text-xs font-bold text-green-700 mb-1">Routing Decision</p>
              <p className="text-lg font-bold text-gray-900">{patient.agent3_routing_decision || 'Standard'}</p>
            </div>
          </div>
        </div>

        {/* Original Input */}
        <div className="bg-white rounded-xl shadow-lg p-8 mb-8">
          <h3 className="text-xl font-bold text-gray-900 mb-4">Original Text Input</h3>
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-6 font-mono text-sm text-gray-800 max-h-48 overflow-auto whitespace-pre-wrap break-words">
            {patient.original_text_input || 'No text input recorded'}
          </div>
        </div>

        {/* Gemini Responses (Raw) */}
        <div className="grid md:grid-cols-2 gap-8 mb-8">
          <div className="bg-white rounded-xl shadow-lg p-8">
            <h3 className="text-xl font-bold text-gray-900 mb-4">Agent 1: Raw Gemini Response</h3>
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 font-mono text-xs text-gray-800 max-h-64 overflow-auto whitespace-pre-wrap break-words">
              {patient.agent1_gemini_raw_response || 'No raw response recorded'}
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-lg p-8">
            <h3 className="text-xl font-bold text-gray-900 mb-4">Agent 2: Raw Gemini Response</h3>
            <div className="bg-purple-50 border border-purple-200 rounded-lg p-4 font-mono text-xs text-gray-800 max-h-64 overflow-auto whitespace-pre-wrap break-words">
              {patient.agent2_gemini_raw_response || 'No raw response recorded'}
            </div>
          </div>
        </div>

        {/* Prompts Sent */}
        <div className="grid md:grid-cols-2 gap-8 mb-8">
          <div className="bg-white rounded-xl shadow-lg p-8">
            <h3 className="text-xl font-bold text-gray-900 mb-4">Agent 1: Prompt Sent</h3>
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 font-mono text-xs text-gray-800 max-h-48 overflow-auto whitespace-pre-wrap break-words">
              {patient.agent1_prompt_sent || 'No prompt recorded'}
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-lg p-8">
            <h3 className="text-xl font-bold text-gray-900 mb-4">Agent 2: Prompt Sent</h3>
            <div className="bg-purple-50 border border-purple-200 rounded-lg p-4 font-mono text-xs text-gray-800 max-h-48 overflow-auto whitespace-pre-wrap break-words">
              {patient.agent2_prompt_sent || 'No prompt recorded'}
            </div>
          </div>
        </div>

        {/* Metadata */}
        <div className="bg-white rounded-xl shadow-lg p-8">
          <h3 className="text-xl font-bold text-gray-900 mb-4">Pipeline Metadata</h3>
          <div className="grid md:grid-cols-2 gap-4">
            <div className="bg-gray-50 rounded-lg p-4">
              <p className="text-sm font-semibold text-gray-600 mb-1">Agents Executed</p>
              <p className="text-gray-800 font-mono text-sm">{Array.isArray(patient.agents_executed) ? patient.agents_executed.join(', ') : 'N/A'}</p>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <p className="text-sm font-semibold text-gray-600 mb-1">Queue ID</p>
              <p className="text-gray-800 font-mono text-xs truncate">{patient.queue_id || 'N/A'}</p>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <p className="text-sm font-semibold text-gray-600 mb-1">Surveillance ID</p>
              <p className="text-gray-800 font-mono text-xs truncate">{patient.surveillance_id || 'N/A'}</p>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <p className="text-sm font-semibold text-gray-600 mb-1">Created At</p>
              <p className="text-gray-800 text-sm">{formatDate(patient.created_at || '')}</p>
            </div>
          </div>
        </div>

      </div>
    </main>
  )
}
