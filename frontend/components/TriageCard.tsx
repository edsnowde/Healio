import { AlertCircle, CheckCircle, AlertTriangle, Activity } from 'lucide-react'
import { Fragment } from 'react'

interface TriageCardProps {
  triageData: {
    patientId: string
    riskScore: number
    priority: 'red' | 'yellow' | 'green'
    doctorAssignment: string
    summary: string
    recommendations: string[]
    outbreak: boolean
    clusterAlert?: string
  }
}

export default function TriageCard({ triageData }: TriageCardProps) {
  const priorityConfig = {
    red: {
      label: 'URGENT',
      color: 'text-priority-red',
      bgColor: 'bg-priority-red/10',
      borderColor: 'border-priority-red',
      icon: AlertCircle,
    },
    yellow: {
      label: 'MODERATE',
      color: 'text-priority-yellow',
      bgColor: 'bg-priority-yellow/10',
      borderColor: 'border-priority-yellow',
      icon: AlertTriangle,
    },
    green: {
      label: 'LOW RISK',
      color: 'text-priority-green',
      bgColor: 'bg-priority-green/10',
      borderColor: 'border-priority-green',
      icon: CheckCircle,
    },
  }

  const config = priorityConfig[triageData.priority]
  const Icon = config.icon

  return (
    <div className={`rounded-xl border-l-4 ${config.borderColor} ${config.bgColor} p-8 bg-white shadow-elevated`}>
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <Icon className={`w-8 h-8 ${config.color}`} />
            <span className={`text-sm font-bold uppercase tracking-wide ${config.color}`}>{config.label}</span>
          </div>
          <p className="text-gray-600 text-sm">
            Patient ID: <span className="font-mono font-bold text-gray-900">{triageData.patientId}</span>
          </p>
        </div>
        <div className="text-right">
          <p className="text-gray-600 text-sm">Risk Score</p>
          <p className={`text-4xl font-bold ${config.color}`}>{triageData.riskScore}%</p>
        </div>
      </div>

      {/* Summary */}
      <div className="mb-6 bg-gray-50 rounded-lg p-4">
        <h3 className="font-bold text-gray-900 mb-2">Clinical Summary</h3>
        <p className="text-gray-700 leading-relaxed">{triageData.summary}</p>
      </div>

      {/* Doctor Assignment */}
      <div className="mb-6 flex items-center gap-3 p-4 bg-primary/5 rounded-lg border border-primary/20">
        <Activity className="w-5 h-5 text-primary flex-shrink-0" />
        <div>
          <p className="text-sm text-gray-600">Doctor Assignment</p>
          <p className="font-bold text-gray-900">{triageData.doctorAssignment}</p>
        </div>
      </div>

      {/* Recommendations */}
      <div>
        <h3 className="font-bold text-gray-900 mb-3">Recommended Actions</h3>
        <ul className="space-y-2">
          {triageData.recommendations.map((rec, idx) => (
            <li key={idx} className="flex items-start gap-3 text-gray-700">
              <span className="inline-block w-2 h-2 rounded-full bg-primary mt-2 flex-shrink-0" />
              <span>{rec}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}
