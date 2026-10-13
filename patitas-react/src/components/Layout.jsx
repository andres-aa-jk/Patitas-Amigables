import { useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Layout({ children }) {
  const [menuOpen, setMenuOpen] = useState(false);
  const { isAuthenticated, isAdmin, logout } = useAuth();
  const navigate = useNavigate();

  function closeMenu() {
    setMenuOpen(false);
  }

  function handleLogout(e) {
    e.preventDefault();
    logout();
    closeMenu();
    navigate('/');
  }

  return (
    <>
      <div className="app-bg" />
      <nav className="navbar">
        <div className="logo-container">
          <NavLink to="/" onClick={closeMenu}>
            <img src="/images/logo.png" alt="Patitas Amigables" className="logo" />
          </NavLink>
        </div>
        <button
          className={`hamburger ${menuOpen ? 'active' : ''}`}
          aria-label="Menu"
          onClick={() => setMenuOpen((v) => !v)}
        >
          <span></span>
          <span></span>
          <span></span>
        </button>
        <ul className={`nav-links ${menuOpen ? 'active' : ''}`}>
          {isAuthenticated ? (
            <>
              <li>
                <NavLink to="/" end onClick={closeMenu}>
                  <i className="fas fa-home"></i>&nbsp; Inicio
                </NavLink>
              </li>
              <li>
                <NavLink to="/perfil" onClick={closeMenu}>
                  <i className="fas fa-user"></i>&nbsp; Perfil
                </NavLink>
              </li>
              <li>
                <NavLink to="/registrar-animal" onClick={closeMenu}>
                  <i className="fas fa-paw"></i>&nbsp; Registrar Animal
                </NavLink>
              </li>
              <li>
                <NavLink to="/mis-solicitudes" onClick={closeMenu}>
                  <i className="fas fa-clipboard-list"></i>&nbsp; Mis solicitudes
                </NavLink>
              </li>
              {isAdmin && (
                <li>
                  <NavLink to="/panel-admin" onClick={closeMenu}>
                    <i className="fas fa-user-shield"></i>&nbsp; Panel admin
                  </NavLink>
                </li>
              )}
              <li>
                <NavLink to="/nosotros" onClick={closeMenu}>
                  <i className="fas fa-info-circle"></i>&nbsp; ¿Quienes somos?
                </NavLink>
              </li>
              <li>
                <NavLink to="/contacto" onClick={closeMenu}>
                  <i className="fas fa-envelope"></i>&nbsp; Contáctanos
                </NavLink>
              </li>
              <li>
                <a href="#">
                  <i className="fas fa-heart"></i>&nbsp; Donaciones
                </a>
              </li>
              <li>
                <button type="button" className="nav-logout" onClick={handleLogout}>
                  <i className="fas fa-sign-out-alt"></i>&nbsp; Cerrar Sesión
                </button>
              </li>
            </>
          ) : (
            <>
              <li>
                <NavLink
                  to="/login"
                  className={({ isActive }) => `login-btn${isActive ? ' active' : ''}`}
                  onClick={closeMenu}
                >
                  <i className="fas fa-sign-in-alt"></i>&nbsp; Iniciar sesión
                </NavLink>
              </li>
              <li>
                <NavLink to="/registro" onClick={closeMenu}>
                  <i className="fas fa-user-plus"></i>&nbsp; Registrarse
                </NavLink>
              </li>
              <li>
                <NavLink to="/nosotros" onClick={closeMenu}>
                  <i className="fas fa-info-circle"></i>&nbsp; ¿Quienes somos?
                </NavLink>
              </li>
              <li>
                <NavLink to="/contacto" onClick={closeMenu}>
                  <i className="fas fa-envelope"></i>&nbsp; Contáctanos
                </NavLink>
              </li>
              <li>
                <a href="#">
                  <i className="fas fa-heart"></i>&nbsp; Donaciones
                </a>
              </li>
            </>
          )}
        </ul>
      </nav>

      <main className="main-content">
        {children}
        <div className={`menu-overlay ${menuOpen ? 'active' : ''}`} onClick={closeMenu} />
        <footer>
          <center>
            <p>&copy; 2025 Patitas Amigables. Todos los derechos reservados.</p>
          </center>
        </footer>
      </main>
    </>
  );
}
