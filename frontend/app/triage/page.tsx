'use client'

import { useState, useEffect } from 'react'
import TriageCard from '@/components/TriageCard'
import { Loader2 } from 'lucide-react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'

interface AnalysisStep {
  agent: string
  status: 'pending' | 'running' | 'complete'
}

interface TriageResult {
  patientId: string
  riskScore: number
  priority: 'red' | 'yellow' | 'green'
  doctorAssignment: string
  summary: string
  recommendations: string[]
  outbreak: boolean
  clusterAlert?: string
}

export default function TriagePage() {
  const router = useRouter()
  const [steps, setSteps] = useState<AnalysisStep[]>([
    { agent: 'Agent 1: Intake Verification', status: 'running' },
    { agent: 'Agent 2: Risk Evaluation', status: 'pending' },
    { agent: 'Agent 3: Routing Assignment', status: 'pending' },
  ])

  const [triageResult, setTriageResult] = useState<TriageResult | null>(null)
  const [complete, setComplete] = useState(false)
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const initializeTriage = async () => {
      try {
        // Get patient data from sessionStorage
        const formDataStr = sessionStorage.getItem('patientFormData')
        if (!formDataStr) {
          setError('No patient data found. Please complete intake form first.')
          setIsLoading(false)
          setTimeout(() => router.push('/intake'), 2000)
          return
        }

        const formData = JSON.parse(formDataStr)

        // Simulate agent processing with timeline
        const timeline = [
          { index: 0, delay: 800 },
          { index: 1, delay: 2200 },
          { index: 2, delay: 3600 },
        ]

        timeline.forEach(({ index, delay }) => {
          setTimeout(() => {
            setSteps(prev => {
              const updated = [...prev]
              if (index > 0) {
                updated[index - 1] = { ...updated[index - 1], status: 'complete' }
              }
              updated[index] = { ...updated[index], status: 'running' }
              return updated
            })
          }, delay)
        })

        // Call backend API after agent animation completes (at 4000ms)
        setTimeout(async () => {
          try {
            const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'
            
            const response = await fetch(`${apiUrl}/triage/analyze`, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
              },
              body: JSON.stringify({
                name: formData.name,
                age: formData.age,
                gender: formData.gender,
                phone: formData.phone,
                symptoms: formData.symptoms,
                temperature: formData.temperature,
                blood_pressure: formData.bloodPressure,
                respiratory_rate: formData.respiratoryRate,
              }),
            })

            if (!response.ok) {
              throw new Error(`API Error: ${response.statusText}`)
            }

            const data = await response.json()

            // Transform API response to match expected format
            setTriageResult({
              patientId: data.patient_id,
              riskScore: data.risk_score,
              priority: data.priority,
              doctorAssignment: data.doctor_assignment,
              summary: data.summary,
              recommendations: data.recommendations,
              outbreak: data.outbreak_detected || false,
              clusterAlert: data.outbreak_detected
                ? '⚠️ Outbreak Pattern Detected: Similar symptoms cluster in current ward'
                : undefined,
            })

            // Mark all steps as complete
            setSteps(prev =>
              prev.map(step => ({
                ...step,
                status: 'complete',
              }))
            )

            setComplete(true)
          } catch (err) {
            console.error('Triage analysis error:', err)
            setError(`Triage analysis failed: ${err instanceof Error ? err.message : 'Unknown error'}`)
            // Still show a mock result for demo purposes
            setTriageResult({
              patientId: `PAT-2626-${Math.random().toString().slice(2, 6).toUpperCase()}`,
              riskScore: Math.floor(Math.random() * 100),
              priority: ['red', 'yellow', 'green'][Math.floor(Math.random() * 3)] as any,
              doctorAssignment: 'Dr. Rahul Verma',
              summary: `Patient analysis: ${formData.symptoms}`,
              recommendations: [
                'Doctor consultation required',
                'Follow-up assessment within 24 hours',
              ],
              outbreak: false,
            })
            setComplete(true)
          } finally {
            setIsLoading(false)
          }
        }, 4000)
      } catch (err) {
        console.error('Error initializing triage:', err)
        setError('Error preparing triage analysis')
        setIsLoading(false)
      }
    }

    initializeTriage()
  }, [router])

  return (
    <main className="min-h-screen py-12 px-6 bg-gradient-to-br from-slate-50 to-slate-100">
      <div className="max-w-4xl mx-auto">
        {/* Agent Progress */}
        <div className="bg-white rounded-xl shadow-elevated p-8 mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">AI Triage Analysis</h2>

          <div className="space-y-4">
            {steps.map((step, idx) => (
              <div key={idx} className="flex items-center gap-4">
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm ${
                    step.status === 'complete'
                      ? 'bg-success text-white'
                      : step.status === 'running'
                      ? 'bg-primary text-white animate-pulse'
                      : 'bg-gray-200 text-gray-600'
                  }`}
                >
                  {step.status === 'running' && <Loader2 className="w-5 h-5 animate-spin" />}
                  {step.status === 'complete' && '✓'}
                  {step.status === 'pending' && idx + 1}
                </div>
                <div className="flex-1">
                  <p className={`font-semibold ${step.status === 'running' ? 'text-primary' : 'text-gray-700'}`}>
                    {step.agent}
                  </p>
                  {step.status === 'running' && <p className="text-sm text-gray-500">Processing...</p>}
                </div>
                <span className="text-xs font-medium px-3 py-1 rounded-full bg-gray-100 text-gray-700 capitalize">
                  {step.status}
                </span>
              </div>
            ))}
          </div>

          {complete && (
            <div className="mt-6 p-4 bg-success/10 border border-success rounded-lg">
              <p className="text-success font-semibold">✓ Analysis Complete</p>
            </div>
          )}
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-danger/10 border border-danger rounded-lg p-4 mb-8">
            <p className="text-danger font-semibold">{error}</p>
          </div>
        )}

        {/* Triage Result */}
        {triageResult && (
          <div className="space-y-6">
            <TriageCard triageData={triageResult} />

            {triageResult.outbreak && triageResult.clusterAlert && (
              <div className="bg-danger/10 border-l-4 border-danger rounded-lg p-6">
                <h3 className="text-lg font-bold text-danger mb-3">⚠️ Outbreak Alert</h3>
                <p className="text-gray-700">{triageResult.clusterAlert}</p>
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex gap-4">
              <Link
                href="/dashboard"
                className="flex-1 px-6 py-3 bg-primary text-white font-bold rounded-lg hover:bg-primary/90 transition-colors text-center"
              >
                View Doctor Queue
              </Link>
              <Link
                href="/intake"
                className="flex-1 px-6 py-3 bg-gray-200 text-gray-900 font-bold rounded-lg hover:bg-gray-300 transition-colors text-center"
              >
                New Patient
              </Link>
            </div>
          </div>
        )}

        {isLoading && !triageResult && (
          <div className="text-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-primary mx-auto mb-4" />
            <p className="text-gray-600">Analyzing patient data...</p>
          </div>
        )}
      </div>
    </main>
  )
}
