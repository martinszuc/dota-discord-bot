import React, { useState, useEffect } from 'react';
import { fetchSettings, updateSettings } from '../api';
import './Settings.css';

const Settings = () => {
  const [guildId, setGuildId] = useState('');
  const [settings, setSettings] = useState({
    prefix: '!',
    timer_channel: 'timer-bot',
    voice_channel: 'DOTA',
    tts_language: 'en-US-AriaNeural',
    mindful_messages_enabled: false
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [isLoaded, setIsLoaded] = useState(false);

  // Available TTS voices
  const availableVoices = [
    { id: 'en-US-AriaNeural', name: 'Aria (US English)' },
    { id: 'en-GB-RyanNeural', name: 'Ryan (British English)' },
    { id: 'en-US-GuyNeural', name: 'Guy (US English)' },
    { id: 'en-US-JennyNeural', name: 'Jenny (US English)' },
    { id: 'en-GB-SoniaNeural', name: 'Sonia (British English)' },
    { id: 'de-DE-KatjaNeural', name: 'Katja (German)' },
    { id: 'es-ES-ElviraNeural', name: 'Elvira (Spanish)' },
    { id: 'fr-FR-DeniseNeural', name: 'Denise (French)' },
    { id: 'it-IT-ElsaNeural', name: 'Elsa (Italian)' },
    { id: 'ru-RU-SvetlanaNeural', name: 'Svetlana (Russian)' }
  ];

  // Load settings when guildId changes
  useEffect(() => {
    if (!guildId) return;

    const loadSettings = async () => {
      try {
        setLoading(true);
        setError(null);

        const response = await fetchSettings(guildId);
        setSettings(response.data);
        setIsLoaded(true);

        setLoading(false);
      } catch (err) {
        console.error('Error loading settings:', err);
        setError('Failed to load settings. Please check your connection.');
        setLoading(false);
      }
    };

    loadSettings();
  }, [guildId]);

  // Handle input changes
  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;

    setSettings(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  // Handle form submission
  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!guildId) {
      setError('Please enter a Guild ID');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      await updateSettings(guildId, settings);

      setSuccess('Settings updated successfully');
      setLoading(false);

      // Clear success message after 3 seconds
      setTimeout(() => {
        setSuccess(null);
      }, 3000);
    } catch (err) {
      console.error('Error updating settings:', err);
      setError('Failed to update settings: ' + (err.message || 'Unknown error'));
      setLoading(false);
    }
  };

  return (
    <div className="settings-container">
      <h1>Bot Settings</h1>

      <div className="guild-selector">
        <label htmlFor="guild-id">Guild ID:</label>
        <input
          type="text"
          id="guild-id"
          value={guildId}
          onChange={(e) => setGuildId(e.target.value)}
          placeholder="Enter Guild ID"
          className="guild-input"
        />
        {!isLoaded && guildId && !loading && (
          <button
            onClick={() => {
              setIsLoaded(false);
              setSettings({
                prefix: '!',
                timer_channel: 'timer-bot',
                voice_channel: 'DOTA',
                tts_language: 'en-US-AriaNeural',
                mindful_messages_enabled: false
              });
            }}
            className="load-button"
          >
            Load Settings
          </button>
        )}
      </div>

      {error && <div className="error-message">{error}</div>}
      {success && <div className="success-message">{success}</div>}

      {loading ? (
        <div className="loading">Loading settings...</div>
      ) : (
        <form onSubmit={handleSubmit} className="settings-form">
          <div className="settings-group">
            <h2>Command Settings</h2>

            <div className="form-group">
              <label htmlFor="prefix">Command Prefix:</label>
              <input
                type="text"
                id="prefix"
                name="prefix"
                value={settings.prefix}
                onChange={handleInputChange}
                placeholder="e.g., !"
                maxLength={3}
              />
              <span className="help-text">Character used before commands (e.g., !start)</span>
            </div>
          </div>

          <div className="settings-group">
            <h2>Channel Settings</h2>

            <div className="form-group">
              <label htmlFor="timer-channel">Timer Channel:</label>
              <input
                type="text"
                id="timer-channel"
                name="timer_channel"
                value={settings.timer_channel}
                onChange={handleInputChange}
                placeholder="e.g., timer-bot"
              />
              <span className="help-text">Text channel where timer messages are sent</span>
            </div>

            <div className="form-group">
              <label htmlFor="voice-channel">Voice Channel:</label>
              <input
                type="text"
                id="voice-channel"
                name="voice_channel"
                value={settings.voice_channel}
                onChange={handleInputChange}
                placeholder="e.g., DOTA"
              />
              <span className="help-text">Voice channel for TTS announcements</span>
            </div>
          </div>

          <div className="settings-group">
            <h2>Voice Settings</h2>

            <div className="form-group">
              <label htmlFor="tts-language">TTS Voice:</label>
              <select
                id="tts-language"
                name="tts_language"
                value={settings.tts_language}
                onChange={handleInputChange}
              >
                {availableVoices.map(voice => (
                  <option key={voice.id} value={voice.id}>
                    {voice.name}
                  </option>
                ))}
              </select>
              <span className="help-text">Voice used for text-to-speech announcements</span>
            </div>
          </div>

          <div className="settings-group">
            <h2>Mindful Messages</h2>

            <div className="form-group checkbox-group">
              <input
                type="checkbox"
                id="mindful-messages"
                name="mindful_messages_enabled"
                checked={settings.mindful_messages_enabled}
                onChange={handleInputChange}
              />
              <label htmlFor="mindful-messages">Enable Mindful Messages</label>
              <span className="help-text">Periodically send positive and encouraging messages during games</span>
            </div>
          </div>

          <div className="settings-group settings-actions">
            <button
              type="submit"
              className="save-button"
              disabled={loading || !guildId}
            >
              {loading ? 'Saving...' : 'Save Settings'}
            </button>

            <button
              type="button"
              className="reset-button"
              onClick={() => {
                setSettings({
                  prefix: '!',
                  timer_channel: 'timer-bot',
                  voice_channel: 'DOTA',
                  tts_language: 'en-US-AriaNeural',
                  mindful_messages_enabled: false
                });
              }}
            >
              Reset to Defaults
            </button>
          </div>
        </form>
      )}
    </div>
  );
};

export default Settings;