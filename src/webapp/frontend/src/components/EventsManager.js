import React, { useState, useEffect } from 'react';
import { fetchEvents, addEvent, removeEvent } from '../api';
import './EventsManager.css';

const EventsManager = () => {
  const [events, setEvents] = useState({ static_events: {}, periodic_events: {} });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [guildId, setGuildId] = useState('');
  const [mode, setMode] = useState('regular');
  const [showAddForm, setShowAddForm] = useState(false);
  const [eventType, setEventType] = useState('static');
  const [formData, setFormData] = useState({
    time: '',
    start_time: '',
    interval: '',
    end_time: '',
    message: ''
  });
  const [submitting, setSubmitting] = useState(false);

  // Load events when guildId or mode changes
  useEffect(() => {
    const loadEvents = async () => {
      if (!guildId) return;

      try {
        setLoading(true);
        const data = await fetchEvents(guildId, mode);
        setEvents(data.data);
        setLoading(false);
      } catch (err) {
        console.error('Error loading events:', err);
        setError('Failed to load events. Please check your connection.');
        setLoading(false);
      }
    };

    loadEvents();
  }, [guildId, mode]);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value
    });
  };

  const handleAddEvent = async (e) => {
    e.preventDefault();

    if (!guildId) {
      setError('Please enter a Guild ID');
      return;
    }

    if (!formData.message) {
      setError('Message is required');
      return;
    }

    try {
      setSubmitting(true);

      const payload = {
        guild_id: guildId,
        type: eventType,
        mode: mode,
        message: formData.message
      };

      if (eventType === 'static') {
        if (!formData.time) {
          setError('Time is required for static events');
          setSubmitting(false);
          return;
        }
        payload.time = formData.time;
      } else {
        if (!formData.start_time || !formData.interval || !formData.end_time) {
          setError('Start time, interval, and end time are required for periodic events');
          setSubmitting(false);
          return;
        }
        payload.start_time = formData.start_time;
        payload.interval = formData.interval;
        payload.end_time = formData.end_time;
      }

      const result = await addEvent(payload);

      // Reload events
      const data = await fetchEvents(guildId, mode);
      setEvents(data.data);

      // Reset form
      setFormData({
        time: '',
        start_time: '',
        interval: '',
        end_time: '',
        message: ''
      });
      setShowAddForm(false);
      setError(null);
    } catch (err) {
      console.error('Error adding event:', err);
      setError('Failed to add event: ' + (err.message || 'Unknown error'));
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteEvent = async (eventId, eventType) => {
    if (!window.confirm('Are you sure you want to delete this event?')) {
      return;
    }

    try {
      await removeEvent(guildId, eventId);

      // Reload events
      const data = await fetchEvents(guildId, mode);
      setEvents(data.data);
    } catch (err) {
      console.error('Error deleting event:', err);
      setError('Failed to delete event: ' + (err.message || 'Unknown error'));
    }
  };

  // Helper function to format time in seconds to MM:SS
  const formatTime = (seconds) => {
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="events-manager">
      <h1>Events Manager</h1>

      <div className="controls">
        <div className="guild-input">
          <label htmlFor="guild-id">Guild ID:</label>
          <input
            type="text"
            id="guild-id"
            value={guildId}
            onChange={(e) => setGuildId(e.target.value)}
            placeholder="Enter Guild ID"
          />
        </div>

        <div className="mode-selector">
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
          className="add-button"
          onClick={() => setShowAddForm(!showAddForm)}
        >
          {showAddForm ? 'Cancel' : 'Add Event'}
        </button>
      </div>

      {error && <div className="error-message">{error}</div>}

      {showAddForm && (
        <div className="add-event-form">
          <h2>Add New Event</h2>
          <form onSubmit={handleAddEvent}>
            <div className="form-group">
              <label htmlFor="event-type">Event Type:</label>
              <select
                id="event-type"
                value={eventType}
                onChange={(e) => setEventType(e.target.value)}
              >
                <option value="static">Static Event</option>
                <option value="periodic">Periodic Event</option>
              </select>
            </div>

            {eventType === 'static' ? (
              <div className="form-group">
                <label htmlFor="time">Time (MM:SS or seconds):</label>
                <input
                  type="text"
                  id="time"
                  name="time"
                  value={formData.time}
                  onChange={handleInputChange}
                  placeholder="e.g., 10:00 or 600"
                  required
                />
              </div>
            ) : (
              <>
                <div className="form-group">
                  <label htmlFor="start-time">Start Time (MM:SS or seconds):</label>
                  <input
                    type="text"
                    id="start-time"
                    name="start_time"
                    value={formData.start_time}
                    onChange={handleInputChange}
                    placeholder="e.g., 05:00 or 300"
                    required
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="interval">Interval (MM:SS or seconds):</label>
                  <input
                    type="text"
                    id="interval"
                    name="interval"
                    value={formData.interval}
                    onChange={handleInputChange}
                    placeholder="e.g., 01:00 or 60"
                    required
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="end-time">End Time (MM:SS or seconds):</label>
                  <input
                    type="text"
                    id="end-time"
                    name="end_time"
                    value={formData.end_time}
                    onChange={handleInputChange}
                    placeholder="e.g., 30:00 or 1800"
                    required
                  />
                </div>
              </>
            )}

            <div className="form-group">
              <label htmlFor="message">Message:</label>
              <input
                type="text"
                id="message"
                name="message"
                value={formData.message}
                onChange={handleInputChange}
                placeholder="Enter the event message"
                required
              />
            </div>

            <button
              type="submit"
              className="submit-button"
              disabled={submitting}
            >
              {submitting ? 'Adding...' : 'Add Event'}
            </button>
          </form>
        </div>
      )}

      {loading ? (
        <div className="loading">Loading events...</div>
      ) : (
        <div className="events-container">
          <div className="events-section">
            <h2>Static Events</h2>
            {Object.keys(events.static_events).length === 0 ? (
              <p className="no-events">No static events found</p>
            ) : (
              <table className="events-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Time</th>
                    <th>Message</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(events.static_events).map(([id, event]) => (
                    <tr key={id}>
                      <td>{id}</td>
                      <td>{formatTime(event.time)}</td>
                      <td>{event.message}</td>
                      <td>
                        <button
                          className="delete-button"
                          onClick={() => handleDeleteEvent(id, 'static')}
                        >
                          Delete
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>

          <div className="events-section">
            <h2>Periodic Events</h2>
            {Object.keys(events.periodic_events).length === 0 ? (
              <p className="no-events">No periodic events found</p>
            ) : (
              <table className="events-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Start Time</th>
                    <th>Interval</th>
                    <th>End Time</th>
                    <th>Message</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(events.periodic_events).map(([id, event]) => (
                    <tr key={id}>
                      <td>{id}</td>
                      <td>{formatTime(event.start_time)}</td>
                      <td>{formatTime(event.interval)}</td>
                      <td>{formatTime(event.end_time)}</td>
                      <td>{event.message}</td>
                      <td>
                        <button
                          className="delete-button"
                          onClick={() => handleDeleteEvent(id, 'periodic')}
                        >
                          Delete
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default EventsManager;