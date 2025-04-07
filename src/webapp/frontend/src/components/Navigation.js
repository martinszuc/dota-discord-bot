import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import './Navigation.css';

const Navigation = ({ user, onLogout }) => {
  const location = useLocation();

  return (
    <nav className="navigation">
      <div className="nav-logo">
        <img src="/favicon-32x32.png" alt="Dota Timer Bot" className="logo-image" />
        <h1 className="logo-text">Dota Timer Bot</h1>
      </div>

      <div className="nav-links">
        <Link
          to="/"
          className={`nav-link ${location.pathname === '/' ? 'active' : ''}`}
        >
          <i className="fas fa-tachometer-alt"></i>
          Dashboard
        </Link>
        <Link
          to="/game"
          className={`nav-link ${location.pathname === '/game' ? 'active' : ''}`}
        >
          <i className="fas fa-gamepad"></i>
          Game Controls
        </Link>
        <Link
          to="/events"
          className={`nav-link ${location.pathname === '/events' ? 'active' : ''}`}
        >
          <i className="fas fa-calendar-alt"></i>
          Events
        </Link>
        <Link
          to="/settings"
          className={`nav-link ${location.pathname === '/settings' ? 'active' : ''}`}
        >
          <i className="fas fa-cog"></i>
          Settings
        </Link>
      </div>

      <div className="nav-user">
        {user && (
          <>
            <span className="user-info">
              <i className="fas fa-user"></i>
              <span className="username">{user.username}</span>
              <span className="role-badge">{user.role}</span>
            </span>
            <button onClick={onLogout} className="logout-button">
              <i className="fas fa-sign-out-alt"></i>
              Logout
            </button>
          </>
        )}
      </div>
    </nav>
  );
};

export default Navigation;