import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function RequireAuth({ children }) {
  const { isAuthenticated, loading } = useAuth();

  // Evita redirigir al login mientras se verifica el token guardado.
  if (loading) {
    return (
      <center>
        <div className="empty-state">
          <h2>Cargando...</h2>
        </div>
      </center>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  return children;
}
