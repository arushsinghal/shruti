import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './ProtectedRoute';
import Landing from './pages/Landing';
import Dashboard from './pages/Dashboard';
import Consultation from './pages/Consultation';
import ReviewNote from './pages/ReviewNote';
import Analytics from './pages/Analytics';
import Tasks from './pages/Tasks';
import Appointments from './pages/Appointments';
import PatientProfile from './pages/PatientProfile';
import Pricing from './pages/Pricing';
import About from './pages/About';
import Research from './pages/Research';
import AssistantDashboard from './pages/AssistantDashboard';
import AssistantIntake from './pages/AssistantIntake';
import Privacy from './pages/Privacy';
import Login from './pages/Login';
import Register from './pages/Register';
import PatientPortal from './pages/PatientPortal';
import ClinicInbox from './pages/ClinicInbox';
import Signup from './pages/Signup';
import Billing from './pages/Billing';
import DocSignPage from './pages/DocSignPage';
import InvoiceView from './pages/InvoiceView';
import ReviewQueue from './pages/ReviewQueue';
import OpsDashboard from './pages/OpsDashboard';
import TPAClaim from './pages/TPAClaim';
import PreVisitForm from './pages/PreVisitForm';

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/pricing" element={<Pricing />} />
          <Route path="/about" element={<About />} />
          <Route path="/research" element={<Research />} />
          <Route path="/privacy" element={<Privacy />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/signup" element={<Signup />} />
          <Route path="/p/:phone" element={<PatientPortal />} />
          {/* No-login doctor signing page — token in URL proves identity */}
          <Route path="/sign/:token" element={<DocSignPage />} />
          {/* No-login patient pre-visit form — appointment id in URL is the access key */}
          <Route path="/pre-visit/:appointmentId" element={<PreVisitForm />} />

          <Route element={<ProtectedRoute />}>
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/assistant" element={<AssistantDashboard />} />
            <Route path="/assistant/intake" element={<AssistantIntake />} />
            <Route path="/patient/:name" element={<PatientProfile />} />
            <Route path="/consultation/:id" element={<Consultation />} />
            <Route path="/review/:id" element={<ReviewNote />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/tasks" element={<Tasks />} />
            <Route path="/appointments" element={<Appointments />} />
            <Route path="/clinic-inbox" element={<ClinicInbox />} />
            <Route path="/billing" element={<Billing />} />
            <Route path="/internal/invoices" element={<InvoiceView />} />
            <Route path="/internal/review-queue" element={<ReviewQueue />} />
            <Route path="/internal/ops" element={<OpsDashboard />} />
            <Route path="/internal/tpa/:sessionId" element={<TPAClaim />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

