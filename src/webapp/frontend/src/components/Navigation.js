import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import './Navigation.css';

const Navigation = ({ user, onLogout }) => {
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [windowWidth, setWindowWidth] = useState(window.innerWidth);

  // Handle window resize for responsive design
  useEffect(() => {
    const handleResize = () => {
      setWindowWidth(window.innerWidth);
      if (window.innerWidth > 768) {
        setMobileMenuOpen(false); // Close mobile menu on desktop view
      }
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Close menu when navigation occurs
  useEffect(() => {
    setMobileMenuOpen(false);
  }, [location]);

  // Toggle mobile menu
  const toggleMobileMenu = () => {
    setMobileMenuOpen(!mobileMenuOpen);
  };

  // Check if we're on mobile view
  const isMobile = windowWidth <= 768;

  return (
    <nav className={`navigation ${isMobile ? 'mobile' : ''}`}>
      {isMobile && (
        <div className="mobile-header">
          <div className="mobile-logo">
            <img src="/favicon-32x32.png" alt="Dota Timer Bot" className="logo-image" />
            <h1 className="logo-text">Dota Timer Bot</h1>
          </div>
          <button
            className={`mobile-menu-toggle ${mobileMenuOpen ? 'active' : ''}`}
            onClick={toggleMobileMenu}
            aria-label="Toggle menu"
          >
            <span className="bar"></span>
            <span className="bar"></span>
            <span className="bar"></span>
          </button>
        </div>
      )}

      {(!isMobile || mobileMenuOpen) && (
        <>
          {!isMobile && (
            <div className="nav-logo">
              <img src="/favicon-32x32.png" alt="Dota Timer Bot" className="logo-image" />
              <h1 className="logo-text">Dota Timer Bot</h1>
            </div>
          )}

          <div className={`nav-links ${mobileMenuOpen ? 'show' : ''}`}>
            <Link
              to="/"
              className={`nav-link ${location.pathname === '/' ? 'active' : ''}`}
            >
              <i className="fas fa-tachometer-alt"></i>
              <span>Dashboard</span>
            </Link>
            <Link
              to="/game"
              className={`nav-link ${location.pathname === '/game' ? 'active' : ''}`}
            >
              <i className="fas fa-gamepad"></i>
              <span>Game Controls</span>
            </Link>
            <Link
              to="/events"
              className={`nav-link ${location.pathname === '/events' ? 'active' : ''}`}
            >
              <i className="fas fa-calendar-alt"></i>
              <span>Events</span>
            </Link>
            <Link
              to="/settings"
              className={`nav-link ${location.pathname === '/settings' ? 'active' : ''}`}
            >
              <i className="fas fa-cog"></i>
              <span>Settings</span>
            </Link>

            <div className="nav-divider"></div>

            {user && (
              <div className="nav-user mobile-user">
                <div className="user-info">
                  <i className="fas fa-user"></i>
                  <span className="username">{user.username}</span>
                  <span className="role-badge">{user.role}</span>
                </div>
                <button onClick={onLogout} className="logout-button">
                  <i className="fas fa-sign-out-alt"></i>
                  <span>Logout</span>
                </button>
              </div>
            )}
          </div>

          {!isMobile && user && (
            <div className="nav-user">
              <div className="user-info">
                <i className="fas fa-user"></i>
                <span className="username">{user.username}</span>
                <span className="role-badge">{user.role}</span>
              </div>
              <button onClick={onLogout} className="logout-button">
                <i className="fas fa-sign-out-alt"></i>
                <span>Logout</span>
              </button>
            </div>
          )}
        </>
      )}
    </nav>
  );
};

export default Navigation;