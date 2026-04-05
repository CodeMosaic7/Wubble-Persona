import React, { useState, useEffect } from 'react';
import Login from './pages/Login';
import Home from './pages/Home';
import './styles/Global.css';

export default function App() {
  const [user, setUser] = useState(null);
  const [isDark, setIsDark] = useState(true);

  // Persist login across refresh
  useEffect(() => {
    const saved = localStorage.getItem('ep_user');
    if (saved) {
      try { setUser(JSON.parse(saved)); } catch {}
    }
  }, []);

  const handleLogin = (userData) => setUser(userData);

  const handleLogout = () => {
    localStorage.removeItem('ep_user');
    setUser(null);
  };

  if (!user) {
    return <Login onLogin={handleLogin} />;
  }

  return (
    <Home
      user={user}
      isDark={isDark}
      setIsDark={setIsDark}
      onLogout={handleLogout}
    />
  );
}