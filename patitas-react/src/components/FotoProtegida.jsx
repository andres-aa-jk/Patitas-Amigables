import { useEffect, useState } from 'react';
import { apiBlobUrl } from '../api/client';

/** Muestra una imagen que exige sesión (la foto de entrega no es pública). */
export default function FotoProtegida({ entregaId, alt = 'Foto de la entrega' }) {
  const [src, setSrc] = useState(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    let url = null;
    let activo = true;
    apiBlobUrl(`/entregas/${entregaId}/foto/`)
      .then((u) => {
        url = u;
        if (activo) setSrc(u);
      })
      .catch(() => activo && setError(true));
    return () => {
      activo = false;
      if (url) URL.revokeObjectURL(url);
    };
  }, [entregaId]);

  if (error) return <p className="form-text">No se pudo cargar la foto.</p>;
  if (!src) return <p className="form-text">Cargando foto...</p>;
  return <img className="thumb" loading="lazy" src={src} alt={alt} />;
}
