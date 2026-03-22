import React, { useState, useEffect } from 'react';
import { Settings as SettingsIcon, Database, RefreshCw, Play, Check, AlertCircle, Zap } from 'lucide-react';
import { scrapingApi } from '../services/api';
import { generateDemoData } from '../services/demoData';

// Store demo data in localStorage for persistence
const DEMO_DATA_KEY = 'ausrace_demo_data';

const Settings = () => {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(null);
  const [isDemoMode, setIsDemoMode] = useState(false);
  const [demoProgress, setDemoProgress] = useState(0);

  useEffect(() => {
    // Check if demo data exists
    const stored = localStorage.getItem(DEMO_DATA_KEY);
    if (stored) {
      try {
        const data = JSON.parse(stored);
        setStatus({ database: data.stats });
        setIsDemoMode(true);
      } catch (e) {
        console.error("Error parsing stored demo data:", e);
      }
    }
    fetchStatus();
  }, []);

  const fetchStatus = async () => {
    try {
      const response = await scrapingApi.getStatus();
      setStatus(response.data);
    } catch (error) {
      console.error("Error fetching status:", error);
      // Use stored demo data if API fails
      const stored = localStorage.getItem(DEMO_DATA_KEY);
      if (stored) {
        try {
          const data = JSON.parse(stored);
          setStatus({ database: data.stats, isDemo: true });
        } catch (e) {}
      }
    }
  };

  const handleLoadDemoData = async () => {
    try {
      setLoading(true);
      setMessage(null);
      setDemoProgress(0);

      // Simulate progressive loading
      setDemoProgress(10);
      await new Promise(r => setTimeout(r, 300));
      
      setDemoProgress(30);
      // Generate demo data
      const data = generateDemoData(30); // 30 days of data
      setDemoProgress(60);
      
      // Store in localStorage
      localStorage.setItem(DEMO_DATA_KEY, JSON.stringify(data));
      setDemoProgress(90);
      
      setStatus({ database: data.stats, isDemo: true });
      setIsDemoMode(true);
      
      setDemoProgress(100);
      setMessage({ type: 'success', text: `Loaded ${data.stats.meetings} meetings, ${data.stats.races} races with full demo data!` });
      
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to load demo data' });
    } finally {
      setLoading(false);
      setTimeout(() => setDemoProgress(0), 1000);
    }
  };

  const handleLoad2YearsData = async () => {
    try {
      setLoading(true);
      setMessage(null);
      setDemoProgress(0);

      setDemoProgress(10);
      await new Promise(r => setTimeout(r, 300));
      
      setDemoProgress(30);
      // Generate 2 years of data
      const data = generateDemoData(730); // 730 days = 2 years
      setDemoProgress(60);
      
      // Store in localStorage
      localStorage.setItem(DEMO_DATA_KEY, JSON.stringify(data));
      setDemoProgress(90);
      
      setStatus({ database: data.stats, isDemo: true });
      setIsDemoMode(true);
      
      setDemoProgress(100);
      setMessage({ type: 'success', text: `Successfully loaded 2 years of data: ${data.stats.meetings} meetings, ${data.stats.races} races, ${data.stats.horses} horses!` });
      
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to load historical data' });
    } finally {
      setLoading(false);
      setTimeout(() => setDemoProgress(0), 1000);
    }
  };

  const handleScrapeRaces = async () => {
    try {
      setLoading(true);
      setMessage(null);
      await scrapingApi.scrapeRaces();
      setMessage({ type: 'success', text: 'Race scraping started!' });
      setTimeout(fetchStatus, 2000);
    } catch (error) {
      // Fallback to demo data
      setMessage({ type: 'warning', text: 'API not available. Using demo mode instead.' });
      await handleLoadDemoData();
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateWeather = async () => {
    try {
      setLoading(true);
      setMessage(null);
      const response = await scrapingApi.updateWeather();
      setMessage({ type: 'success', text: response.data.message });
      setTimeout(fetchStatus, 2000);
    } catch (error) {
      setMessage({ type: 'warning', text: 'API not available' });
    } finally {
      setLoading(false);
    }
  };

  const handleSeedData = async () => {
    try {
      setLoading(true);
      setMessage(null);
      const response = await scrapingApi.seedSampleData();
      setMessage({ type: 'success', text: response.data.message });
      setTimeout(fetchStatus, 2000);
    } catch (error) {
      setMessage({ type: 'warning', text: 'API not available. Using demo mode.' });
      await handleLoadDemoData();
    } finally {
      setLoading(false);
    }
  };

  const clearDemoData = () => {
    localStorage.removeItem(DEMO_DATA_KEY);
    setStatus(null);
    setIsDemoMode(false);
    setMessage({ type: 'success', text: 'Demo data cleared' });
  };

  const handleStartLiveUpdates = async () => {
    try {
      setLoading(true);
      setMessage(null);
      const response = await scrapingApi.startLiveUpdates();
      setMessage({ type: 'success', text: response.data.message || 'Live updates started!' });
      setTimeout(fetchStatus, 2000);
    } catch (error) {
      setMessage({ type: 'warning', text: 'API not available. Use demo mode.' });
    } finally {
      setLoading(false);
    }
  };

  const handleStopLiveUpdates = async () => {
    try {
      setLoading(true);
      setMessage(null);
      const response = await scrapingApi.stopLiveUpdates();
      setMessage({ type: 'success', text: response.data.message || 'Live updates stopped!' });
      setTimeout(fetchStatus, 2000);
    } catch (error) {
      setMessage({ type: 'warning', text: 'API not available' });
    } finally {
      setLoading(false);
    }
  };

  const handleRefreshData = async () => {
    try {
      setLoading(true);
      setMessage(null);
      setDemoProgress(20);
      const response = await scrapingApi.triggerRefresh();
      setDemoProgress(100);
      setMessage({ type: 'success', text: response.data.message || 'Data refresh started!' });
      setTimeout(() => {
        setDemoProgress(0);
        fetchStatus();
      }, 2000);
    } catch (error) {
      setMessage({ type: 'warning', text: 'API not available. Use demo mode.' });
    } finally {
      setLoading(false);
    }
  };

  const handleRefreshUpcoming = async () => {
    try {
      setLoading(true);
      setMessage(null);
      setDemoProgress(20);
      const response = await scrapingApi.triggerUpcomingRefresh(30);
      setDemoProgress(100);
      setMessage({ type: 'success', text: response.data.message || 'Upcoming events refresh started!' });
      setTimeout(() => {
        setDemoProgress(0);
        fetchStatus();
      }, 2000);
    } catch (error) {
      setMessage({ type: 'warning', text: 'API not available' });
    } finally {
      setLoading(false);
    }
  };

  const handleGetStats = async () => {
    try {
      setLoading(true);
      const response = await scrapingApi.getStats();
      setStatus({ database: response.data, isDemo: false });
      setMessage({ type: 'success', text: 'Database stats loaded!' });
    } catch (error) {
      setMessage({ type: 'warning', text: 'API not available' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white">Settings</h1>
        <p className="text-secondary-400">Manage data sources and system configuration</p>
      </div>

      {/* Demo Mode Banner */}
      {isDemoMode && (
        <div className="bg-primary-500/10 border border-primary-500 rounded-xl p-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Zap className="w-6 h-6 text-primary-400" />
<div>
              <p className="text-primary-400 font-medium">Demo Mode Active</p>
              <p className="text-sm text-secondary-400">Using generated sample data for demonstration</p>
            </div>
          </div>
          <button
            onClick={clearDemoData}
            className="px-3 py-1 text-sm text-secondary-400 hover:text-white"
          >
            Clear Data
          </button>
        </div>
      )}

      {/* Message */}
      {message && (
        <div className={`p-4 rounded-lg flex items-center gap-3 ${
          message.type === 'success' 
            ? 'bg-green-500/10 text-green-400 border border-green-500' 
            : message.type === 'warning'
            ? 'bg-yellow-500/10 text-yellow-400 border border-yellow-500'
            : 'bg-red-500/10 text-red-400 border border-red-500'
        }`}>
          {message.type === 'success' ? <Check className="w-5 h-5" /> : 
           message.type === 'warning' ? <AlertCircle className="w-5 h-5" /> : 
           <AlertCircle className="w-5 h-5" />}
          {message.text}
        </div>
      )}

      {/* Progress Bar */}
      {demoProgress > 0 && (
        <div className="bg-secondary-800 rounded-xl p-4 border border-secondary-700">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-secondary-400">Loading data...</span>
            <span className="text-sm text-primary-400">{demoProgress}%</span>
          </div>
          <div className="w-full bg-secondary-700 rounded-full h-2">
            <div 
              className="bg-primary-500 h-2 rounded-full transition-all duration-300"
              style={{ width: `${demoProgress}%` }}
            />
          </div>
        </div>
      )}

      {/* Database Status */}
      <div className="bg-secondary-800 rounded-xl p-6 border border-secondary-700">
        <div className="flex items-center gap-3 mb-4">
          <Database className="w-6 h-6 text-primary-500" />
          <h2 className="text-lg font-bold text-white">Database Status</h2>
          {isDemoMode && <span className="text-xs bg-primary-500/20 text-primary-400 px-2 py-1 rounded">DEMO</span>}
        </div>

        {status ? (
          <div className="grid grid-cols-4 gap-4">
            <div className="bg-secondary-700/50 rounded-lg p-4">
              <p className="text-secondary-400 text-sm">Venues</p>
              <p className="text-2xl font-bold text-white">{status.database?.venues || 0}</p>
            </div>
            <div className="bg-secondary-700/50 rounded-lg p-4">
              <p className="text-secondary-400 text-sm">Meetings</p>
              <p className="text-2xl font-bold text-white">{status.database?.meetings || 0}</p>
            </div>
            <div className="bg-secondary-700/50 rounded-lg p-4">
              <p className="text-secondary-400 text-sm">Races</p>
              <p className="text-2xl font-bold text-white">{status.database?.races || 0}</p>
            </div>
            <div className="bg-secondary-700/50 rounded-lg p-4">
              <p className="text-secondary-400 text-sm">Horses</p>
              <p className="text-2xl font-bold text-white">{status.database?.horses || 0}</p>
            </div>
            <div className="bg-secondary-700/50 rounded-lg p-4">
              <p className="text-secondary-400 text-sm">Jockeys</p>
              <p className="text-2xl font-bold text-white">{status.database?.jockeys || 0}</p>
            </div>
            <div className="bg-secondary-700/50 rounded-lg p-4">
              <p className="text-secondary-400 text-sm">Trainers</p>
              <p className="text-2xl font-bold text-white">{status.database?.trainers || 0}</p>
            </div>
            <div className="bg-secondary-700/50 rounded-lg p-4">
              <p className="text-secondary-400 text-sm">Participants</p>
              <p className="text-2xl font-bold text-white">{status.database?.participants || 0}</p>
            </div>
            <div className="bg-secondary-700/50 rounded-lg p-4">
              <p className="text-secondary-400 text-sm">Results</p>
              <p className="text-2xl font-bold text-white">{status.database?.results || 0}</p>
            </div>
          </div>
        ) : (
          <div className="text-center py-8 text-secondary-400">
            <Database className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p>No data loaded yet</p>
          </div>
        )}

        <div className="mt-4 pt-4 border-t border-secondary-700">
          <p className="text-sm text-secondary-500">
            {isDemoMode ? 'Using demo data' : 'Click "Load Demo Data" to get started'}
          </p>
        </div>
      </div>

      {/* Data Management */}
      <div className="bg-secondary-800 rounded-xl p-6 border border-secondary-700">
        <div className="flex items-center gap-3 mb-4">
          <SettingsIcon className="w-6 h-6 text-primary-500" />
          <h2 className="text-lg font-bold text-white">Data Management</h2>
        </div>

        <div className="space-y-4">
          {/* Load Demo Data */}
          <div className="flex items-center justify-between p-4 bg-secondary-700/50 rounded-lg">
            <div>
              <h3 className="font-medium text-white">Load Demo Data</h3>
              <p className="text-sm text-secondary-400">
                Generate realistic sample data with meetings, races, horses, odds
              </p>
            </div>
            <button
              onClick={handleLoadDemoData}
              disabled={loading}
              className="flex items-center gap-2 px-4 py-2 bg-primary-500 hover:bg-primary-600 disabled:opacity-50 rounded-lg transition-colors"
            >
              <Play className="w-4 h-4" />
              Load Demo
            </button>
          </div>

          {/* Load 2 Years Data */}
          <div className="flex items-center justify-between p-4 bg-primary-500/10 border border-primary-500/30 rounded-lg">
            <div>
              <h3 className="font-medium text-white">Load 2 Years Historical Data</h3>
              <p className="text-sm text-secondary-400">
                Generate 2 years of comprehensive race data for ML training
              </p>
            </div>
            <button
              onClick={handleLoad2YearsData}
              disabled={loading}
              className="flex items-center gap-2 px-4 py-2 bg-primary-600 hover:bg-primary-700 disabled:opacity-50 rounded-lg transition-colors"
            >
              <Zap className="w-4 h-4" />
              Load 2 Years
            </button>
          </div>

          {/* Scrape Races */}
          <div className="flex items-center justify-between p-4 bg-secondary-700/50 rounded-lg">
            <div>
              <h3 className="font-medium text-white">Scrape Race Data</h3>
              <p className="text-sm text-secondary-400">
                Fetch upcoming races from racing websites (requires backend)
              </p>
            </div>
            <button
              onClick={handleScrapeRaces}
              disabled={loading}
              className="flex items-center gap-2 px-4 py-2 bg-secondary-600 hover:bg-secondary-500 disabled:opacity-50 rounded-lg transition-colors"
            >
              <RefreshCw className="w-4 h-4" />
              Scrape
            </button>
          </div>

          {/* Update Weather */}
          <div className="flex items-center justify-between p-4 bg-secondary-700/50 rounded-lg">
            <div>
              <h3 className="font-medium text-white">Update Weather Data</h3>
              <p className="text-sm text-secondary-400">
                Refresh weather conditions (requires backend)
              </p>
            </div>
            <button
              onClick={handleUpdateWeather}
              disabled={loading}
              className="flex items-center gap-2 px-4 py-2 bg-secondary-600 hover:bg-secondary-500 disabled:opacity-50 rounded-lg transition-colors"
            >
              <RefreshCw className="w-4 h-4" />
              Update
            </button>
          </div>

          {/* Start Live Updates */}
          <div className="flex items-center justify-between p-4 bg-green-500/10 border border-green-500/30 rounded-lg">
            <div>
              <h3 className="font-medium text-white">Start Live Updates</h3>
              <p className="text-sm text-secondary-400">
                Enable real-time data updates every 60 seconds
              </p>
            </div>
            <button
              onClick={handleStartLiveUpdates}
              disabled={loading}
              className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 disabled:opacity-50 rounded-lg transition-colors"
            >
              <Zap className="w-4 h-4" />
              Start
            </button>
          </div>

          {/* Stop Live Updates */}
          <div className="flex items-center justify-between p-4 bg-red-500/10 border border-red-500/30 rounded-lg">
            <div>
              <h3 className="font-medium text-white">Stop Live Updates</h3>
              <p className="text-sm text-secondary-400">
                Disable real-time data updates
              </p>
            </div>
            <button
              onClick={handleStopLiveUpdates}
              disabled={loading}
              className="flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 disabled:opacity-50 rounded-lg transition-colors"
            >
              <Zap className="w-4 h-4" />
              Stop
            </button>
          </div>

          {/* Refresh Data */}
          <div className="flex items-center justify-between p-4 bg-secondary-700/50 rounded-lg">
            <div>
              <h3 className="font-medium text-white">Refresh All Data</h3>
              <p className="text-sm text-secondary-400">
                Update odds, check results, add upcoming events
              </p>
            </div>
            <button
              onClick={handleRefreshData}
              disabled={loading}
              className="flex items-center gap-2 px-4 py-2 bg-secondary-600 hover:bg-secondary-500 disabled:opacity-50 rounded-lg transition-colors"
            >
              <RefreshCw className="w-4 h-4" />
              Refresh
            </button>
          </div>

          {/* Refresh Upcoming Events */}
          <div className="flex items-center justify-between p-4 bg-secondary-700/50 rounded-lg">
            <div>
              <h3 className="font-medium text-white">Refresh Upcoming Events</h3>
              <p className="text-sm text-secondary-400">
                Add/update upcoming race events for next 30 days
              </p>
            </div>
            <button
              onClick={handleRefreshUpcoming}
              disabled={loading}
              className="flex items-center gap-2 px-4 py-2 bg-secondary-600 hover:bg-secondary-500 disabled:opacity-50 rounded-lg transition-colors"
            >
              <RefreshCw className="w-4 h-4" />
              Update
            </button>
          </div>

          {/* Get Database Stats */}
          <div className="flex items-center justify-between p-4 bg-secondary-700/50 rounded-lg">
            <div>
              <h3 className="font-medium text-white">View Database Stats</h3>
              <p className="text-sm text-secondary-400">
                View detailed database statistics including race counts
              </p>
            </div>
            <button
              onClick={handleGetStats}
              disabled={loading}
              className="flex items-center gap-2 px-4 py-2 bg-secondary-600 hover:bg-secondary-500 disabled:opacity-50 rounded-lg transition-colors"
            >
              <Database className="w-4 h-4" />
              View Stats
            </button>
          </div>
        </div>
      </div>

      {/* About */}
      <div className="bg-secondary-800 rounded-xl p-6 border border-secondary-700">
        <h2 className="text-lg font-bold text-white mb-4">About AusRace Predictor AI</h2>
        <div className="space-y-2 text-sm text-secondary-400">
          <p><strong className="text-white">Version:</strong> 1.0.0</p>
          <p><strong className="text-white">ML Model:</strong> XGBoost Classifier</p>
          <p><strong className="text-white">Features:</strong> 30+ features including horse form, jockey/trainer stats, track conditions</p>
          <p><strong className="text-white">Data Sources:</strong> Racing.com, Punters.com.au</p>
          <p><strong className="text-white">Demo Mode:</strong> Works standalone without backend</p>
        </div>
      </div>
    </div>
  );
};

export default Settings;
