import { lazy, Suspense } from 'react';
import { Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import RequireAuth from './components/RequireAuth';
import Home from './pages/Home';
import RequireAdmin from './components/RequireAdmin';

// Las páginas se descargan cuando se visitan (Home queda en la carga inicial).
const Login = lazy(() => import('./pages/Login'));
const Register = lazy(() => import('./pages/Register'));
const Profile = lazy(() => import('./pages/Profile'));
const ProfileEdit = lazy(() => import('./pages/ProfileEdit'));
const AddAnimal = lazy(() => import('./pages/AddAnimal'));
const Adoptar = lazy(() => import('./pages/Adoptar'));
const MisSolicitudes = lazy(() => import('./pages/MisSolicitudes'));
const Entrega = lazy(() => import('./pages/Entrega'));
const AdminPanel = lazy(() => import('./pages/AdminPanel'));
const About = lazy(() => import('./pages/About'));
const Contact = lazy(() => import('./pages/Contact'));

export default function App() {
  return (
    <Layout>
      <Suspense fallback={<p style={{ textAlign: 'center', padding: '2rem' }}>Cargando…</p>}>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/login" element={<Login />} />
        <Route path="/registro" element={<Register />} />
        <Route path="/nosotros" element={<About />} />
        <Route path="/contacto" element={<Contact />} />
        <Route
          path="/perfil"
          element={
            <RequireAuth>
              <Profile />
            </RequireAuth>
          }
        />
        <Route
          path="/perfil/editar"
          element={
            <RequireAuth>
              <ProfileEdit />
            </RequireAuth>
          }
        />
        <Route
          path="/registrar-animal"
          element={
            <RequireAuth>
              <AddAnimal />
            </RequireAuth>
          }
        />
        <Route path="/adoptar/:id" element={<RequireAuth><Adoptar /></RequireAuth>} />
        <Route path="/mis-solicitudes" element={<RequireAuth><MisSolicitudes /></RequireAuth>} />
        <Route path="/entrega/:solicitudId" element={<RequireAuth><Entrega /></RequireAuth>} />
        <Route path="/panel-admin" element={<RequireAdmin><AdminPanel /></RequireAdmin>} />
      </Routes>
      </Suspense>
    </Layout>
  );
}
