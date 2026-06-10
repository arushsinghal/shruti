import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Landing from './pages/Landing';
import Dashboard from './pages/Dashboard';
import Consultation from './pages/Consultation';
import ReviewNote from './pages/ReviewNote';
import Analytics from './pages/Analytics';
import About from './pages/About';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/consultation/:id" element={<Consultation />} />
        <Route path="/review/:id" element={<ReviewNote />} />
        <Route path="/analytics" element={<Analytics />} />
        <Route path="/about" element={<About />} />
      </Routes>
    </BrowserRouter>
  );
}

