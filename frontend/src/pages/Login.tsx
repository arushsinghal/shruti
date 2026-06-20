import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import api from '../lib/api';

export default function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleLogin = async (user: string, pass: string) => {
    setError('');
    setIsLoading(true);
    try {
      const formData = new URLSearchParams();
      formData.append('username', user);
      formData.append('password', pass);

      const response = await api.post('/auth/token', formData, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      });
      
      login(response.data.access_token);
      navigate('/dashboard');
    } catch (err: any) {
      if (err.response?.data?.detail) {
        setError(err.response.data.detail);
      } else if (err.message) {
        setError("Network error: " + err.message);
      } else {
        setError('Invalid username or password');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    handleLogin(username, password);
  };

  const handleDemoLogin = () => {
    setUsername('arush');
    setPassword('1234');
    handleLogin('arush', '1234');
  };

  return (
    <div className="min-h-screen bg-[#0B0F19] flex flex-col justify-center py-12 sm:px-6 lg:px-8 relative overflow-hidden text-gray-200">
      {/* Decorative dark mode background blobs */}
      <div className="absolute top-0 left-0 w-full h-full overflow-hidden -z-10 pointer-events-none">
        <div className="absolute -top-[10%] -left-[10%] w-[40%] h-[40%] rounded-full bg-indigo-900 blur-[100px] opacity-40"></div>
        <div className="absolute top-[60%] -right-[10%] w-[50%] h-[50%] rounded-full bg-cyan-900 blur-[100px] opacity-30"></div>
      </div>

      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="flex justify-center">
          {/* Lipi Logo */}
          <div className="h-16 w-16 bg-gradient-to-br from-indigo-500 to-cyan-500 rounded-2xl shadow-[0_0_30px_rgba(99,102,241,0.5)] flex items-center justify-center transform rotate-3 hover:rotate-0 transition-all duration-300">
            <svg className="w-9 h-9 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 20h9" />
              <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z" />
            </svg>
          </div>
        </div>
        <h2 className="mt-6 text-center text-3xl font-extrabold text-white tracking-tight">
          Welcome to Lipi
        </h2>
        <p className="mt-2 text-center text-sm text-gray-400">
          India's AI Clinical Scribe — Hindi · English · Hinglish
        </p>
        <div className="mt-4 flex items-center justify-center gap-2 flex-wrap">
          {['Audit Trail Enabled', 'Local NLP', 'Sarvam ASR', 'No LLM Hallucination'].map(label => (
            <span key={label} className="text-[10px] font-bold uppercase tracking-wider text-cyan-400 border border-cyan-800 bg-cyan-950/60 px-2 py-1 rounded-full">
              {label}
            </span>
          ))}
        </div>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-[#111827]/80 backdrop-blur-xl py-8 px-4 shadow-2xl sm:rounded-2xl sm:px-10 border border-white/10">
          
          <button
            onClick={handleDemoLogin}
            disabled={isLoading}
            className="w-full mb-6 flex justify-center items-center py-3 px-4 border border-transparent rounded-xl shadow-lg text-sm font-semibold text-white bg-gradient-to-r from-indigo-600 to-cyan-600 hover:from-indigo-500 hover:to-cyan-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-900 focus:ring-indigo-500 transition-all duration-200 hover:shadow-indigo-500/30 disabled:opacity-70"
          >
            {isLoading ? (
              <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            ) : (
              <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            )}
            {isLoading ? 'Authenticating...' : 'One-Click Demo Login'}
          </button>

          <div className="relative mb-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-700" />
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-2 bg-[#111827] text-gray-500">Or sign in manually</span>
            </div>
          </div>

          <form className="space-y-5" onSubmit={handleSubmit}>
            {error && (
              <div className="bg-red-900/30 border border-red-500/50 text-red-400 px-4 py-3 rounded-lg text-sm flex items-center">
                <svg className="w-5 h-5 mr-2 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
                {error}
              </div>
            )}
            
            <div>
              <label className="block text-sm font-medium text-gray-300">Username</label>
              <div className="mt-1">
                <input
                  type="text"
                  required
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="appearance-none block w-full px-4 py-3 border border-gray-700 rounded-xl shadow-sm placeholder-gray-500 text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent sm:text-sm transition-all duration-200 bg-gray-900/50 focus:bg-gray-800"
                  placeholder="Enter your username"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300">Password</label>
              <div className="mt-1">
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="appearance-none block w-full px-4 py-3 border border-gray-700 rounded-xl shadow-sm placeholder-gray-500 text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent sm:text-sm transition-all duration-200 bg-gray-900/50 focus:bg-gray-800"
                  placeholder="••••••••"
                />
              </div>
            </div>

            <div className="flex items-center justify-between">
              <div className="text-sm">
                <Link to="/register" className="font-medium text-indigo-400 hover:text-indigo-300 transition-colors">
                  Create an account
                </Link>
              </div>
              <div className="text-sm">
                <a href="#" className="font-medium text-gray-500 hover:text-gray-400 transition-colors">
                  Forgot password?
                </a>
              </div>
            </div>

            <div>
              <button
                type="submit"
                disabled={isLoading}
                className="w-full flex justify-center py-3 px-4 border border-white/10 rounded-xl shadow-sm text-sm font-semibold text-gray-300 bg-white/5 hover:bg-white/10 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-900 focus:ring-indigo-500 transition-all duration-200 disabled:opacity-50"
              >
                Sign in manually
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
