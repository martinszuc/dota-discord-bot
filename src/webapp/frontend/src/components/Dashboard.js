import React, { useState, useEffect } from 'react';
import { fetchStatus, fetchLogs, fetchEvents } from '../api';
import './Dashboard.css';

const Dashboard = () => {
  const [status, setStatus] = useState({ bot_running: false, active_timers_count: 0, active_timers: {} });
  const [logs, setLogs] = useState([]);
  const [events, setEvents] = useState({ static_events: {}, periodic_events: {} });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeGuild, setActiveGuild] = useState(null);

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);

        // Fetch bot status
        try {
          const statusData = await fetchStatus();
          setStatus(statusData.data || { bot_running: false, active_timers_count: 0, active_timers: {} });

          // Set active guild if there's at least one active timer
          if (statusData.data.active_timers_count > 0) {
            const guildIds = Object.keys(statusData.data.active_timers);
            setActiveGuild(guildIds[0]);

            // Fetch events for this guild
            try {
              const eventsData = await fetchEvents(guildIds[0]);
              setEvents(eventsData.data || { static_events: {}, periodic_events: {} });
            } catch (err) {
              console.error("Error fetching events:", err);
            }
          } else {
            // If no active timers, try to fetch events with a default guild ID
            try {
              const defaultGuildId = "279614276338188288";  // A placeholder ID
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
      } catch (err) {
        console.error('Error loading dashboard data:', err);
        setError('Failed to load dashboard data. Please try again.');
        setLoading(false);
      }
    };

    loadData();

    // Set up polling for updates every 5 seconds
    const interval = setInterval(loadData, 5000);

    return () => clearInterval(interval);
  }, []);

  const formatTime = (seconds) => {
    if (seconds === undefined || seconds === null) return '00:00';
    const minutes = Math.floor(Math.abs(seconds) / 60);
    const secs = Math.abs(seconds) % 60;
    const sign = seconds < 0 ? '-' : '';
    return `${sign}${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  if (loading) {
    return <div className="loading">Loading dashboard data...</div>;
  }

  return (
    <div className="dashboard">
      <h1>Dota Timer Bot Dashboard</h1>

      <div className="status-section">
        <h2>Bot Status</h2>
        <div className="status-indicator">
          <span className={`status-dot ${status?.bot_running ? 'online' : 'offline'}`}></span>
          <span>{status?.bot_running ? 'Online' : 'Offline'}</span>
        </div>
        <div className="status-detail">
          <p>Active Timers: {status?.active_timers_count || 0}</p>
        </div>
      </div>

      {status?.active_timers_count > 0 && activeGuild && (
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
              <div className="timer-card">
                <h3>Game Timer</h3>
                <div className="timer-info">
                  <p>Mode: <span className="highlight">{status.active_timers[activeGuild].mode || 'regular'}</span></p>
                  <p>Time: <span className="highlight">{formatTime(status.active_timers[activeGuild].elapsed_time)}</span></p>
                  <p>Status: <span className="highlight">{status.active_timers[activeGuild].paused ? 'Paused' : 'Running'}</span></p>
                </div>
              </div>

              <div className="sub-timers">
                <div className={`timer-card mini ${status.active_timers[activeGuild].roshan_active ? 'active' : 'inactive'}`}>
                  <h4>Roshan</h4>
                  <div className="timer-status">
                    {status.active_timers[activeGuild].roshan_active ? 'Active' : 'Inactive'}
                  </div>
                </div>

                <div className={`timer-card mini ${status.active_timers[activeGuild].glyph_active ? 'active' : 'inactive'}`}>
                  <h4>Glyph</h4>
                  <div className="timer-status">
                    {status.active_timers[activeGuild].glyph_active ? 'Active' : 'Inactive'}
                  </div>
                </div>

                <div className={`timer-card mini ${status.active_timers[activeGuild].tormentor_active ? 'active' : 'inactive'}`}>
                  <h4>Tormentor</h4>
                  <div className="timer-status">
                    {status.active_timers[activeGuild].tormentor_active ? 'Active' : 'Inactive'}
                  </div>
                </div>
              </div>

              <div className="recent-events">
                <h3>Recent Events</h3>
                <ul className="events-list">
                  {Array.isArray(status.active_timers[activeGuild].recent_events) &&
                    status.active_timers[activeGuild].recent_events.length > 0 ? (
                    status.active_timers[activeGuild].recent_events.map((event, index) => (
                      <li key={index}>{event}</li>
                    ))
                  ) : (
                    <li>No recent events</li>
                  )}
                </ul>
              </div>
            </div>
          )}
        </div>
      )}

      <div className="events-section">
        <h2>All Events</h2>
        <div className="events-container">
          <div className="event-type">
            <h3>Static Events</h3>
            {!events.static_events || Object.keys(events.static_events).length === 0 ? (
              <p className="no-events">No static events found</p>
            ) : (
              <table className="events-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Time</th>
                    <th>Mode</th>
                    <th>Message</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(events.static_events || {}).map(([id, event]) => (
                    <tr key={id}>
                      <td>{id}</td>
                      <td>{formatTime(event.time)}</td>
                      <td>{event.mode || 'regular'}</td>
                      <td>{event.message || ''}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>

          <div className="event-type">
            <h3>Periodic Events</h3>
            {!events.periodic_events || Object.keys(events.periodic_events).length === 0 ? (
              <p className="no-events">No periodic events found</p>
            ) : (
              <table className="events-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Start</th>
                    <th>Interval</th>
                    <th>End</th>
                    <th>Mode</th>
                    <th>Message</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(events.periodic_events || {}).map(([id, event]) => (
                    <tr key={id}>
                      <td>{id}</td>
                      <td>{formatTime(event.start_time)}</td>
                      <td>{formatTime(event.interval)}</td>
                      <td>{formatTime(event.end_time)}</td>
                      <td>{event.mode || 'regular'}</td>
                      <td>{event.message || ''}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      </div>

      <div className="logs-section">
        <h2>Recent Logs</h2>
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
      </div>
    </div>
  );
};

export default Dashboard;