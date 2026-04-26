'use client'

import { useState } from 'react'
import { Mic, Upload } from 'lucide-react'

interface PatientFormProps {
  onSubmit: (formData: PatientFormData) => void
}

export interface PatientFormData {
  name: string
  age: number
  gender: string
  phone: string
  symptoms: string
  temperature: number
  bloodPressure: string
  respiratoryRate: number
}

export default function PatientForm({ onSubmit }: PatientFormProps) {

  const [formData, setFormData] = useState<PatientFormData>({
    name: '',
    age: 0,
    gender: '',
    phone: '',
    symptoms: '',
    temperature: 0,
    bloodPressure: '',
    respiratoryRate: 0
  })

  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  const handleChange = (
    e: React.ChangeEvent<
      HTMLInputElement |
      HTMLTextAreaElement |
      HTMLSelectElement
    >
  ) => {

    const { name, value } = e.target

    setFormData(prev => ({
      ...prev,
      [name]:
        name === 'age' ||
        name === 'temperature' ||
        name === 'respiratoryRate'
          ? value === '' ? 0 : Number(value)
          : value
    }))
  }

  const validateForm = () => {

    if (!formData.name.trim()) {
      setError('Patient name is required')
      return false
    }

    if (formData.age <= 0 || formData.age > 150) {
      setError('Enter valid age')
      return false
    }

    if (!formData.gender) {
      setError('Select gender')
      return false
    }

    if (!formData.phone.trim()) {
      setError('Phone number required')
      return false
    }

    if (!formData.symptoms.trim()) {
      setError('Describe symptoms')
      return false
    }

    if (!formData.bloodPressure.trim()) {
      setError('Blood pressure required')
      return false
    }

    return true
  }

  const handleSubmit = async (
    e: React.FormEvent
  ) => {

    e.preventDefault()
    setError('')

    if (!validateForm()) return

    setIsLoading(true)

    try {
      onSubmit(formData)
    } catch (err) {
      console.error(err)
      setError('Submission failed')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="bg-white rounded-2xl shadow-xl p-8 space-y-8"
    >

      {error && (
        <div className="p-4 rounded-lg border bg-red-50 text-red-600">
          {error}
        </div>
      )}

      {/* Personal Info */}
      <div>
        <h3 className="text-xl font-bold mb-4">
          Patient Information
        </h3>

        <div className="grid md:grid-cols-2 gap-4">

          <input
            name="name"
            value={formData.name}
            onChange={handleChange}
            placeholder="Full Name"
            className="border rounded-lg p-3 w-full"
          />

          <input
            type="number"
            name="age"
            value={formData.age || ''}
            onChange={handleChange}
            placeholder="Age"
            className="border rounded-lg p-3 w-full"
          />

          <select
            name="gender"
            value={formData.gender}
            onChange={handleChange}
            className="border rounded-lg p-3 w-full"
          >
            <option value="">
              Select Gender
            </option>
            <option value="male">
              Male
            </option>
            <option value="female">
              Female
            </option>
            <option value="other">
              Other
            </option>
          </select>

          <input
            name="phone"
            value={formData.phone}
            onChange={handleChange}
            placeholder="+91 Phone Number"
            className="border rounded-lg p-3 w-full"
          />

        </div>
      </div>


      {/* Symptoms */}
      <div>
        <h3 className="text-xl font-bold mb-4">
          Chief Complaints
        </h3>

        <textarea
          name="symptoms"
          value={formData.symptoms}
          onChange={handleChange}
          rows={4}
          placeholder="Describe symptoms..."
          className="border rounded-lg p-3 w-full"
        />
      </div>


      {/* Vitals */}
      <div>
        <h3 className="text-xl font-bold mb-4">
          Vital Signs
        </h3>

        <div className="grid md:grid-cols-3 gap-4">

          <input
            type="number"
            step="0.1"
            name="temperature"
            value={formData.temperature || ''}
            onChange={handleChange}
            placeholder="Temperature"
            className="border rounded-lg p-3 w-full"
          />

          <input
            name="bloodPressure"
            value={formData.bloodPressure}
            onChange={handleChange}
            placeholder="120/80"
            className="border rounded-lg p-3 w-full"
          />

          <input
            type="number"
            name="respiratoryRate"
            value={formData.respiratoryRate || ''}
            onChange={handleChange}
            placeholder="Respiratory Rate"
            className="border rounded-lg p-3 w-full"
          />

        </div>
      </div>


      {/* Uploads */}
      <div className="grid md:grid-cols-2 gap-6">

        <div className="border-2 border-dashed rounded-xl p-6 text-center">
          <Upload className="mx-auto mb-3"/>
          <p className="font-medium">
            Upload Medical Images
          </p>
          <p className="text-sm text-gray-500">
            (Coming Soon)
          </p>
        </div>

        <div className="border-2 border-dashed rounded-xl p-6 text-center">
          <Mic className="mx-auto mb-3"/>
          <p className="font-medium">
            Voice Input
          </p>
          <p className="text-sm text-gray-500">
            (Coming Soon)
          </p>
        </div>

      </div>


      {/* Submit */}
      <div className="flex gap-4">

        <button
          type="submit"
          disabled={isLoading}
          className="flex-1 bg-blue-600 text-white py-3 rounded-xl font-semibold"
        >
          {isLoading
            ? 'Processing...'
            : 'Submit for Triage'}
        </button>

        <button
          type="reset"
          className="px-6 bg-gray-200 rounded-xl font-semibold"
        >
          Clear
        </button>

      </div>

      <p className="text-xs text-gray-500 text-center">
        Encrypted healthcare-safe intake.
      </p>

    </form>
  )
}