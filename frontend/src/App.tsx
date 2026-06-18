import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './ProtectedRoute';
import Landing from './pages/Landing';
import Dashboard from './pages/Dashboard';
import Consultation from './pages/Consultation';
import ReviewNote from './pages/ReviewNote';
import Analytics from './pages/Analytics';
import About from './pages/About';
import Privacy from './pages/Privacy';
import Login from './pages/Login';
import Register from './pages/Register';

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/about" element={<About />} />
          <Route path="/privacy" element={<Privacy />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          
          <Route element={<ProtectedRoute />}>
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/consultation/:id" element={<Consultation />} />
            <Route path="/review/:id" element={<ReviewNote />} />
            <Route path="/analytics" element={<Analytics />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

