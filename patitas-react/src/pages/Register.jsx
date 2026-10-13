import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const initialState = {
  username: '',
  email: '',
  direccion: '',
  numero: '',
  password1: '',
  password2: '',
  acepta_politica: false,
};

export default function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState(initialState);
  const [error, setError] = useState('');
  const [enviando, setEnviando] = useState(false);

  function handleChange(e) {
    setForm((prev) => ({
      ...prev,
      [e.target.name]: e.target.type === 'checkbox' ? e.target.checked : e.target.value,
    }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setEnviando(true);
    const result = await register(form);
    setEnviando(false);
    if (result.ok) {
      navigate('/');
    } else {
      setError(result.error);
    }
  }

  return (
    <div className="form-container">
      <h2>Registro de Usuario</h2>
      <form onSubmit={handleSubmit}>
        {error && (
          <div className="alert alert-danger">
            <p>{error}</p>
          </div>
        )}
        <div className="form-group">
          <label htmlFor="username">Nombre de usuario:</label>
          <input
            id="username"
            name="username"
            className="form-control"
            type="text"
            value={form.username}
            onChange={handleChange}
            required
          />
        </div>
        <div className="form-group">
          <label htmlFor="email">Correo electrónico:</label>
          <input
            id="email"
            name="email"
            className="form-control"
            type="email"
            value={form.email}
            onChange={handleChange}
            required
          />
        </div>
        <div className="form-group">
          <label htmlFor="direccion">Dirección:</label>
          <textarea
            id="direccion"
            name="direccion"
            className="form-control"
            rows={3}
            value={form.direccion}
            onChange={handleChange}
            required
          />
        </div>
        <div className="form-group">
          <label htmlFor="numero">Número de teléfono:</label>
          <input
            id="numero"
            name="numero"
            className="form-control"
            type="text"
            maxLength={20}
            value={form.numero}
            onChange={handleChange}
            required
          />
        </div>
        <div className="form-group">
          <label htmlFor="password1">Contraseña:</label>
          <input
            id="password1"
            name="password1"
            className="form-control"
            type="password"
            value={form.password1}
            onChange={handleChange}
            required
          />
          <p className="form-text">
            Mínimo 8 caracteres, no puede ser solo números ni una contraseña común.
          </p>
        </div>
        <div className="form-group">
          <label htmlFor="password2">Confirmar contraseña:</label>
          <input
            id="password2"
            name="password2"
            className="form-control"
            type="password"
            value={form.password2}
            onChange={handleChange}
            required
          />
        </div>
        <div className="form-group">
          <label htmlFor="acepta_politica" style={{ display: 'flex', gap: '0.5rem', alignItems: 'flex-start' }}>
            <input
              id="acepta_politica"
              name="acepta_politica"
              type="checkbox"
              style={{ width: 'auto', marginTop: 4 }}
              checked={form.acepta_politica}
              onChange={handleChange}
              required
            />
            <span>
              Autorizo el tratamiento de mis datos personales (Ley 1581 de 2012) para gestionar
              adopciones. Entiendo que, por seguridad y prevención de fraude, el sistema registra
              qué fichas de animales consulto y por cuánto tiempo, y que esos registros se
              conservan 90 días.
            </span>
          </label>
        </div>
        <button type="submit" className="btn" disabled={enviando}>
          {enviando ? 'Creando cuenta...' : 'Registrarse'}
        </button>
      </form>
      <p>
        ¿Ya tienes una cuenta? <Link to="/login">Inicia sesión aquí</Link>
      </p>
    </div>
  );
}
