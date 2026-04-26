import { AlertTriangle, Bell } from 'lucide-react'

interface ClusterAlertProps {
  message: string
}

export default function ClusterAlert({ message }: ClusterAlertProps) {
  return (
    <div className="bg-danger/10 border border-danger rounded-lg p-4 flex items-start gap-3 animate-slide-in">
      <div className="flex-shrink-0 mt-0.5">
        <Bell className="w-5 h-5 text-danger animate-pulse-glow" />
      </div>
      <div className="flex-1">
        <h3 className="font-bold text-danger mb-1">Outbreak Surveillance Alert</h3>
        <p className="text-gray-700 text-sm">{message}</p>
      </div>
      <button className="text-sm text-danger font-medium hover:text-danger/80 transition-colors flex-shrink-0">
        Review
      </button>
    </div>
  )
}
