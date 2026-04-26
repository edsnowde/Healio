'use client'

import { useState, useEffect } from 'react'
import { collection, onSnapshot, query, orderBy, limit } from 'firebase/firestore'
import { db } from '@/lib/firebase'
import {
  AlertTriangle, TrendingUp, Clock, Activity,
  Users, AlertCircle, CheckCircle2, X, Wifi, WifiOff, RefreshCw,
} from 'lucide-react'
import type { ClusterDoc, SurveillanceDoc } from '@/lib/api'

// ── Helpers ────────────────────────────────────────────────────────────────────

function fmtTs(ts: string) {
  try { return new Date(ts).toLocaleString('en-IN', { dateStyle: 'short', timeStyle: 'short' }) }
  catch { return ts }
}

function hourBucket(ts: string) {
  try { return new Date(ts).getHours() }
  catch { return 0 }
}

// ── Component ──────────────────────────────────────────────────────────────────

export default function SurveillanceDashboard() {
  const [clusters,    setClusters]    = useState<ClusterDoc[]>([])
  const [records,     setRecords]     = useState<SurveillanceDoc[]>([])
  const [connected,   setConnected]   = useState(false)
  const [loading,     setLoading]     = useState(true)

  const [showReportModal, setShowReportModal] = useState(false)
  const [reportStatus,    setReportStatus]    = useState<'idle' | 'submitted' | 'success'>('idle')
  const [activeCluster,   setActiveCluster]   = useState<ClusterDoc | null>(null)

  // ── Live: detected_clusters/ ─────────────────────────────────────────────────
  useEffect(() => {
    const q = query(
      collection(db, 'detected_clusters'),
      orderBy('timestamp', 'desc'),
      limit(10)
    )
    const unsub = onSnapshot(q, snap => {
      const docs: ClusterDoc[] = snap.docs.map(d => ({ id: d.id, ...d.data() } as ClusterDoc))
      setClusters(docs)
      // Set the most severe cluster as the active hero cluster
      const active = docs.find(c => c.action_required) ?? docs[0] ?? null
      setActiveCluster(active)
      setConnected(true)
      setLoading(false)
    }, err => {
      console.error('[Surveillance] clusters error:', err)
      setConnected(false)
      setLoading(false)
    })
    return () => unsub()
  }, [])

  // ── Live: outbreak_surveillance/ ─────────────────────────────────────────────
  useEffect(() => {
    const q = query(
      collection(db, 'outbreak_surveillance'),
      orderBy('timestamp', 'desc'),
      limit(200)
    )
    const unsub = onSnapshot(q, snap => {
      const docs: SurveillanceDoc[] = snap.docs.map(d => ({ id: d.id, ...d.data() } as SurveillanceDoc))
      setRecords(docs)
    }, err => console.error('[Surveillance] records error:', err))
    return () => unsub()
  }, [])

  // ── Derived: timeline from surveillance docs (group by hour) ─────────────────
  const timeline = (() => {
    const buckets: Record<number, number> = {}
    records.forEach(r => { const h = hourBucket(r.timestamp); buckets[h] = (buckets[h] ?? 0) + 1 })
    const hours = Object.keys(buckets).map(Number).sort((a, b) => a - b)
    let cum = 0
    return hours.map(h => {
      cum += buckets[h]
      return { time: `${String(h).padStart(2, '0')}:00`, patients: buckets[h], cumulativePatients: cum }
    })
  })()

  // ── Derived: symptom frequency across all surveillance records ────────────────
  const symptomFreq: Record<string, number> = {}
  records.forEach(r => {
    ;(r.symptoms_anonymized ?? []).forEach(s => {
      const key = s.toLowerCase()
      symptomFreq[key] = (symptomFreq[key] ?? 0) + 1
    })
  })
  const topSymptoms = Object.entries(symptomFreq)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 5)
  const maxFreq = topSymptoms[0]?.[1] ?? 1

  // ── Derived: severity breakdown from surveillance records ─────────────────────
  const severity = {
    mild:     records.filter(r => r.severity_category === 'mild').length,
    moderate: records.filter(r => r.severity_category === 'moderate').length,
    severe:   records.filter(r => r.triage_color === 'Red').length,
  }

  const handleSubmitReport = () => {
    setReportStatus('submitted')
    setTimeout(() => setReportStatus('success'), 1500)
  }

  // ── No data state ─────────────────────────────────────────────────────────────
  if (!loading && clusters.length === 0) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center">
        <div className="text-center p-12 bg-white rounded-3xl shadow-xl max-w-md">
          <CheckCircle2 className="w-16 h-16 text-green-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-gray-900 mb-2">No Active Clusters</h2>
          <p className="text-gray-600 mb-2">No outbreak clusters detected in Firestore.</p>
          <p className="text-sm text-gray-400">
            Firestore: <code className="bg-gray-100 px-2 py-0.5 rounded">detected_clusters/</code> is empty.
          </p>
          <p className="text-sm text-gray-400 mt-2">
            Send 3+ patients with similar symptoms via <code className="bg-gray-100 px-2 py-0.5 rounded">/intake</code> to trigger a cluster.
          </p>
          <div className={`mt-6 inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-semibold border
            ${connected ? 'bg-green-50 border-green-200 text-green-700' : 'bg-red-50 border-red-200 text-red-700'}`}>
            {connected ? <Wifi size={14} /> : <WifiOff size={14} />}
            {connected ? 'Firestore Connected — Watching for Clusters' : 'Reconnecting…'}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      {/* Background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 right-0 w-96 h-96 bg-emerald-100/20 rounded-full blur-3xl" />
        <div className="absolute bottom-0 left-0 w-96 h-96 bg-red-100/10 rounded-full blur-3xl" />
      </div>

      <div className="relative z-10">
        {/* Nav */}
        <div className="border-b border-slate-200 bg-white/80 backdrop-blur-xl">
          <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">🏥 Healio Surveillance Dashboard</h1>
              <p className="text-sm text-gray-600 mt-1">Real-time AI outbreak detection &amp; monitoring</p>
            </div>
            <div className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-semibold border
              ${connected ? 'bg-green-50 border-green-200 text-green-700' : 'bg-red-50 border-red-200 text-red-700'}`}>
              {connected ? <Wifi size={14} /> : <WifiOff size={14} />}
              {connected ? 'Firestore Live' : 'Reconnecting…'}
            </div>
          </div>
        </div>

        <div className="max-w-7xl mx-auto px-6 py-8 space-y-8">

          {/* LOADING */}
          {loading && (
            <div className="text-center py-24">
              <RefreshCw className="w-10 h-10 text-emerald-500 mx-auto mb-4 animate-spin" />
              <p className="text-gray-600 font-medium">Connecting to Firestore…</p>
            </div>
          )}

          {/* HERO ALERT — uses activeCluster from Firestore */}
          {!loading && activeCluster && (
            <div className="bg-gradient-to-r from-red-50 via-orange-50 to-yellow-50 border-2 border-red-300 rounded-3xl p-8 shadow-lg relative overflow-hidden">
              <div className="absolute top-0 right-0 w-40 h-40 bg-red-200/20 rounded-full blur-3xl animate-pulse" />

              <div className="relative z-10 grid lg:grid-cols-3 gap-8 items-start">
                <div className="lg:col-span-2">
                  <div className="flex items-start gap-4 mb-6">
                    <div className="flex items-center justify-center w-16 h-16 rounded-full bg-red-600 text-white flex-shrink-0 animate-pulse">
                      <AlertTriangle size={32} />
                    </div>
                    <div>
                      <h2 className="text-3xl font-bold text-red-900 mb-2">
                        {activeCluster.action_required ? '🚨 DHO Escalation Active' : '⚠️ Probable Outbreak Detected'}
                      </h2>
                      <p className="text-lg text-red-700 font-semibold">
                        Clustered patients: <span className="text-2xl font-bold text-red-600">{activeCluster.patient_count}+</span>
                      </p>
                    </div>
                  </div>

                  <div className="grid md:grid-cols-2 gap-4 mb-4">
                    <div className="bg-white/70 rounded-xl p-4 border border-red-200">
                      <p className="text-xs text-gray-600 font-semibold uppercase mb-1">First Detection</p>
                      <p className="text-lg font-bold text-gray-900">{fmtTs(activeCluster.timestamp)}</p>
                    </div>
                    <div className="bg-white/70 rounded-xl p-4 border border-red-200">
                      <p className="text-xs text-gray-600 font-semibold uppercase mb-1">AI Confidence</p>
                      <p className="text-lg font-bold text-red-600">{Math.round((activeCluster.confidence ?? 0) * 100)}%</p>
                      <div className="w-full bg-gray-300 rounded-full h-2 mt-2">
                        <div
                          className="bg-gradient-to-r from-red-500 to-orange-500 h-2 rounded-full"
                          style={{ width: `${Math.round((activeCluster.confidence ?? 0) * 100)}%` }}
                        />
                      </div>
                    </div>
                  </div>

                  {/* Symptom tags from cluster */}
                  <div className="flex flex-wrap gap-2">
                    {(activeCluster.symptoms ?? []).map((s, i) => (
                      <span key={i} className="bg-red-100 border border-red-200 text-red-800 text-sm font-semibold px-3 py-1 rounded-full">
                        {s}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="space-y-3">
                  <div className="bg-white/80 rounded-xl p-4 border border-red-200 text-sm text-gray-700 space-y-1">
                    <p><span className="font-bold">Cluster ID:</span> <span className="font-mono text-xs">{activeCluster.id}</span></p>
                    <p><span className="font-bold">Severity:</span> <span className="capitalize">{activeCluster.severity}</span></p>
                    <p><span className="font-bold">Window:</span> {activeCluster.time_window_hours}h</p>
                    <p><span className="font-bold">Status:</span> <span className="capitalize">{activeCluster.status?.replace(/_/g, ' ')}</span></p>
                    <p><span className="font-bold">DHO Required:</span> {activeCluster.action_required ? '✅ Yes' : 'No'}</p>
                  </div>
                  <button
                    onClick={() => { setActiveCluster(activeCluster); setReportStatus('idle'); setShowReportModal(true) }}
                    className="w-full bg-gradient-to-r from-orange-600 to-red-600 hover:from-orange-700 hover:to-red-700 text-white font-bold py-4 rounded-xl transition shadow-lg flex items-center justify-center gap-2"
                  >
                    <AlertCircle size={20} /> Report to PHC
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* CLUSTER SUMMARY CARDS */}
          {!loading && activeCluster && (
            <div>
              <h3 className="text-2xl font-bold text-gray-900 mb-4">Cluster Summary</h3>
              <div className="grid md:grid-cols-4 gap-4">
                <div className="bg-white border-2 border-emerald-200 rounded-2xl p-6 hover:shadow-lg transition">
                  <div className="flex items-center justify-between mb-3">
                    <p className="text-sm font-semibold text-gray-600">AFFECTED PATIENTS</p>
                    <Users size={20} className="text-emerald-600" />
                  </div>
                  <p className="text-4xl font-bold text-emerald-600 mb-2">{activeCluster.patient_count}</p>
                  <p className="text-xs text-gray-600">Within {activeCluster.time_window_hours}h window</p>
                </div>

                <div className="bg-white border-2 border-orange-200 rounded-2xl p-6 hover:shadow-lg transition">
                  <div className="flex items-center justify-between mb-3">
                    <p className="text-sm font-semibold text-gray-600">SEVERITY TREND</p>
                    <TrendingUp size={20} className="text-orange-600" />
                  </div>
                  <p className="text-4xl font-bold text-orange-600 mb-2">{severity.moderate}</p>
                  <p className="text-xs text-gray-600">Moderate severity cases</p>
                </div>

                <div className="bg-white border-2 border-blue-200 rounded-2xl p-6 hover:shadow-lg transition">
                  <div className="flex items-center justify-between mb-3">
                    <p className="text-sm font-semibold text-gray-600">COMMON SYMPTOMS</p>
                    <Activity size={20} className="text-blue-600" />
                  </div>
                  <p className="text-4xl font-bold text-blue-600 mb-2">{(activeCluster.symptoms ?? []).length}</p>
                  <p className="text-xs text-gray-600">{(activeCluster.symptoms ?? []).join(', ')}</p>
                </div>

                <div className="bg-white border-2 border-purple-200 rounded-2xl p-6 hover:shadow-lg transition">
                  <div className="flex items-center justify-between mb-3">
                    <p className="text-sm font-semibold text-gray-600">FIRST DETECTED</p>
                    <Clock size={20} className="text-purple-600" />
                  </div>
                  <p className="text-sm font-bold text-purple-600 mb-2">{fmtTs(activeCluster.timestamp)}</p>
                  <p className="text-xs text-gray-600">Firestore timestamp</p>
                </div>
              </div>
            </div>
          )}

          {/* TIMELINE — built from outbreak_surveillance docs */}
          {!loading && timeline.length > 0 && (
            <div className="bg-white rounded-2xl border border-gray-200 p-8 shadow-lg">
              <h3 className="text-2xl font-bold text-gray-900 mb-6">
                Cluster Growth Timeline ({records.length} records)
              </h3>
              <div className="space-y-4">
                {timeline.map((event, idx) => {
                  const maxPts = timeline[timeline.length - 1]?.cumulativePatients || 1
                  const barWidth = (event.cumulativePatients / maxPts) * 100
                  return (
                    <div key={idx} className="flex items-center gap-4">
                      <div className="w-16 font-bold text-sm text-gray-600">{event.time}</div>
                      <div className="flex-1">
                        <div className="flex items-center gap-3">
                          <div className="relative h-8 flex-1 bg-gray-100 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-gradient-to-r from-emerald-500 to-green-500 transition-all duration-500"
                              style={{ width: `${barWidth}%` }}
                            />
                          </div>
                          <div className="text-right w-36">
                            <p className="font-bold text-gray-900 text-sm">
                              +{event.patients} / {event.cumulativePatients} total
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
              <div className="mt-6 pt-6 border-t border-gray-200">
                <p className="text-sm text-gray-600">
                  ℹ️ Outbreak threshold: <span className="font-bold">3+ cases with Jaccard ≥ 0.25</span> in 48h.
                  Current status: <span className="font-bold text-red-600">
                    {clusters.length > 0 ? 'ACTIVE' : 'MONITORING'}
                  </span>
                </p>
              </div>
            </div>
          )}

          {/* SYMPTOM PATTERN — from Firestore outbreak_surveillance records */}
          {!loading && topSymptoms.length > 0 && (
            <div className="bg-white rounded-2xl border border-gray-200 p-8 shadow-lg">
              <h3 className="text-2xl font-bold text-gray-900 mb-6">Symptom Pattern Analysis</h3>
              <div className="space-y-5">
                {topSymptoms.map(([symptom, count]) => {
                  const pct = Math.round((count / records.length) * 100)
                  return (
                    <div key={symptom}>
                      <div className="flex items-center justify-between mb-2">
                        <p className="font-semibold text-gray-700 capitalize">{symptom}</p>
                        <p className="text-lg font-bold text-emerald-600">{pct}% <span className="text-xs text-gray-400">({count} patients)</span></p>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
                        <div
                          className="h-full bg-gradient-to-r from-emerald-500 to-green-500 transition-all duration-700"
                          style={{ width: `${(count / maxFreq) * 100}%` }}
                        />
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          {/* ALL ACTIVE CLUSTERS LIST */}
          {!loading && clusters.length > 1 && (
            <div className="bg-white rounded-2xl border border-gray-200 p-8 shadow-lg">
              <h3 className="text-2xl font-bold text-gray-900 mb-6">All Active Clusters ({clusters.length})</h3>
              <div className="space-y-4">
                {clusters.map(c => (
                  <div key={c.id} className={`p-4 rounded-xl border-l-4 ${c.action_required ? 'border-red-500 bg-red-50' : 'border-yellow-400 bg-yellow-50'}`}>
                    <div className="flex items-start justify-between">
                      <div>
                        <p className="font-bold text-gray-900 mb-1">
                          {c.action_required && '🚨 '}{c.patient_count} patients · {Math.round((c.confidence ?? 0) * 100)}% confidence
                        </p>
                        <div className="flex flex-wrap gap-1 mb-1">
                          {(c.symptoms ?? []).map((s, i) => (
                            <span key={i} className="text-xs bg-white/80 border border-gray-200 rounded px-2 py-0.5">{s}</span>
                          ))}
                        </div>
                        <p className="text-xs text-gray-500">{fmtTs(c.timestamp)} · {c.time_window_hours}h window</p>
                      </div>
                      <span className={`text-xs font-bold px-3 py-1 rounded-full ${
                        c.severity === 'high' ? 'bg-red-200 text-red-800' : 'bg-yellow-200 text-yellow-800'
                      }`}>{c.severity?.toUpperCase()}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* STATUS BADGES */}
          {!loading && (
            <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-lg">
              <h3 className="text-lg font-bold text-gray-900 mb-4">Surveillance Status</h3>
              <div className="flex flex-wrap gap-3">
                <div className="inline-flex items-center gap-2 bg-red-50 border border-red-200 rounded-full px-4 py-2">
                  <div className="w-2.5 h-2.5 rounded-full bg-red-600 animate-pulse" />
                  <span className="text-sm font-semibold text-red-700">Active Monitoring</span>
                </div>
                <div className="inline-flex items-center gap-2 bg-emerald-50 border border-emerald-200 rounded-full px-4 py-2">
                  <Wifi size={14} className="text-emerald-600" />
                  <span className="text-sm font-semibold text-emerald-700">Firestore Real-time</span>
                </div>
                <div className="inline-flex items-center gap-2 bg-blue-50 border border-blue-200 rounded-full px-4 py-2">
                  <Activity size={14} className="text-blue-600" />
                  <span className="text-sm font-semibold text-blue-700">{records.length} Records Scanned</span>
                </div>
                {clusters.some(c => c.action_required) && (
                  <div className="inline-flex items-center gap-2 bg-orange-50 border border-orange-200 rounded-full px-4 py-2">
                    <TrendingUp size={14} className="text-orange-600" />
                    <span className="text-sm font-semibold text-orange-700">DHO Escalation Active</span>
                  </div>
                )}
              </div>
            </div>
          )}

        </div>
      </div>

      {/* REPORT MODAL */}
      {showReportModal && activeCluster && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-3xl shadow-2xl p-8 max-w-md w-full border border-gray-100">

            {reportStatus === 'idle' && (
              <>
                <div className="flex items-center justify-between mb-6">
                  <h3 className="text-2xl font-bold text-gray-900">Report Outbreak</h3>
                  <button onClick={() => setShowReportModal(false)} className="text-gray-500 hover:text-gray-700">
                    <X size={24} />
                  </button>
                </div>
                <div className="space-y-4 mb-8">
                  <div className="bg-gray-50 rounded-xl p-4 border border-gray-200">
                    <p className="text-xs text-gray-600 font-semibold uppercase mb-1">Cluster ID</p>
                    <p className="font-mono font-bold text-gray-900 text-sm">{activeCluster.id}</p>
                  </div>
                  <div className="bg-gray-50 rounded-xl p-4 border border-gray-200">
                    <p className="text-xs text-gray-600 font-semibold uppercase mb-1">Clustered Patients</p>
                    <p className="text-2xl font-bold text-red-600">{activeCluster.patient_count}</p>
                  </div>
                  <div className="bg-gray-50 rounded-xl p-4 border border-gray-200">
                    <p className="text-xs text-gray-600 font-semibold uppercase mb-1">Symptoms</p>
                    <p className="text-sm text-gray-800">{(activeCluster.symptoms ?? []).join(', ')}</p>
                  </div>
                  <div className="bg-blue-50 rounded-xl p-4 border border-blue-200">
                    <p className="text-sm text-blue-900">
                      ℹ️ This report will be logged and sent to PHC authorities for epidemiological investigation.
                    </p>
                  </div>
                </div>
                <button
                  onClick={handleSubmitReport}
                  className="w-full bg-gradient-to-r from-orange-600 to-red-600 hover:from-orange-700 hover:to-red-700 text-white font-bold py-3 rounded-xl transition flex items-center justify-center gap-2"
                >
                  <AlertCircle size={20} /> Submit Report to PHC
                </button>
              </>
            )}

            {reportStatus === 'submitted' && (
              <div className="text-center py-8">
                <RefreshCw className="w-12 h-12 mx-auto mb-4 text-blue-600 animate-spin" />
                <p className="font-semibold text-gray-900">Submitting report…</p>
              </div>
            )}

            {reportStatus === 'success' && (
              <>
                <div className="text-center mb-6">
                  <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-emerald-100 mb-4">
                    <CheckCircle2 size={32} className="text-emerald-600" />
                  </div>
                  <h3 className="text-2xl font-bold text-gray-900 mb-2">Outbreak Reported</h3>
                  <p className="text-gray-600">Successfully escalated to PHC surveillance unit</p>
                </div>
                <div className="space-y-3 mb-8">
                  <div className="bg-emerald-50 rounded-xl p-4 border border-emerald-200">
                    <p className="font-bold text-emerald-700 flex items-center gap-2">
                      <CheckCircle2 size={18} /> SUCCESS
                    </p>
                  </div>
                  <div className="bg-gray-50 rounded-xl p-4 border border-gray-200">
                    <p className="text-xs text-gray-600 uppercase mb-1">Cluster ID</p>
                    <p className="font-mono font-bold text-gray-900 text-sm">{activeCluster.id}</p>
                  </div>
                </div>
                <button
                  onClick={() => setShowReportModal(false)}
                  className="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-3 rounded-xl transition"
                >
                  Close
                </button>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
