import React, { useState, useEffect } from 'react';
import {
  fetchStatus,
  startTimer,
  stopTimer,
  pauseTimer,
  unpauseTimer,
  startRoshanTimer,
  cancelRoshanTimer,
  startGlyphTimer,
  cancelGlyphTimer,
  startTormentorTimer,
  cancelTormentorTimer
} from '../api';
import './GameControls.css';

const GameControls = () => {
  const [guildId, setGuildId] = useState('');
  const [countdown, setCountdown] = useState('10:00');
  const [mode, setMode] = useState('regular');
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [actionLoading, setActionLoading] = useState(false);

  // Load initial status
  useEffect(() => {
    const loadStatus = async () => {
      try {
        setLoading(true);
        const response = await fetchStatus();
        setStatus(response.data);

        // Set guildId to the first active timer if available
        if (response.data.active_timers_count > 0) {
          const firstGuildId = Object.keys(response.data.active_timers)[0];
          setGuildId(firstGuildId);
          setMode(response.data.active_timers[firstGuildId].mode);
        }

        setLoading(false);
      } catch (err) {
        console.error('Error loading status:', err);
        setError('Failed to load bot status. Please try again.');
        setLoading(false);
      }
    };

    loadStatus();

    // Poll for updates every 5 seconds
    const interval = setInterval(loadStatus, 5000);

    return () => clearInterval(interval);
  }, []);

  // Clear success message after 3 seconds
  useEffect(() => {
    if (success) {
      const timer = setTimeout(() => {
        setSuccess(null);
      }, 3000);

      return () => clearTimeout(timer);
    }
  }, [success]);

  const isTimerActive = () => {
    if (!status || !guildId) return false;
    return status.active_timers && status.active_timers[guildId];
  };

  const isTimerPaused = () => {
    if (!isTimerActive()) return false;
    return status.active_timers[guildId].paused;
  };

  const isRoshanActive = () => {
    if (!isTimerActive()) return false;
    return status.active_timers[guildId].roshan_active;
  };

  const isGlyphActive = () => {
    if (!isTimerActive()) return false;
    return status.active_timers[guildId].glyph_active;
  };

  const isTormentorActive = () => {
    if (!isTimerActive()) return false;
    return status.active_timers[guildId].tormentor_active;
  };

  // Format time seconds as MM:SS
  const formatTime = (seconds) => {
    const absSeconds = Math.abs(seconds);
    const mins = Math.floor(absSeconds / 60);
    const secs = absSeconds % 60;
    const sign = seconds < 0 ? '-' : '';
    return `${sign}${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  // Handle form submission for starting timer
  const handleStartTimer = async (e) => {
    e.preventDefault();

    if (!guildId) {
      setError('Please enter a Guild ID');
      return;
    }

    if (!countdown) {
      setError('Please enter a countdown value');
      return;
    }

    try {
      setActionLoading(true);
      setError(null);

      const response = await startTimer(guildId, countdown, mode);
      setSuccess(`Timer started: ${response.data.message}`);

      // Refresh status
      const statusResponse = await fetchStatus();
      setStatus(statusResponse.data);
    } catch (err) {
      console.error('Error starting timer:', err);
      setError('Failed to start timer: ' + (err.message || 'Unknown error'));
    } finally {
      setActionLoading(false);
    }
  };

  // Action handlers
  const handleAction = async (action) => {
    if (!guildId) {
      setError('Please enter a Guild ID');
      return;
    }

    try {
      setActionLoading(true);
      setError(null);

      let response;

      switch (action) {
        case 'stop':
          response = await stopTimer(guildId);
          break;
        case 'pause':
          response = await pauseTimer(guildId);
          break;
        case 'unpause':
          response = await unpauseTimer(guildId);
          break;
        case 'roshan-start':
          response = await startRoshanTimer(guildId);
          break;
        case 'roshan-cancel':
          response = await cancelRoshanTimer(guildId);
          break;
        case 'glyph-start':
          response = await startGlyphTimer(guildId);
          break;
        case 'glyph-cancel':
          response = await cancelGlyphTimer(guildId);
          break;
        case 'tormentor-start':
          response = await startTormentorTimer(guildId);
          break;
        case 'tormentor-cancel':
          response = await cancelTormentorTimer(guildId);
          break;
        default:
          throw new Error('Unknown action');
      }

      setSuccess(`Action successful: ${response.data.message}`);

      // Refresh status
      const statusResponse = await fetchStatus();
      setStatus(statusResponse.data);
    } catch (err) {
      console.error(`Error performing action ${action}:`, err);
      setError(`Failed to perform action: ${err.message || 'Unknown error'}`);
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div className="game-controls">
      <h1>Game Controls</h1>

      <div className="controls-container">
        <div className="guild-selector">
          <label htmlFor="guild-id">Guild ID:</label>
          <input
            type="text"
            id="guild-id"
            value={guildId}
            onChange={(e) => setGuildId(e.target.value)}
            placeholder="Enter Guild ID"
          />
        </div>

        {error && <div className="error-message">{error}</div>}
        {success && <div className="success-message">{success}</div>}

        <div className="control-panel">
          <div className="start-timer-form">
            <h2>Start Game Timer</h2>
            <form onSubmit={handleStartTimer}>
              <div className="form-group">
                <label htmlFor="countdown">Countdown:</label>
                <input
                  type="text"
                  id="countdown"
                  value={countdown}
                  onChange={(e) => setCountdown(e.target.value)}
                  placeholder="MM:SS or seconds"
                />
              </div>

              <div className="form-group">
                <label htmlFor="mode">Mode:</label>
                <select
                  id="mode"
                  value={mode}
                  onChange={(e) => setMode(e.target.value)}
                >
                  <option value="regular">Regular</option>
                  <option value="turbo">Turbo</option>
                </select>
              </div>

              <button
                type="submit"
                className="primary-button"
                disabled={actionLoading || isTimerActive()}
              >
                Start Timer
              </button>
            </form>
          </div>

          <div className="timer-actions">
            <h2>Timer Controls</h2>
            <div className="button-group">
              <button
                className="control-button red"
                onClick={() => handleAction('stop')}
                disabled={actionLoading || !isTimerActive()}
              >
                Stop Timer
              </button>

              <button
                className="control-button yellow"
                onClick={() => handleAction('pause')}
                disabled={actionLoading || !isTimerActive() || isTimerPaused()}
              >
                Pause Timer
              </button>

              <button
                className="control-button green"
                onClick={() => handleAction('unpause')}
                disabled={actionLoading || !isTimerActive() || !isTimerPaused()}
              >
                Unpause Timer
              </button>
            </div>
          </div>

          <div className="special-timers">
            <h2>Special Timers</h2>

            <div className="timer-card">
              <h3>Roshan Timer</h3>
              <div className="status">
                Status: <span className={isRoshanActive() ? 'active' : 'inactive'}>
                  {isRoshanActive() ? 'Active' : 'Inactive'}
                </span>
              </div>
              <div className="button-group">
                <button
                  className="control-button blue"
                  onClick={() => handleAction('roshan-start')}
                  disabled={actionLoading || !isTimerActive() || isRoshanActive()}
                >
                  Start Roshan Timer
                </button>
                <button
                  className="control-button red"
                  onClick={() => handleAction('roshan-cancel')}
                  disabled={actionLoading || !isTimerActive() || !isRoshanActive()}
                >
                  Cancel Roshan Timer
                </button>
              </div>
            </div>

            <div className="timer-card">
              <h3>Glyph Timer</h3>
              <div className="status">
                Status: <span className={isGlyphActive() ? 'active' : 'inactive'}>
                  {isGlyphActive() ? 'Active' : 'Inactive'}
                </span>
              </div>
              <div className="button-group">
                <button
                  className="control-button blue"
                  onClick={() => handleAction('glyph-start')}
                  disabled={actionLoading || !isTimerActive() || isGlyphActive()}
                >
                  Start Glyph Timer
                </button>
                <button
                  className="control-button red"
                  onClick={() => handleAction('glyph-cancel')}
                  disabled={actionLoading || !isTimerActive() || !isGlyphActive()}
                >
                  Cancel Glyph Timer
                </button>
              </div>
            </div>

            <div className="timer-card">
              <h3>Tormentor Timer</h3>
              <div className="status">
                Status: <span className={isTormentorActive() ? 'active' : 'inactive'}>
                  {isTormentorActive() ? 'Active' : 'Inactive'}
                </span>
              </div>
              <div className="button-group">
                <button
                  className="control-button blue"
                  onClick={() => handleAction('tormentor-start')}
                  disabled={actionLoading || !isTimerActive() || isTormentorActive()}
                >
                  Start Tormentor Timer
                </button>
                <button
                  className="control-button red"
                  onClick={() => handleAction('tormentor-cancel')}
                  disabled={actionLoading || !isTimerActive() || !isTormentorActive()}
                >
                  Cancel Tormentor Timer
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {isTimerActive() && (
        <div className="active-timer-display">
          <h2>Current Timer Status</h2>
          <div className="timer-info">
            <div className="timer-value">
              <span className="label">Time:</span>
              <span className="value">{formatTime(status.active_timers[guildId].elapsed_time)}</span>
            </div>
            <div className="timer-details">
              <div className="detail-item">
                <span className="label">Mode:</span>
                <span className="value">{status.active_timers[guildId].mode}</span>
              </div>
              <div className="detail-item">
                <span className="label">Status:</span>
                <span className="value">{status.active_timers[guildId].paused ? 'Paused' : 'Running'}</span>
              </div>
            </div>
          </div>

          <div className="recent-events">
            <h3>Recent Events</h3>
            <ul>
              {status.active_timers[guildId].recent_events?.map((event, index) => (
                <li key={index}>{event}</li>
              )) || <li>No recent events</li>}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
};

export default GameControls;