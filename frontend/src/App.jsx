import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AppShell } from './AppShell';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Transactions from './pages/Transactions';
import FraudMonitor from './pages/FraudMonitor';
import Disputes from './pages/Disputes';
import BNPL from './pages/BNPL';
import CheckoutDemo from './pages/CheckoutDemo';

function RequireAuth({ children }) {
  const token = localStorage.getItem('access_token');
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  return children;
}

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          path="/"
          element={
            <RequireAuth>
              <AppShell />
            </RequireAuth>
          }
        >
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="transactions" element={<Transactions />} />
          <Route path="fraud" element={<FraudMonitor />} />
          <Route path="disputes" element={<Disputes />} />
          <Route path="bnpl" element={<BNPL />} />
          <Route path="checkout" element={<CheckoutDemo />} />
          <Route index element={<Navigate to="/dashboard" replace />} />
        </Route>
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </Router>
  );
}

export default App;