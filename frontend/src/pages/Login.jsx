import React, { useState } from 'react';
import '../styles/Login.css';

const PLANS = ['free', 'starter', 'pro'];

export default function Login({ onLogin }) {
  const [email, setEmail] = useState('');
  const [plan, setPlan] = useState('free');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email.trim()) return;
    setLoading(true);
    setError('');
    try {
      const data = {"email": email, "plan": plan}
      localStorage.setItem('ep_user', JSON.stringify(data));
      onLogin(data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Something went wrong. Try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-noise" />

      <div className="login-left">
        <div className="login-brand">
          <span className="login-brand-icon">◈</span>
          <span className="login-brand-name">EchoPersona</span>
        </div>
        <div className="login-tagline">
          <h1>Your life,<br />scored.</h1>
          <p>Turn daily moments into cinematic audio stories. Type, upload, feel.</p>
        </div>
        <div className="login-orbs">
          <div className="orb orb-1" />
          <div className="orb orb-2" />
          <div className="orb orb-3" />
        </div>
      </div>

      <div className="login-right">
        <form className="login-form" onSubmit={handleSubmit}>
          <h2>Begin your story</h2>
          <p className="login-sub">No password. Just your email and we're in.</p>

          <div className="field">
            <label>Email</label>
            <input
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>

          <div className="field">
            <label>Plan</label>
            <div className="plan-options">
              {PLANS.map((p) => (
                <button
                  key={p}
                  type="button"
                  className={`plan-btn ${plan === p ? 'active' : ''}`}
                  onClick={() => setPlan(p)}
                >
                  {p}
                </button>
              ))}
            </div>
          </div>

          {error && <p className="login-error">{error}</p>}

          <button type="submit" className="login-submit" disabled={loading}>
            {loading ? <span className="spinner" /> : 'Enter →'}
          </button>
        </form>
      </div>
    </div>
  );
}