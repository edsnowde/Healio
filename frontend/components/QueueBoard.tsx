import Link from 'next/link'
import { AlertCircle, CheckCircle, AlertTriangle, Clock, Building2 } from 'lucide-react'

export interface QueuePatient {
  id: string
  patient_id: string                  // Reference to patients/{patient_id}
  name?: string                       // Patient name
  chief_complaint: string
  symptoms: string[]
  triage_color: 'Red' | 'Yellow' | 'Green'
  risk_score: number                  // 0.0–1.0 from Firestore
  assigned_doctor: string
  assigned_department: string
  status: string
  timestamp: string
  requires_anm_confirmation: boolean
  urgent_flag?: boolean
}

interface QueueBoardProps {
  patients: QueuePatient[]
  onStatusChange?: (id: string, status: 'waiting' | 'in_consultation' | 'completed') => void
}

export default function QueueBoard({ patients, onStatusChange }: QueueBoardProps) {

  const getPriorityIcon = (color: 'Red' | 'Yellow' | 'Green') => {
    const icons = {
      Red:    <AlertCircle   className="w-5 h-5 text-red-600" />,
      Yellow: <AlertTriangle className="w-5 h-5 text-yellow-500" />,
      Green:  <CheckCircle   className="w-5 h-5 text-green-600" />,
    }
    return icons[color]
  }

  const getPriorityBg = (color: 'Red' | 'Yellow' | 'Green') => {
    const styles = {
      Red:    'bg-red-50    border-l-4 border-red-500',
      Yellow: 'bg-yellow-50 border-l-4 border-yellow-400',
      Green:  'bg-green-50  border-l-4 border-green-500',
    }
    return styles[color]
  }

  const getDeptColor = (dept: string) => {
    const map: Record<string, string> = {
      'Emergency':            'bg-red-100 text-red-700 border-red-200',
      'Cardiology':           'bg-pink-100 text-pink-700 border-pink-200',
      'Paediatrics':          'bg-purple-100 text-purple-700 border-purple-200',
      'Respiratory Medicine': 'bg-blue-100 text-blue-700 border-blue-200',
      'Orthopaedics':         'bg-orange-100 text-orange-700 border-orange-200',
      'General Medicine':     'bg-teal-100 text-teal-700 border-teal-200',
      'Dermatology':          'bg-yellow-100 text-yellow-700 border-yellow-200',
      'ENT':                  'bg-indigo-100 text-indigo-700 border-indigo-200',
      'OB&G':                 'bg-rose-100 text-rose-700 border-rose-200',
    }
    return map[dept] ?? 'bg-gray-100 text-gray-700 border-gray-200'
  }

  const formatTime = (ts: string) => {
    try {
      return new Date(ts).toLocaleTimeString('en-IN', {
        hour: '2-digit', minute: '2-digit', hour12: true,
      })
    } catch { return ts }
  }

  const riskPct = (score: number) => Math.round(score * 100)

  // Sort: Red → Yellow → Green
  const sorted = [...patients].sort((a, b) => {
    const order = { Red: 0, Yellow: 1, Green: 2 }
    return order[a.triage_color] - order[b.triage_color]
  })

  return (
    <div className="bg-white rounded-xl shadow p-6">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Patient Priority Queue</h2>

      <div className="space-y-3">
        {sorted.map((patient, idx) => (
          <Link
            key={patient.id}
            href={`/patient/${patient.patient_id}`}
            className="block"
          >
            <div
              className={`${getPriorityBg(patient.triage_color)} rounded-lg p-4 transition-all hover:shadow-md hover:scale-102 cursor-pointer`}
            >
            <div className="flex items-start justify-between gap-4 flex-wrap">

              {/* Queue number + info */}
              <div className="flex gap-4 items-start flex-1 min-w-0">
                <div className="flex items-center justify-center w-10 h-10 bg-gray-200 rounded-full font-bold text-gray-900 flex-shrink-0">
                  {idx + 1}
                </div>

                <div className="flex-1 min-w-0">
                  {/* Patient name and ID row - NEW! */}
                  <div className="flex items-center gap-2 mb-2 flex-wrap">
                    <span className="font-bold text-gray-900">👤 {patient.name || 'Unknown'}</span>
                    {patient.patient_id && (
                      <span className="text-xs bg-gray-200 text-gray-700 px-2 py-1 rounded font-mono">ID: {patient.patient_id.slice(0, 8)}</span>
                    )}
                  </div>

                  <div className="flex items-center gap-2 mb-1 flex-wrap">
                    {getPriorityIcon(patient.triage_color)}
                    <h3 className="font-bold text-gray-900 truncate">{patient.chief_complaint}</h3>
                    {patient.requires_anm_confirmation && (
                      <span className="text-xs bg-red-600 text-white px-2 py-0.5 rounded-full font-semibold flex-shrink-0">
                        ANM Confirm
                      </span>
                    )}
                  </div>

                  {/* Symptoms as tags */}
                  <div className="flex flex-wrap gap-1 mb-2">
                    {(Array.isArray(patient.symptoms)
                      ? patient.symptoms
                      : typeof patient.symptoms === 'string'
                      ? [patient.symptoms]
                      : []
                    ).slice(0, 4).map((s: string, i: number) => (
                      <span key={i} className="text-xs bg-white/70 border border-gray-200 rounded px-2 py-0.5 text-gray-600">
                        {s}
                      </span>
                    ))}
                  </div>

                  <div className="flex gap-4 text-xs text-gray-600 flex-wrap">
                    <span>
                      Risk: <strong className={
                        patient.triage_color === 'Red' ? 'text-red-600' :
                        patient.triage_color === 'Yellow' ? 'text-yellow-600' : 'text-green-600'
                      }>{riskPct(patient.risk_score)}%</strong>
                    </span>
                    <span>Intake: <strong className="text-gray-900">{formatTime(patient.timestamp)}</strong></span>
                  </div>
                </div>
              </div>

              {/* Right side: doctor + department + action */}
              <div className="flex flex-col items-end gap-2 flex-shrink-0">
                <div className="text-right">
                  <p className="text-xs text-gray-500">Assigned to</p>
                  <p className="font-bold text-gray-900 text-sm">{patient.assigned_doctor}</p>
                </div>

                {/* Department badge */}
                <span className={`inline-flex items-center gap-1 text-xs font-semibold border rounded-full px-3 py-1 ${getDeptColor(patient.assigned_department)}`}>
                  <Building2 size={11} />
                  {patient.assigned_department}
                </span>

                {/* Status selector */}
                {onStatusChange && (
                  <select
                    value={patient.status}
                    onChange={e => onStatusChange(patient.id, e.target.value as any)}
                    className="text-xs border rounded px-2 py-1 bg-white text-gray-700 cursor-pointer"
                  >
                    <option value="waiting">Waiting</option>
                    <option value="in_consultation">In Consultation</option>
                    <option value="completed">Completed</option>
                  </select>
                )}
              </div>

            </div>
            </div>
          </Link>
        ))}
      </div>

      {patients.length === 0 && (
        <div className="text-center py-16">
          <CheckCircle className="w-12 h-12 text-green-400 mx-auto mb-4" />
          <p className="text-gray-500 font-medium">No patients in queue</p>
          <p className="text-gray-400 text-sm mt-1">New patients will appear here in real-time</p>
        </div>
      )}
    </div>
  )
}
