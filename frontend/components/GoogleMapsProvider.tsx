import { useJsApiLoader } from '@react-google-maps/api'
import { ReactNode } from 'react'

interface GoogleMapsProviderProps {
  children: ReactNode
}

export function GoogleMapsProvider({ children }: GoogleMapsProviderProps) {
  const { isLoaded, loadError } = useJsApiLoader({
    googleMapsApiKey: process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY || '',
    libraries: ['places', 'drawing'],
  })

  if (loadError) {
    return (
      <div className="w-full h-full bg-red-50 rounded-xl flex items-center justify-center border-2 border-red-200">
        <div className="text-center p-6">
          <p className="text-red-700 font-bold mb-2">⚠️ Map Failed to Load</p>
          <p className="text-red-600 text-sm">
            Google Maps API key not configured. 
          </p>
          <p className="text-red-600 text-sm mt-1">
            Add <code className="bg-red-100 px-2 py-1 rounded">NEXT_PUBLIC_GOOGLE_MAPS_API_KEY</code> to <code className="bg-red-100 px-2 py-1 rounded">.env.local</code>
          </p>
        </div>
      </div>
    )
  }

  if (!isLoaded) {
    return (
      <div className="w-full h-full bg-gray-100 rounded-xl flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-4 border-blue-500 border-t-transparent mx-auto mb-4"></div>
          <p className="text-gray-600">Loading map...</p>
        </div>
      </div>
    )
  }

  return <>{children}</>
}

export function useGoogleMapsLoaded() {
  const { isLoaded, loadError } = useJsApiLoader({
    googleMapsApiKey: process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY || '',
    libraries: ['places', 'drawing'],
  })

  return { isLoaded, loadError }
}
