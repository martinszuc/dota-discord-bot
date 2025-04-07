import React, { useState, useEffect, useCallback } from 'react';
import { fetchStatus, fetchLogs, fetchEvents, toggleGSISync } from '../api';
import GSIStatus from './GSIStatus';
import './Dashboard.css';

// New component for status indicators
const StatusIndicator = ({ status, label }) => (
  <div className="status-indicator">
    <span className={`status-dot ${status ? 'online' : 'offline'}`}></span>
    <span>{label}</span>
  </div>
);

// Timer display component
const TimerDisplay = ({ timer, formatTime }) => (
  <div className="timer-card">
    <h3>Game Timer</h3>
    <div className="timer-info">
      <p>Mode: <span className="highlight">{timer.mode || 'regular'}</span></p>
      <p>Time: <span className="highlight">{formatTime(timer.elapsed_time)}</span></p>
      <p>Status: <span className="highlight">{timer.paused ? 'Paused' : 'Running'}</span></p>
    </div>
  </div>
);

// Subtimer component
const SubTimer = ({ title, active }) => (
  <div className={`timer-card mini ${active ? 'active' : 'inactive'}`}>
    <h4>{title}</h4>
    <div className="timer-status">
      {active ? 'Active' : 'Inactive'}
    </div>
  </div>
);

// Recent events component
const RecentEvents = ({ events = [] }) => (
  <div className="recent-events">
    <h3>Recent Events</h3>
    <ul className="events-list">
      {events.length > 0 ? (
        events.map((event, index) => (
          <li key={index} className={getEventClass(event)}>
            <span className="event-time">{event.split(' - ')[0]}</span>
            <span className="event-message">{event.split(' - ').slice(1).join(' - ')}</span>
          </li>
        ))
      ) : (
        <li className="no-events">No recent events</li>
      )}
    </ul>
  </div>
);

// Helper function to determine event class based on content
const getEventClass = (event) => {
  const lowerEvent = event.toLowerCase();
  if (lowerEvent.includes('roshan')) return 'event-roshan';
  if (lowerEvent.includes('glyph')) return 'event-glyph';
  if (lowerEvent.includes('tormentor')) return 'event-tormentor';
  if (lowerEvent.includes('rune')) return 'event-rune';
  if (lowerEvent.includes('bounty')) return 'event-bounty';
  if (lowerEvent.includes('siege')) return 'event-siege';
  return '';
};

// Events table component
const EventsTable = ({ events, title, headers, formatEvent }) => (
  <div className="event-type">
    <h3>{title}</h3>
    {Object.keys(events).length === 0 ? (
      <p className="no-events">No {title.toLowerCase()} found</p>
    ) : (
      <table className="events-table">
        <thead>
          <tr>
            {headers.map((header, index) => (
              <th key={index}>{header}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {Object.entries(events).map(([id, event]) => formatEvent(id, event))}
        </tbody>
      </table>
    )}
  </div>
);

// Logs table component
const LogsTable = ({ logs }) => (
  <div className="logs-container">
    {Array.isArray(logs) && logs.length > 0 ? (
      <table className="logs-table">
        <thead>
          <tr>
            <th>Time</th>
            <th>Level</th>
            <th>Message</th>
          </tr>
        </thead>
        <tbody>
          {logs.map((log, index) => (
            <tr key={index} className={`log-level-${(log.level || '').toLowerCase()}`}>
              <td>{log.timestamp || ''}</td>
              <td>{log.level || ''}</td>
              <td>{log.message || ''}</td>
            </tr>
          ))}
        </tbody>
      </table>
    ) : (
      <p className="no-logs">No logs available</p>
    )}
  </div>
);

const Dashboard = () => {
  // State hooks
  const [status, setStatus] = useState({ bot_running: false, active_timers_count: 0, active_timers: {} });
  const [logs, setLogs] = useState([]);
  const [events, setEvents] = useState({ static_events: {}, periodic_events: {} });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeGuild, setActiveGuild] = useState("279614276338188288");
  const [gsiSyncEnabled, setGsiSyncEnabled] = useState(false);
  const [refreshInterval, setRefreshInterval] = useState(5000); // 5 seconds default
  const [refreshing, setRefreshing] = useState(false);

  // Format time function (memoized for performance)
  const formatTime = useCallback((seconds) => {
    if (seconds === undefined || seconds === null) return '00:00';
    const minutes = Math.floor(Math.abs(seconds) / 60);
    const secs = Math.abs(seconds) % 60;
    const sign = seconds < 0 ? '-' : '';
    return `${sign}${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  }, []);

  // Data loading function
  const loadData = useCallback(async () => {
    try {
      setRefreshing(true);

      // Fetch bot status
      try {
        const statusData = await fetchStatus();
        setStatus(statusData.data || { bot_running: false, active_timers_count: 0, active_timers: {} });

        // Set active guild if there's at least one active timer
        if (statusData.data.active_timers_count > 0) {
          const guildIds = Object.keys(statusData.data.active_timers);
          if (!activeGuild || !statusData.data.active_timers[activeGuild]) {
            setActiveGuild(guildIds[0]);
          }

          // Only fetch events if we have a valid guild ID
          const guildIdToUse = activeGuild || guildIds[0];
          try {
            const eventsData = await fetchEvents(guildIdToUse);
            setEvents(eventsData.data || { static_events: {}, periodic_events: {} });
          } catch (err) {
            console.error("Error fetching events:", err);
          }
        } else if (!events.static_events || Object.keys(events.static_events).length === 0) {
          // If no active timers, try to fetch events with a default guild ID
          try {
            const defaultGuildId = "1";  // A placeholder ID
            const eventsData = await fetchEvents(defaultGuildId);
            setEvents(eventsData.data || { static_events: {}, periodic_events: {} });
          } catch (err) {
            console.error("Error fetching events with default ID:", err);
          }
        }
      } catch (err) {
        console.error("Error fetching status:", err);
        setStatus({ bot_running: false, active_timers_count: 0, active_timers: {} });
      }

      // Fetch recent logs
      try {
        const logsData = await fetchLogs(20);
        setLogs(Array.isArray(logsData.data) ? logsData.data : []);
      } catch (err) {
        console.error("Error fetching logs:", err);
        setLogs([]);
      }

      setLoading(false);
      setRefreshing(false);
    } catch (err) {
      console.error('Error loading dashboard data:', err);
      setError('Failed to load dashboard data. Please try again.');
      setLoading(false);
      setRefreshing(false);
    }
  }, [activeGuild, events.static_events]);

  // Toggle GSI sync function
  const handleToggleGsiSync = async () => {
    if (!activeGuild) {
      setError("Please select a guild first");
      return;
    }

    try {
      await toggleGSISync(activeGuild);
      setGsiSyncEnabled(!gsiSyncEnabled);

      // Show success message
      const tempSuccess = document.createElement('div');
      tempSuccess.className = 'success-message';
      tempSuccess.textContent = `GSI sync ${!gsiSyncEnabled ? 'enabled' : 'disabled'} successfully!`;
      document.querySelector('.dashboard').appendChild(tempSuccess);

      // Remove after 3 seconds
      setTimeout(() => {
        if (tempSuccess.parentNode) {
          tempSuccess.parentNode.removeChild(tempSuccess);
        }
      }, 3000);

    } catch (err) {
      console.error("Error toggling GSI sync:", err);
      setError("Failed to toggle GSI sync");
    }
  };

  // Initialize data loading
  useEffect(() => {
    loadData();

    // Set up polling for updates
    const interval = setInterval(loadData, refreshInterval);

    return () => clearInterval(interval);
  }, [loadData, refreshInterval]);

  // Change refresh rate
  const handleRefreshRateChange = (e) => {
    const newRate = parseInt(e.target.value, 10);
    setRefreshInterval(newRate);
  };

  // Manually refresh data
  const handleManualRefresh = () => {
    loadData();
  };

  if (loading && !refreshing) {
    return (
      <div className="dashboard-loading">
        <div className="loading-spinner"></div>
        <p>Loading dashboard data...</p>
      </div>
    );
  }

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1>Dota Timer Bot Dashboard</h1>
        <div className="refresh-controls">
          <select
            value={refreshInterval}
            onChange={handleRefreshRateChange}
            className="refresh-rate-selector"
          >
            <option value={2000}>Refresh: 2s</option>
            <option value={5000}>Refresh: 5s</option>
            <option value={10000}>Refresh: 10s</option>
            <option value={30000}>Refresh: 30s</option>
          </select>
          <button
            onClick={handleManualRefresh}
            className="refresh-button"
            disabled={refreshing}
          >
            {refreshing ? 'Refreshing...' : 'Refresh Now'}
          </button>
        </div>
      </div>

      {error && (
        <div className="error-message">
          <i className="fas fa-exclamation-circle"></i> {error}
          <button onClick={() => setError(null)} className="dismiss-button">
            <i className="fas fa-times"></i>
          </button>
        </div>
      )}

      {/* GSI Status Section */}
      <div className="section-container">
        <GSIStatus />
        {activeGuild && (
          <button
            className={`gsi-sync-button ${gsiSyncEnabled ? 'enabled' : ''}`}
            onClick={handleToggleGsiSync}
          >
            <i className={`fas fa-${gsiSyncEnabled ? 'toggle-on' : 'toggle-off'}`}></i>
            {gsiSyncEnabled ? 'Disable GSI Sync' : 'Enable GSI Sync'}
          </button>
        )}
      </div>

      <div className="status-section">
        <h2>Bot Status</h2>
        <StatusIndicator status={status?.bot_running} label={status?.bot_running ? 'Bot Online' : 'Bot Offline'} />
        <div className="status-detail">
          <p>Active Timers: <span className="counter">{status?.active_timers_count || 0}</span></p>
        </div>
      </div>

      {status?.active_timers_count > 0 && (
        <div className="active-timers-section">
          <h2>Active Timers</h2>
          <div className="guild-selector">
            <select
              value={activeGuild || ''}
              onChange={(e) => setActiveGuild(e.target.value)}
            >
              {Object.keys(status.active_timers || {}).map(guildId => (
                <option key={guildId} value={guildId}>
                  Guild ID: {guildId}
                </option>
              ))}
            </select>
          </div>

          {activeGuild && status.active_timers[activeGuild] && (
            <div className="timer-details">
              <TimerDisplay timer={status.active_timers[activeGuild]} formatTime={formatTime} />

              <div className="sub-timers">
                <SubTimer
                  title="Roshan"
                  active={status.active_timers[activeGuild].roshan_active}
                />
                <SubTimer
                  title="Glyph"
                  active={status.active_timers[activeGuild].glyph_active}
                />
                <SubTimer
                  title="Tormentor"
                  active={status.active_timers[activeGuild].tormentor_active}
                />
              </div>

              <RecentEvents events={status.active_timers[activeGuild].recent_events} />
            </div>
          )}
        </div>
      )}

      <div className="events-section">
        <h2>All Events</h2>
        <div className="events-container">
          <EventsTable
            events={events.static_events || {}}
            title="Static Events"
            headers={["ID", "Time", "Mode", "Message"]}
            formatEvent={(id, event) => (
              <tr key={id}>
                <td>{id}</td>
                <td>{formatTime(event.time)}</td>
                <td>{event.mode || 'regular'}</td>
                <td>{event.message || ''}</td>
              </tr>
            )}
          />

          <EventsTable
            events={events.periodic_events || {}}
            title="Periodic Events"
            headers={["ID", "Start", "Interval", "End", "Mode", "Message"]}
            formatEvent={(id, event) => (
              <tr key={id}>
                <td>{id}</td>
                <td>{formatTime(event.start_time)}</td>
                <td>{formatTime(event.interval)}</td>
                <td>{formatTime(event.end_time)}</td>
                <td>{event.mode || 'regular'}</td>
                <td>{event.message || ''}</td>
              </tr>
            )}
          />
        </div>
      </div>

      <div className="logs-section">
        <h2>Recent Logs</h2>
        <LogsTable logs={logs} />
      </div>
    </div>
  );
};

export default Dashboard;