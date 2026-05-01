import { GoogleMap, Marker, InfoWindow } from '@react-google-maps/api'
import { useCallback, useState } from 'react'
import type { ClusterDoc } from '@/lib/api'

interface ClusterMapProps {
  clusters: ClusterDoc[]
  isLoaded: boolean
}

export default function ClusterMap({ clusters, isLoaded }: ClusterMapProps) {
  const [selectedMarker, setSelectedMarker] = useState<ClusterDoc | null>(null)

  const mapCenter = {
    lat: 13.0827,
    lng: 77.5933,
  }

  const mapOptions = {
    zoom: 11,
    mapTypeId: 'roadmap' as const,
    zoomControl: true,
    fullscreenControl: true,
    streetViewControl: false,
    mapTypeControl: true,
  }

  const handleMarkerClick = useCallback((cluster: ClusterDoc) => {
    setSelectedMarker(cluster)
  }, [])

  const getMarkerIcon = (cluster: ClusterDoc) => {
    const isHighSeverity = cluster.action_required
    const fillColor = isHighSeverity ? '%23dc2626' : '%23f97316'
    const strokeColor = isHighSeverity ? '%23991b1b' : '%23ea580c'
    
    return {
      url: `data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 40 40'%3E%3Ccircle cx='20' cy='20' r='18' fill='${fillColor}' opacity='0.9'/%3E%3Ccircle cx='20' cy='20' r='18' fill='none' stroke='${strokeColor}' stroke-width='2'/%3E%3Ctext x='20' y='28' font-size='20' font-weight='bold' text-anchor='middle' fill='white'%3E${cluster.patient_count}%3C/text%3E%3C/svg%3E`,
      scaledSize: typeof window !== 'undefined' && window.google?.maps?.Size 
        ? new window.google.maps.Size(40, 40)
        : undefined,
      anchor: typeof window !== 'undefined' && window.google?.maps?.Point
        ? new window.google.maps.Point(20, 20)
        : undefined,
    }
  }

  if (!isLoaded) {
    return (
      <div className="w-full h-full bg-gray-100 rounded-xl flex items-center justify-center">
        <p className="text-gray-600">Loading map...</p>
      </div>
    )
  }

  return (
    <GoogleMap
      mapContainerStyle={{ width: '100%', height: '100%' }}
      center={mapCenter}
      zoom={mapOptions.zoom}
      options={mapOptions}
    >
      {clusters.map(cluster => {
        const lat = cluster.latitude || 13.0827
        const lng = cluster.longitude || 77.5933

        return (
          <Marker
            key={cluster.id}
            position={{ lat, lng }}
            onClick={() => handleMarkerClick(cluster)}
            title={`${cluster.patient_count} patients`}
            icon={getMarkerIcon(cluster)}
          >
            {selectedMarker?.id === cluster.id && (
              <InfoWindow onCloseClick={() => setSelectedMarker(null)}>
                <div className="p-2 max-w-xs">
                  <p className="font-bold text-gray-900">{cluster.patient_count} patients</p>
                  <p className="text-sm text-gray-600">
                    {(cluster.symptoms || []).join(', ') || 'No symptoms recorded'}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    Confidence: {Math.round((cluster.confidence || 0) * 100)}%
                  </p>
                  <p className={`text-xs font-bold mt-1 ${
                    cluster.action_required ? 'text-red-600' : 'text-orange-600'
                  }`}>
                    {cluster.action_required ? '🚨 Requires Action' : '⚠️ Medium Priority'}
                  </p>
                </div>
              </InfoWindow>
            )}
          </Marker>
        )
      })}
    </GoogleMap>
  )
}
