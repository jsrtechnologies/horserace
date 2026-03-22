import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Races API
export const racesApi = {
  getAll: (params) => api.get('/races/', { params }),
  getById: (id) => api.get(`/races/${id}`),
  getMeetings: (params) => api.get('/races/meetings/', { params }),
  getUpcoming: (hours = 24) => api.get(`/races/upcoming/?hours=${hours}`),
  getVenues: (state) => api.get('/races/venues/', { params: { state } }),
  createRace: (data) => api.post('/races/', data),
  createMeeting: (data) => api.post('/races/meetings/', data),
  createVenue: (data) => api.post('/races/venues/', data),
};

// Predictions API
export const predictionsApi = {
  getByRaceId: (raceId) => api.get(`/predictions/${raceId}`),
  generate: (raceId) => api.post(`/predictions/generate/${raceId}`),
  clear: (raceId) => api.post(`/predictions/clear/${raceId}`),
  getBestBetsToday: (limit = 10) => api.get(`/predictions/best-bet/today?limit=${limit}`),
};

// Scraping API
export const scrapingApi = {
  scrapeRaces: () => api.post('/scraping/scrape-races'),
  scrapeResults: (days = 1) => api.post(`/scraping/scrape-results?days=${days}`),
  updateWeather: () => api.post('/scraping/update-weather'),
  getStatus: () => api.get('/scraping/status'),
  seedSampleData: () => api.post('/scraping/seed-sample-data'),
  // New endpoints for historical data loading
  loadHistorical: (days = 730) => api.post(`/scraping/load-historical?days_back=${days}`),
  getHistoricalStatus: () => api.get('/scraping/load-historical/status'),
  // Live updates
  startLiveUpdates: () => api.post('/scraping/live/start'),
  stopLiveUpdates: () => api.post('/scraping/live/stop'),
  getLiveStatus: () => api.get('/scraping/live/status'),
  getLiveRaces: () => api.get('/scraping/live/races'),
  getUpcomingWithOdds: (hours = 24) => api.get(`/scraping/live/upcoming?hours=${hours}`),
  // Database stats and refresh
  getStats: () => api.get('/scraping/stats'),
  triggerRefresh: () => api.post('/scraping/refresh'),
  triggerUpcomingRefresh: (days = 30) => api.post(`/scraping/refresh-upcoming?days=${days}`),
};

export default api;
