import axios from 'axios';

// Create an axios instance with base URL and common config
const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  }
});

// Add request interceptor to add authorization token to requests
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add response interceptor to handle 401 Unauthorized errors
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    if (error.response && error.response.status === 401) {
      // Clear any stored credentials and reload the page
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth endpoints
export const login = (username, password) => {
  return axios.post('/auth/login', { username, password });
};

export const logout = () => {
  return api.post('/auth/logout');
};

// Status endpoints
export const fetchStatus = () => {
  return api.get('/status');
};

// Timer endpoints
export const fetchTimers = () => {
  return api.get('/timers');
};

export const startTimer = (guild_id, countdown, mode = 'regular') => {
  return api.post('/timers/start', { guild_id, countdown, mode });
};

export const stopTimer = (guild_id) => {
  return api.post('/timers/stop', { guild_id });
};

export const pauseTimer = (guild_id) => {
  return api.post('/timers/pause', { guild_id });
};

export const unpauseTimer = (guild_id) => {
  return api.post('/timers/unpause', { guild_id });
};

// Events endpoints
export const fetchEvents = (guild_id, mode = 'regular') => {
  return api.get(`/events?guild_id=${guild_id}&mode=${mode}`);
};

export const addEvent = (eventData) => {
  return api.post('/events', eventData);
};

export const removeEvent = (guild_id, event_id) => {
  return api.delete(`/events/${event_id}?guild_id=${guild_id}`);
};

// Settings endpoints
export const fetchSettings = (guild_id) => {
  return api.get(`/settings?guild_id=${guild_id}`);
};

export const updateSettings = (guild_id, settings) => {
  return api.put('/settings', { guild_id, settings });
};

// Special commands endpoints
export const startRoshanTimer = (guild_id) => {
  return api.post('/commands/roshan', { guild_id, action: 'start' });
};

export const cancelRoshanTimer = (guild_id) => {
  return api.post('/commands/roshan', { guild_id, action: 'cancel' });
};

export const startGlyphTimer = (guild_id) => {
  return api.post('/commands/glyph', { guild_id, action: 'start' });
};

export const cancelGlyphTimer = (guild_id) => {
  return api.post('/commands/glyph', { guild_id, action: 'cancel' });
};

export const startTormentorTimer = (guild_id) => {
  return api.post('/commands/tormentor', { guild_id, action: 'start' });
};

export const cancelTormentorTimer = (guild_id) => {
  return api.post('/commands/tormentor', { guild_id, action: 'cancel' });
};

// Logs endpoint
export const fetchLogs = (limit = 100, offset = 0) => {
  return api.get(`/logs?limit=${limit}&offset=${offset}`);
};