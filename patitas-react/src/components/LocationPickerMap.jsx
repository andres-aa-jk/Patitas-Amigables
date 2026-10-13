import { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

import iconRetinaUrl from 'leaflet/dist/images/marker-icon-2x.png';
import iconUrl from 'leaflet/dist/images/marker-icon.png';
import shadowUrl from 'leaflet/dist/images/marker-shadow.png';

delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({ iconRetinaUrl, iconUrl, shadowUrl });

export default function LocationPickerMap({ onSelect }) {
  const mapRef = useRef(null);
  const mapInstance = useRef(null);
  const markerRef = useRef(null);

  useEffect(() => {
    if (!mapRef.current || mapInstance.current) return;

    const map = L.map(mapRef.current).setView([4.7059, -74.2309], 13);
    mapInstance.current = map;

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors',
    }).addTo(map);

    map.on('click', (e) => {
      if (markerRef.current) map.removeLayer(markerRef.current);
      markerRef.current = L.marker(e.latlng).addTo(map);
      onSelect(e.latlng.lat, e.latlng.lng);
    });

    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition((position) => {
        if (!activo) return;
        const { latitude: lat, longitude: lng } = position.coords;
        map.setView([lat, lng], 15);
      });
    }

    // El temporizador se cancela al desmontar: si no, Leaflet falla al operar sobre un mapa eliminado.
    let activo = true;
    const temporizador = setTimeout(() => activo && map.invalidateSize(), 250);

    return () => {
      activo = false;
      clearTimeout(temporizador);
      map.stop();
      map.remove();
      mapInstance.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return <div id="map" className="picker-map" ref={mapRef}></div>;
}
