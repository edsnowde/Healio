import { Upload } from 'lucide-react'

export default function SymptomUpload() {
  return (
    <div className="flex items-center justify-center gap-3 p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-primary transition-colors cursor-pointer">
      <Upload className="w-6 h-6 text-gray-400" />
      <span className="text-sm font-medium text-gray-600">Upload Images (Coming Soon)</span>
    </div>
  )
}
