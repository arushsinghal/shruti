import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import api from '../lib/api';

export default function Register() {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);
    try {
      await api.post('/auth/register', { username, email, password, full_name: fullName });
      navigate('/login');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error registering account');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0B0F19] flex flex-col justify-center py-12 sm:px-6 lg:px-8 relative overflow-hidden text-gray-200">
      {/* Background blobs */}
      <div className="absolute top-0 left-0 w-full h-full overflow-hidden -z-10 pointer-events-none">
        <div className="absolute -top-[10%] -right-[10%] w-[40%] h-[40%] rounded-full bg-indigo-900 blur-[100px] opacity-40"></div>
        <div className="absolute top-[60%] -left-[10%] w-[50%] h-[50%] rounded-full bg-cyan-900 blur-[100px] opacity-30"></div>
      </div>

      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="flex justify-center">
          <div className="h-16 w-16 bg-gradient-to-br from-indigo-500 to-cyan-500 rounded-2xl shadow-[0_0_30px_rgba(99,102,241,0.5)] flex items-center justify-center transform -rotate-3 hover:rotate-0 transition-all duration-300">
            <svg className="w-9 h-9 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 20h9" />
              <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z" />
            </svg>
          </div>
        </div>
        <h2 className="mt-6 text-center text-3xl font-extrabold text-white tracking-tight">
          Create your account
        </h2>
        <p className="mt-2 text-center text-sm text-gray-400">
          Already have one?{' '}
          <Link to="/login" className="font-medium text-indigo-400 hover:text-indigo-300 transition-colors">
            Sign in
          </Link>
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-[#111827]/80 backdrop-blur-xl py-8 px-4 shadow-2xl sm:rounded-2xl sm:px-10 border border-white/10">

          {/* Trust badges */}
          <div className="flex items-center justify-center gap-3 mb-6 flex-wrap">
            {['Audit Trail Enabled', 'Local NLP', 'India First'].map(label => (
              <span key={label} className="text-[10px] font-bold uppercase tracking-wider text-cyan-400 border border-cyan-800 bg-cyan-950/60 px-2 py-1 rounded-full">
                {label}
              </span>
            ))}
          </div>

          <form className="space-y-4" onSubmit={handleSubmit}>
            {error && (
              <div className="bg-red-900/30 border border-red-500/50 text-red-400 px-4 py-3 rounded-lg text-sm flex items-center gap-2">
                <svg className="w-4 h-4 shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
                {error}
              </div>
            )}

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-gray-400 mb-1.5">Full Name</label>
                <input
                  type="text"
                  required
                  value={fullName}
                  onChange={e => setFullName(e.target.value)}
                  placeholder="Dr. Priya Sharma"
                  className="appearance-none block w-full px-4 py-3 border border-gray-700 rounded-xl shadow-sm placeholder-gray-600 text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-sm transition-all bg-gray-900/50 focus:bg-gray-800"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-400 mb-1.5">Username</label>
                <input
                  type="text"
                  required
                  value={username}
                  onChange={e => setUsername(e.target.value)}
                  placeholder="drpriya"
                  className="appearance-none block w-full px-4 py-3 border border-gray-700 rounded-xl shadow-sm placeholder-gray-600 text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-sm transition-all bg-gray-900/50 focus:bg-gray-800"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-400 mb-1.5">Email address</label>
              <input
                type="email"
                required
                value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder="doctor@hospital.in"
                className="appearance-none block w-full px-4 py-3 border border-gray-700 rounded-xl shadow-sm placeholder-gray-600 text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-sm transition-all bg-gray-900/50 focus:bg-gray-800"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-400 mb-1.5">Password</label>
              <input
                type="password"
                required
                value={password}
                onChange={e => setPassword(e.target.value)}
                placeholder="••••••••"
                className="appearance-none block w-full px-4 py-3 border border-gray-700 rounded-xl shadow-sm placeholder-gray-600 text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-sm transition-all bg-gray-900/50 focus:bg-gray-800"
              />
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full mt-2 flex justify-center items-center py-3 px-4 border border-transparent rounded-xl shadow-lg text-sm font-semibold text-white bg-gradient-to-r from-indigo-600 to-cyan-600 hover:from-indigo-500 hover:to-cyan-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-900 focus:ring-indigo-500 transition-all duration-200 disabled:opacity-70"
            >
              {isLoading ? (
                <>
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
                  </svg>
                  Creating account…
                </>
              ) : 'Create Lipi Account →'}
            </button>
          </form>

          <p className="mt-6 text-center text-[11px] text-gray-600 leading-relaxed">
            By registering you agree to our{' '}
            <Link to="/privacy" className="text-gray-500 underline hover:text-gray-400">Privacy Policy</Link>.
            {' '}Patient audio is never stored permanently.
          </p>
        </div>
      </div>
    </div>
  );
}
