import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from './context/AuthContext';

export default function ProtectedRoute() {
  const { token, user, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!token) {
    return <Navigate to="/login" replace />;
  }

  // Assistants live in /assistant but may open a note read-only via /review/:id.
  // Any other protected route (e.g. the doctor's /dashboard) bounces them home.
  const ASSISTANT_ALLOWED = ['/assistant', '/review', '/assistant/intake'];
  const isAssistant = user?.role === 'assistant';
  if (isAssistant && !ASSISTANT_ALLOWED.some(p => location.pathname.startsWith(p))) {
    return <Navigate to="/assistant" replace />;
  }

  return <Outlet />;
}
