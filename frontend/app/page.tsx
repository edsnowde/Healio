'use client'

import Hero from '@/components/Hero'
import Link from 'next/link'
import { ArrowRight, Activity, Brain, BarChart3, AlertTriangle } from 'lucide-react'

export default function Home() {
  return (
    <main className="overflow-hidden">
      <Hero />
      
      {/* Features Section */}
      <section className="py-20 px-6 max-w-7xl mx-auto">
        <h2 className="text-4xl font-bold text-center mb-16">Why Healio?</h2>
        
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
          <div className="bg-white p-8 rounded-lg shadow-card hover:shadow-elevated transition-shadow">
            <Activity className="w-12 h-12 text-primary mb-4" />
            <h3 className="text-xl font-bold mb-3">Patient Intake</h3>
            <p className="text-gray-600">Streamlined digital intake forms with symptom tracking and vital signs collection</p>
          </div>
          
          <div className="bg-white p-8 rounded-lg shadow-card hover:shadow-elevated transition-shadow">
            <Brain className="w-12 h-12 text-primary mb-4" />
            <h3 className="text-xl font-bold mb-3">AI Triage</h3>
            <p className="text-gray-600">Intelligent risk assessment and prioritization powered by advanced AI agents</p>
          </div>
          
          <div className="bg-white p-8 rounded-lg shadow-card hover:shadow-elevated transition-shadow">
            <BarChart3 className="w-12 h-12 text-primary mb-4" />
            <h3 className="text-xl font-bold mb-3">Doctor Queue</h3>
            <p className="text-gray-600">Real-time priority queue management for optimal resource allocation</p>
          </div>
          
          <div className="bg-white p-8 rounded-lg shadow-card hover:shadow-elevated transition-shadow">
            <AlertTriangle className="w-12 h-12 text-danger mb-4" />
            <h3 className="text-xl font-bold mb-3">Outbreak Alert</h3>
            <p className="text-gray-600">Disease cluster detection and surveillance for public health response</p>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-6 bg-gradient-to-br from-primary to-primary/80">
        <div className="max-w-4xl mx-auto text-center text-white">
          <h2 className="text-4xl font-bold mb-6">Ready to Transform Patient Care?</h2>
          <p className="text-lg mb-8 text-green-50">Start your patient intake in seconds with our intelligent AI-powered triage system.</p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              href="/intake"
              className="inline-flex items-center justify-center px-8 py-4 bg-white text-primary font-bold rounded-lg hover:bg-green-50 transition-colors"
            >
              New Patient Intake
              <ArrowRight className="ml-2 w-5 h-5" />
            </Link>
            
            <Link
              href="/dashboard"
              className="inline-flex items-center justify-center px-8 py-4 bg-green-700 text-white font-bold rounded-lg hover:bg-green-800 transition-colors border border-green-600"
            >
              Doctor Dashboard
              <ArrowRight className="ml-2 w-5 h-5" />
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-6 bg-gray-900 text-white">
        <div className="max-w-7xl mx-auto text-center">
          <p className="text-gray-400">© 2026 Healio. AI-Powered Healthcare Systems for PHC Centers.</p>
        </div>
      </footer>
    </main>
  )
}
