import React from 'react';
import ThemeToggle from './ThemeToggle';
import '../styles/Header.css';

export default function Header({ isDark, setIsDark, user, onLogout }) {
  return (
    <header className="header">
      <div className="header-brand">
        <span className="header-icon">◈</span>
        <span className="header-title">Persona</span>
      </div>
      <div className="header-right">
        {user && (
          <span className="header-user">{user.email}</span>
        )}
        <ThemeToggle isDark={isDark} setIsDark={setIsDark} />
        {user && (
          <button className="logout-btn" onClick={onLogout}>Exit</button>
        )}
      </div>
    </header>
  );
}