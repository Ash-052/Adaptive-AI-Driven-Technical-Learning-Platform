import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { LogIn, UserPlus, Mail, Lock, User, Loader2, AlertCircle } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { api } from '../api/api';

const AuthLayout = ({ children, title, subtitle }) => (
  <div className="min-h-screen bg-gray-950 flex items-center justify-center p-6">
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="max-w-md w-full bg-gray-900 border border-gray-800 rounded-3xl p-10 shadow-2xl"
    >
      <div className="text-center mb-10">
        <h1 className="text-3xl font-black text-white mb-2">{title}</h1>
        <p className="text-gray-500">{subtitle}</p>
      </div>
      {children}
    </motion.div>
  </div>
);

// --- LOGIN PAGE ---
export const Login = () => {
  const [formData, setFormData] = useState({ email: '', password: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await api.login(formData);
      localStorage.setItem('token', res.data.access_token);
      localStorage.setItem('user_id', res.data.user_id);
      localStorage.setItem('username', res.data.username);
      navigate('/');
    } catch (err) {
      setError(err.response?.data?.detail || "Login failed. Check your credentials.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthLayout title="Welcome Back" subtitle="Log in to continue your learning journey">
      <form onSubmit={handleSubmit} className="space-y-6">
        <Input icon={<Mail size={18} />} type="email" placeholder="Email Address" 
          value={formData.email} onChange={(e) => setFormData({...formData, email: e.target.value})} required />
        <Input icon={<Lock size={18} />} type="password" placeholder="Password" 
          value={formData.password} onChange={(e) => setFormData({...formData, password: e.target.value})} required />
        
        {error && <div className="flex items-center space-x-2 text-red-400 text-sm bg-red-900/20 p-3 rounded-lg border border-red-900/50">
          <AlertCircle size={16} /> <span>{error}</span>
        </div>}

        <button disabled={loading} className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-4 rounded-xl transition-all shadow-lg shadow-blue-900/20 flex items-center justify-center space-x-2 disabled:opacity-50">
          {loading ? <Loader2 className="animate-spin" /> : <LogIn size={20} />}
          <span>Sign In</span>
        </button>
      </form>
      <p className="mt-8 text-center text-gray-500 text-sm">
        Don't have an account? <Link to="/register" className="text-blue-400 font-bold hover:underline">Register now</Link>
      </p>
    </AuthLayout>
  );
};

// --- REGISTER PAGE ---
export const Register = () => {
  const [formData, setFormData] = useState({ username: '', email: '', password: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await api.register(formData);
      navigate('/login');
    } catch (err) {
      setError(err.response?.data?.detail || "Registration failed. Try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthLayout title="Create Account" subtitle="Join the adaptive AI learning platform">
      <form onSubmit={handleSubmit} className="space-y-6">
        <Input icon={<User size={18} />} type="text" placeholder="Username" 
          value={formData.username} onChange={(e) => setFormData({...formData, username: e.target.value})} required />
        <Input icon={<Mail size={18} />} type="email" placeholder="Email Address" 
          value={formData.email} onChange={(e) => setFormData({...formData, email: e.target.value})} required />
        <Input icon={<Lock size={18} />} type="password" placeholder="Password" 
          value={formData.password} onChange={(e) => setFormData({...formData, password: e.target.value})} required />
        
        {error && <div className="flex items-center space-x-2 text-red-400 text-sm bg-red-900/20 p-3 rounded-lg border border-red-900/50">
          <AlertCircle size={16} /> <span>{error}</span>
        </div>}

        <button disabled={loading} className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-4 rounded-xl transition-all shadow-lg shadow-blue-900/20 flex items-center justify-center space-x-2 disabled:opacity-50">
          {loading ? <Loader2 className="animate-spin" /> : <UserPlus size={20} />}
          <span>Create Account</span>
        </button>
      </form>
      <p className="mt-8 text-center text-gray-500 text-sm">
        Already have an account? <Link to="/login" className="text-blue-400 font-bold hover:underline">Log in</Link>
      </p>
    </AuthLayout>
  );
};

const Input = ({ icon, ...props }) => (
  <div className="relative">
    <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-gray-500">
      {icon}
    </div>
    <input {...props} className="block w-full pl-12 pr-4 py-4 bg-gray-950 border border-gray-800 rounded-2xl text-white placeholder-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all" />
  </div>
);
