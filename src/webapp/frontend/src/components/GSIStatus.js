import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './GSIStatus.css';

const GSIStatus = () => {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        setLoading(true);
        const response = await axios.get('/api/gsi/status');
        setStatus(response.data.data);
        setError(null);
      } catch (err) {
        console.error('Error fetching GSI status:', err);
        setError('Failed to load GSI status');
      } finally {
        setLoading(false);
      }
    };

    // Fetch immediately
    fetchStatus();

    // Set up polling
    const interval = setInterval(fetchStatus, 5000);

    // Clean up
    return () => clearInterval(interval);
  }, []);

  const formatTime = (seconds) => {
    if (seconds === undefined || seconds === null) return '00:00';
    const minutes = Math.floor(Math.abs(seconds) / 60);
    const secs = Math.abs(seconds) % 60;
    return `${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  if (loading) {
    return <div className="gsi-loading">Loading GSI status...</div>;
  }

  if (error) {
    return <div className="gsi-error">{error}</div>;
  }

  return (
    <div className="gsi-status-container">
      <h2>Dota 2 GSI Status</h2>

      <div className="gsi-status-card">
        <div className="gsi-status-header">
          <div className={`status-indicator ${status?.connected ? 'connected' : 'disconnected'}`}>
            {status?.connected ? 'Connected' : 'Disconnected'}
          </div>

          {status?.last_update_seconds_ago !== null && (
            <div className="last-update">
              Last update: {Math.round(status.last_update_seconds_ago)} seconds ago
            </div>
          )}
        </div>

        {status?.connected && (
          <div className="gsi-status-details">
            <div className="status-row">
              <label>In Game:</label>
              <span className={status.in_game ? 'status-active' : 'status-inactive'}>
                {status.in_game ? 'Yes' : 'No'}
              </span>
            </div>

            {status.in_game && (
              <>
                {status.game_mode && (
                  <div className="status-row">
                    <label>Game Mode:</label>
                    <span>{status.game_mode.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}</span>
                  </div>
                )}

                {status.match_id && (
                  <div className="status-row">
                    <label>Match ID:</label>
                    <span>{status.match_id}</span>
                  </div>
                )}

                {status.game_time !== null && (
                  <div className="status-row">
                    <label>Game Time:</label>
                    <span>{formatTime(status.game_time)}</span>
                  </div>
                )}

                {status.player_team && (
                  <div className="status-row">
                    <label>Your Team:</label>
                    <span className={`team-${status.player_team.toLowerCase()}`}>
                      {status.player_team.charAt(0).toUpperCase() + status.player_team.slice(1)}
                    </span>
                  </div>
                )}
              </>
            )}
          </div>
        )}
      </div>

      {!status?.connected && (
        <div className="gsi-setup-instructions">
          <h3>GSI Setup Instructions</h3>
          <p>
            To enable Game State Integration with this bot, follow these steps:
          </p>
          <ol>
            <li>
              Create a file named <code>gamestate_integration_discord_bot.cfg</code> in your
              Dota 2 GSI configuration folder:
              <code>C:\Program Files (x86)\Steam\steamapps\common\dota 2 beta\game\dota\cfg\gamestate_integration\</code>
            </li>
            <li>
              Add the following content to the file:
              <pre>
{`"dota_discord_bot"
{
    "uri"           "http://20.56.9.182:5000/api/gsi"
    "timeout"       "5.0"
    "buffer"        "0.1"
    "throttle"      "0.1"
    "heartbeat"     "30.0"
    "data"
    {
        "provider"      "1"
        "map"           "1"
        "player"        "1"
        "hero"          "1"
        "abilities"     "1"
        "items"         "1"
        "draft"         "1"
        "wearables"     "0"
        "buildings"     "1"
        "events"        "1"
        "gamestate"     "1"
    }
    "auth"
    {
        "token"         "your_secret_token"
    }
}`}
              </pre>
            </li>
            <li>Restart Dota 2 if it's already running</li>
            <li>The connection status above should change to "Connected" once everything is set up correctly</li>
          </ol>
        </div>
      )}
    </div>
  );
};

export default GSIStatus;