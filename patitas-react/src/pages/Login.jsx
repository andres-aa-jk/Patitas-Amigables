import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [enviando, setEnviando] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setEnviando(true);
    const result = await login(username, password);
    setEnviando(false);
    if (result.ok) {
      navigate('/');
    } else {
      setError(result.error);
    }
  }

  return (
    <div className="form-container">
      <h2>Iniciar Sesión</h2>
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
            className="form-control"
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
          />
        </div>
        <div className="form-group">
          <label htmlFor="password">Contraseña:</label>
          <input
            id="password"
            className="form-control"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>
        <button type="submit" className="btn" disabled={enviando}>
          {enviando ? 'Entrando...' : 'Iniciar Sesión'}
        </button>
      </form>
      <p>
        ¿No tienes una cuenta? <Link to="/registro">Regístrate aquí</Link>
      </p>
    </div>
  );
}
