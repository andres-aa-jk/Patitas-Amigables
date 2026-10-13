import { Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import RequireAuth from './components/RequireAuth';
import Home from './pages/Home';
import Login from './pages/Login';
import Register from './pages/Register';
import Profile from './pages/Profile';
import ProfileEdit from './pages/ProfileEdit';
import AddAnimal from './pages/AddAnimal';
import RequireAdmin from './components/RequireAdmin';
import Adoptar from './pages/Adoptar';
import MisSolicitudes from './pages/MisSolicitudes';
import Entrega from './pages/Entrega';
import AdminPanel from './pages/AdminPanel';
import About from './pages/About';
import Contact from './pages/Contact';

export default function App() {
  return (
    <Layout>
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
    </Layout>
  );
}
