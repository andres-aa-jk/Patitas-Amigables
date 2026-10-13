import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAnimals } from '../context/AnimalsContext';
import LocationPickerMap from '../components/LocationPickerMap';

const initialState = {
  nombre: '',
  especie: 'perro',
  raza: '',
  edad: '',
  estado_salud: 'saludable',
  descripcion: '',
};

export default function AddAnimal() {
  const { addAnimal, ESPECIES, ESTADOS_SALUD } = useAnimals();
  const navigate = useNavigate();

  const [form, setForm] = useState(initialState);
  const [foto, setFoto] = useState(null);
  const [fotoPreview, setFotoPreview] = useState(null);
  const [coords, setCoords] = useState({ lat: null, lng: null });
  const [error, setError] = useState('');
  const [enviando, setEnviando] = useState(false);

  function handleChange(e) {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  }

  function handleFotoChange(e) {
    const file = e.target.files?.[0];
    if (file) {
      setFoto(file);
      setFotoPreview(URL.createObjectURL(file));
    }
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (coords.lat == null || coords.lng == null) {
      setError('Por favor selecciona la ubicación en el mapa antes de enviar.');
      return;
    }

    setError('');
    setEnviando(true);

    const result = await addAnimal({
      ...form,
      edad: form.edad === '' ? null : Number(form.edad),
      latitud: coords.lat,
      longitud: coords.lng,
      foto,
    });

    setEnviando(false);

    if (result.ok) {
      navigate('/perfil', { state: { aviso: result.animal.estado_publicacion === 'aprobado' ? 'Animal publicado.' : 'Animal enviado. Un administrador lo revisará antes de publicarlo en el mapa.' } });
    } else {
      setError(result.error);
    }
  }

  return (
    <div className="form-container">
      <h2>Registrar Animal</h2>
      <form onSubmit={handleSubmit}>
        {error && (
          <div className="form-group">
            <div className="errorlist">{error}</div>
          </div>
        )}

        <div className="form-group">
          <label htmlFor="nombre">Nombre (si se conoce):</label>
          <input
            id="nombre"
            name="nombre"
            className="form-control"
            type="text"
            value={form.nombre}
            onChange={handleChange}
          />
        </div>

        <div className="form-group">
          <label htmlFor="especie">Especie:</label>
          <select
            id="especie"
            name="especie"
            className="form-control"
            value={form.especie}
            onChange={handleChange}
          >
            {Object.entries(ESPECIES).map(([value, label]) => (
              <option value={value} key={value}>
                {label}
              </option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="raza">Raza (si se conoce):</label>
          <input
            id="raza"
            name="raza"
            className="form-control"
            type="text"
            value={form.raza}
            onChange={handleChange}
          />
        </div>

        <div className="form-group">
          <label htmlFor="edad">Edad aproximada:</label>
          <input
            id="edad"
            name="edad"
            className="form-control"
            type="number"
            min="0"
            value={form.edad}
            onChange={handleChange}
          />
        </div>

        <div className="form-group">
          <label htmlFor="estado_salud">Estado de salud:</label>
          <select
            id="estado_salud"
            name="estado_salud"
            className="form-control"
            value={form.estado_salud}
            onChange={handleChange}
          >
            {Object.entries(ESTADOS_SALUD).map(([value, label]) => (
              <option value={value} key={value}>
                {label}
              </option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="descripcion">Descripción:</label>
          <textarea
            id="descripcion"
            name="descripcion"
            className="form-control"
            value={form.descripcion}
            onChange={handleChange}
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="foto">Fotografía:</label>
          <input id="foto" name="foto" type="file" accept="image/*" onChange={handleFotoChange} />
          {fotoPreview && (
            <img
              src={fotoPreview}
              alt="Vista previa"
              style={{ marginTop: '0.75rem', maxWidth: 160, borderRadius: 12 }}
            />
          )}
        </div>

        <div className="form-group">
          <label>Ubicación donde se encontró:</label>
          <LocationPickerMap onSelect={(lat, lng) => setCoords({ lat, lng })} />
          <div className="location-info">
            <p>
              {coords.lat != null
                ? `Ubicación seleccionada: ${coords.lat.toFixed(5)}, ${coords.lng.toFixed(5)}`
                : 'Haz clic en el mapa para marcar la ubicación'}
            </p>
          </div>
        </div>

        <button type="submit" className="btn" disabled={enviando}>
          {enviando ? 'Registrando...' : 'Registrar Animal'}
        </button>
      </form>
    </div>
  );
}
