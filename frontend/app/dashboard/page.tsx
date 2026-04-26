'use client'

import { useState, useEffect } from 'react'
import { collection, onSnapshot, query, orderBy, limit } from 'firebase/firestore'
import { db } from '@/lib/firebase'
import QueueBoard, { QueuePatient } from '@/components/QueueBoard'
import ClusterAlert from '@/components/ClusterAlert'
import { Activity, TrendingUp, RefreshCw, Wifi, WifiOff } from 'lucide-react'
import type { ClusterDoc } from '@/lib/api'

export default function DashboardPage() {
  const [patients,  setPatients]  = useState<QueuePatient[]>([])
  const [clusters,  setClusters]  = useState<ClusterDoc[]>([])
  const [connected, setConnected] = useState(false)
  const [loading,   setLoading]   = useState(true)
  const [lastSync,  setLastSync]  = useState<Date | null>(null)

  // ── Live listener: patient_queue/ ───────────────────────────────────────────
  useEffect(() => {
    const q = query(
      collection(db, 'patient_queue'),
      orderBy('timestamp', 'desc'),
      limit(50)
    )

    const unsub = onSnapshot(
      q,
      (snapshot) => {
        const docs: QueuePatient[] = snapshot.docs
          .map(doc => ({ id: doc.id, ...(doc.data() as Omit<QueuePatient, 'id'>) }))
          // Only show patients that haven't been completed
          .filter(p => p.status !== 'completed')

        setPatients(docs)
        setConnected(true)
        setLoading(false)
        setLastSync(new Date())
      },
      (err) => {
        console.error('[Dashboard] Firestore queue error:', err)
        setConnected(false)
        setLoading(false)
      }
    )

    return () => unsub()
  }, [])

  // ── Live listener: detected_clusters/ ───────────────────────────────────────
  useEffect(() => {
    const q = query(
      collection(db, 'detected_clusters'),
      orderBy('timestamp', 'desc'),
      limit(10)
    )

    const unsub = onSnapshot(
      q,
      (snapshot) => {
        const docs: ClusterDoc[] = snapshot.docs.map(doc => ({
          id: doc.id,
          ...(doc.data() as Omit<ClusterDoc, 'id'>),
        }))
        // Only show clusters pending verification or escalated
        setClusters(docs.filter(c => c.status !== 'resolved'))
      },
      (err) => console.error('[Dashboard] Firestore clusters error:', err)
    )

    return () => unsub()
  }, [])

  // ── Derived stats ────────────────────────────────────────────────────────────
  const stats = {
    total:    patients.length,
    red:      patients.filter(p => p.triage_color === 'Red').length,
    yellow:   patients.filter(p => p.triage_color === 'Yellow').length,
    green:    patients.filter(p => p.triage_color === 'Green').length,
    avgRisk:  patients.length
      ? Math.round(patients.reduce((s, p) => s + p.risk_score, 0) / patients.length * 100)
      : 0,
  }

  // Build cluster alert messages from Firestore data
  const clusterMessages = clusters.map(c => {
    const sym = c.symptoms?.slice(0, 3).join(', ') || 'similar symptoms'
    const flag = c.action_required ? '🚨 DHO ESCALATED — ' : ''
    return `${flag}${c.patient_count} patients with ${sym} detected in ${c.time_window_hours}h window (confidence: ${Math.round((c.confidence ?? 0) * 100)}%)`
  })

  return (
    <main className="min-h-screen py-12 px-6 bg-gradient-to-br from-slate-50 to-slate-100">
      <div className="max-w-7xl mx-auto">

        {/* Header */}
        <div className="mb-8 flex items-start justify-between">
          <div>
            <h1 className="text-4xl font-bold text-gray-900 mb-2">Doctor Dashboard</h1>
            <p className="text-gray-600">Real-time patient queue and clinical intelligence</p>
          </div>

          {/* Connection badge */}
          <div className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-semibold border
            ${connected
              ? 'bg-green-50 border-green-200 text-green-700'
              : 'bg-red-50 border-red-200 text-red-700'}`}
          >
            {connected ? <Wifi size={16} /> : <WifiOff size={16} />}
            {connected ? 'Live' : 'Reconnecting…'}
            {lastSync && (
              <span className="text-xs font-normal opacity-70">
                · {lastSync.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })}
              </span>
            )}
          </div>
        </div>

        {/* Cluster alerts from Firestore */}
        {clusterMessages.length > 0 && (
          <div className="mb-8 space-y-3">
            {clusterMessages.map((msg, i) => (
              <ClusterAlert key={i} message={msg} />
            ))}
          </div>
        )}

        {/* Stats */}
        <div className="grid md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6 border-l-4 border-emerald-500">
            <p className="text-gray-500 text-sm font-medium">Total Active</p>
            <p className="text-3xl font-bold text-gray-900">{stats.total}</p>
            <p className="text-xs text-gray-400 mt-1">Patients in queue</p>
          </div>

          <div className="bg-white rounded-lg shadow p-6 border-l-4 border-red-500">
            <p className="text-gray-500 text-sm font-medium">🔴 Red — Urgent</p>
            <p className="text-3xl font-bold text-red-600">{stats.red}</p>
            <p className="text-xs text-gray-400 mt-1">Immediate attention</p>
          </div>

          <div className="bg-white rounded-lg shadow p-6 border-l-4 border-yellow-400">
            <p className="text-gray-500 text-sm font-medium">🟡 Yellow — Moderate</p>
            <p className="text-3xl font-bold text-yellow-500">{stats.yellow}</p>
            <p className="text-xs text-gray-400 mt-1">Doctor review needed</p>
          </div>

          <div className="bg-white rounded-lg shadow p-6 border-l-4 border-green-500">
            <p className="text-gray-500 text-sm font-medium">Avg Risk Score</p>
            <p className="text-3xl font-bold text-gray-900">{stats.avgRisk}%</p>
            <p className="text-xs text-gray-400 mt-1">Across all patients</p>
          </div>
        </div>

        {/* Queue board */}
        {loading ? (
          <div className="bg-white rounded-xl shadow p-16 text-center">
            <RefreshCw className="w-10 h-10 text-emerald-500 mx-auto mb-4 animate-spin" />
            <p className="text-gray-600 font-medium">Connecting to Firestore…</p>
          </div>
        ) : (
          <QueueBoard patients={patients} />
        )}

        {/* Footer info */}
        <div className="mt-8 bg-white rounded-lg shadow p-6">
          <div className="flex gap-3 items-start">
            <TrendingUp className="w-5 h-5 text-emerald-600 flex-shrink-0 mt-1" />
            <div>
              <h3 className="font-bold text-gray-900 mb-1">Queue Insights</h3>
              <p className="text-gray-600 text-sm">
                🟢 {stats.green} routine &nbsp;|&nbsp;
                🟡 {stats.yellow} under watch &nbsp;|&nbsp;
                🔴 {stats.red} urgent &nbsp;|&nbsp;
                Firestore real-time sync active
                {clusters.length > 0 && (
                  <span className="ml-2 font-semibold text-red-600">
                    · {clusters.length} cluster alert{clusters.length > 1 ? 's' : ''} active
                  </span>
                )}
              </p>
            </div>
          </div>
        </div>

      </div>
    </main>
  )
}
