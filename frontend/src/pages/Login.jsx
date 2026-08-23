import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import apiClient from '../api/client';
import { ToastProvider, useToast } from '../components/ToastProvider';

function LoginContent() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const { addToast } = useToast();
  const navigate = useNavigate();

  const demoCredentials = {
    email: 'demo@payos.com',
    password: 'demopassword',
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await apiClient.post('/auth/login', {
        email,
        password,
      });

      localStorage.setItem('access_token', response.data.access_token);

      addToast({
        type: 'success',
        message: 'Login successful.',
      });

      navigate('/dashboard');
    } catch (err) {
      if (err.response && err.response.status === 401) {
        setError('Invalid email or password.');

        addToast({
          type: 'error',
          message: 'Invalid email or password.',
        });
      } else {
        setError('An error occurred. Please try again.');

        addToast({
          type: 'error',
          message: 'Login failed. Please try again.',
        });
      }
    } finally {
      setLoading(false);
    }
  };

  const handleDemoLogin = async () => {
    setError('');
    setLoading(true);

    try {
      const response = await apiClient.post(
        '/auth/login',
        demoCredentials
      );

      localStorage.setItem(
        'access_token',
        response.data.access_token
      );

      addToast({
        type: 'success',
        message: 'Demo login successful.',
      });

      navigate('/dashboard');
    } catch (err) {
      setError('Demo login failed. Please try again later.');

      addToast({
        type: 'error',
        message: 'Demo login failed. Please try again later.',
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full bg-white p-8 rounded shadow">
        <h1 className="text-3xl font-bold mb-6 text-center">
          PayOS Login
        </h1>

        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label
              htmlFor="email"
              className="block text-sm font-medium text-gray-700"
            >
              Email
            </label>

            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="mt-1 block w-full border border-gray-300 rounded px-3 py-2"
              disabled={loading}
            />
          </div>

          <div>
            <label
              htmlFor="password"
              className="block text-sm font-medium text-gray-700"
            >
              Password
            </label>

            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="mt-1 block w-full border border-gray-300 rounded px-3 py-2"
              disabled={loading}
            />
          </div>

          {error && (
            <p className="text-red-600 text-sm">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? 'Signing In...' : 'Sign In'}
          </button>
        </form>

        <button
          type="button"
          onClick={handleDemoLogin}
          disabled={loading}
          className="mt-4 w-full bg-gray-600 text-white py-2 rounded hover:bg-gray-700 disabled:opacity-50"
        >
          {loading ? 'Signing In...' : 'Demo Login'}
        </button>
      </div>
    </div>
  );
}

export default function Login() {
  return (
    <ToastProvider>
      <LoginContent />
    </ToastProvider>
  );
}