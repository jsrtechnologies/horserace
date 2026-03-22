import React, { useState, useEffect, useMemo } from 'react';
import { TrendingUp, Trophy, Filter, RefreshCw, Search, X, MapPin, Clock, DollarSign } from 'lucide-react';
import { predictionsApi } from '../services/api';

const Predictions = () => {
  const [bestBets, setBestBets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Filter states
  const [searchTerm, setSearchTerm] = useState('');
  const [venueFilter, setVenueFilter] = useState('all');
  const [confidenceFilter, setConfidenceFilter] = useState('all');
  const [distanceFilter, setDistanceFilter] = useState('all');
  const [oddsMin, setOddsMin] = useState(0);
  const [oddsMax, setOddsMax] = useState(100);
  const [showFilters, setShowFilters] = useState(false);

  // Get unique venues for filter
  const venues = useMemo(() => {
    const uniqueVenues = [...new Set(bestBets.map(bet => bet.venue))];
    return uniqueVenues.sort();
  }, [bestBets]);

  useEffect(() => {
    fetchBestBets();
  }, []);

  const fetchBestBets = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Fetch from local API
      const response = await predictionsApi.getBestBetsToday(20);
      if (response.data && response.data.best_bets) {
        setBestBets(response.data.best_bets);
      } else {
        setBestBets([]);
      }
      
    } catch (err) {
      console.error("Error fetching best bets:", err);
      setError("Failed to load predictions. Please try again.");
      setBestBets([]);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = () => {
    setLoading(true);
    fetchBestBets();
  };

  const handleClearFilters = () => {
    setSearchTerm('');
    setVenueFilter('all');
    setConfidenceFilter('all');
    setDistanceFilter('all');
    setOddsMin(0);
    setOddsMax(100);
  };

  // Apply all filters
  const filteredBets = useMemo(() => {
    return bestBets.filter(bet => {
      // Search filter
      if (searchTerm) {
        const term = searchTerm.toLowerCase();
        if (!bet.horse_name?.toLowerCase().includes(term) && 
            !bet.jockey_name?.toLowerCase().includes(term) &&
            !bet.venue?.toLowerCase().includes(term)) {
          return false;
        }
      }
      
      // Venue filter
      if (venueFilter !== 'all' && bet.venue !== venueFilter) {
        return false;
      }
      
      // Confidence filter
      if (confidenceFilter === 'high' && bet.confidence_score < 40) return false;
      if (confidenceFilter === 'medium' && (bet.confidence_score < 25 || bet.confidence_score >= 40)) return false;
      if (confidenceFilter === 'low' && bet.confidence_score >= 25) return false;
      
      // Distance filter
      if (distanceFilter !== 'all') {
        const dist = bet.distance;
        if (distanceFilter === 'sprint' && dist > 1400) return false;
        if (distanceFilter === 'middle' && (dist < 1400 || dist > 2000)) return false;
        if (distanceFilter === 'staying' && dist <= 2000) return false;
      }
      
      return true;
    });
  }, [bestBets, searchTerm, venueFilter, confidenceFilter, distanceFilter]);

  const hasActiveFilters = searchTerm || venueFilter !== 'all' || confidenceFilter !== 'all' || 
                           distanceFilter !== 'all' || oddsMin > 0 || oddsMax < 100;

  const getConfidenceColor = (score) => {
    if (score >= 40) return 'text-green-400';
    if (score >= 25) return 'text-yellow-400';
    return 'text-secondary-400';
  };

  const getConfidenceBadge = (score) => {
    if (score >= 40) return 'bg-green-500/20 text-green-400 border-green-500';
    if (score >= 25) return 'bg-yellow-500/20 text-yellow-400 border-yellow-500';
    return 'bg-secondary-700 text-secondary-400 border-secondary-600';
  };

  const formatRaceTime = (timeStr) => {
    if (!timeStr) return '';
    const date = new Date(timeStr);
    return date.toLocaleTimeString('en-AU', { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className="space-y-6 pt-14 lg:pt-0 animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-white">AI Predictions</h1>
          <p className="text-secondary-400 text-sm">Best bets and race predictions</p>
        </div>
        
        <div className="flex flex-wrap items-center gap-3">
          {/* Search */}
          <div className="relative">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-secondary-400" />
            <input
              type="text"
              placeholder="Search horse, jockey..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="bg-secondary-800 border border-secondary-700 rounded-lg pl-9 pr-3 py-1.5 sm:py-2 text-white text-sm focus:outline-none focus:border-primary-500 w-40 sm:w-48"
            />
          </div>

          {/* Filter Toggle */}
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`flex items-center gap-2 px-3 py-1.5 sm:px-4 sm:py-2 rounded-lg border transition-colors text-sm ${
              showFilters || hasActiveFilters 
                ? 'bg-primary-500/20 border-primary-500 text-primary-400' 
                : 'bg-secondary-800 border-secondary-700 hover:bg-secondary-700'
            }`}
          >
            <Filter className="w-4 h-4" />
            <span className="hidden sm:inline">Filters</span>
            {hasActiveFilters && (
              <span className="w-2 h-2 bg-primary-500 rounded-full"></span>
            )}
          </button>

          {/* Clear Filters */}
          {hasActiveFilters && (
            <button
              onClick={handleClearFilters}
              className="flex items-center gap-1 px-2 py-1.5 text-secondary-400 hover:text-white text-sm"
            >
              <X className="w-4 h-4" />
              <span className="hidden sm:inline">Clear</span>
            </button>
          )}

          <button
            onClick={handleRefresh}
            className="flex items-center gap-2 px-3 py-1.5 sm:px-4 sm:py-2 bg-secondary-800 hover:bg-secondary-700 rounded-lg border border-secondary-700 transition-colors text-sm"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            <span className="hidden sm:inline">Refresh</span>
          </button>
        </div>
      </div>

      {/* Expanded Filters Panel */}
      {showFilters && (
        <div className="bg-secondary-800 rounded-xl p-4 border border-secondary-700 animate-fadeIn">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Venue Filter */}
            <div>
              <label className="block text-sm text-secondary-400 mb-2 flex items-center gap-1">
                <MapPin className="w-4 h-4" />
                Venue
              </label>
              <select
                value={venueFilter}
                onChange={(e) => setVenueFilter(e.target.value)}
                className="w-full bg-secondary-700 border border-secondary-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-primary-500"
              >
                <option value="all">All Venues</option>
                {venues.map(venue => (
                  <option key={venue} value={venue}>{venue}</option>
                ))}
              </select>
            </div>

            {/* Confidence Filter */}
            <div>
              <label className="block text-sm text-secondary-400 mb-2 flex items-center gap-1">
                <TrendingUp className="w-4 h-4" />
                Confidence
              </label>
              <select
                value={confidenceFilter}
                onChange={(e) => setConfidenceFilter(e.target.value)}
                className="w-full bg-secondary-700 border border-secondary-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-primary-500"
              >
                <option value="all">All Confidence</option>
                <option value="high">High (40%+)</option>
                <option value="medium">Medium (25-40%)</option>
                <option value="low">Low (&lt;25%)</option>
              </select>
            </div>

            {/* Distance Filter */}
            <div>
              <label className="block text-sm text-secondary-400 mb-2 flex items-center gap-1">
                <Clock className="w-4 h-4" />
                Distance
              </label>
              <select
                value={distanceFilter}
                onChange={(e) => setDistanceFilter(e.target.value)}
                className="w-full border border-secondary- bg-secondary-700600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-primary-500"
              >
                <option value="all">All Distances</option>
                <option value="sprint">Sprint (&lt;1400m)</option>
                <option value="middle">Middle (1400-2000m)</option>
                <option value="staying">Staying (&gt;2000m)</option>
              </select>
            </div>

            {/* Odds Range */}
            <div>
              <label className="block text-sm text-secondary-400 mb-2 flex items-center gap-1">
                <DollarSign className="w-4 h-4" />
                Odds Range: {oddsMin} - {oddsMax}
              </label>
              <div className="flex items-center gap-2">
                <input
                  type="range"
                  min="0"
                  max="50"
                  value={oddsMin}
                  onChange={(e) => setOddsMin(parseInt(e.target.value))}
                  className="flex-1 h-2 bg-secondary-700 rounded-lg appearance-none cursor-pointer"
                />
                <input
                  type="range"
                  min="0"
                  max="50"
                  value={oddsMax}
                  onChange={(e) => setOddsMax(parseInt(e.target.value))}
                  className="flex-1 h-2 bg-secondary-700 rounded-lg appearance-none cursor-pointer"
                />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Stats Summary */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 sm:gap-4">
        <div className="bg-secondary-800 rounded-xl p-4 border border-secondary-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-secondary-400 text-sm">Total Picks</p>
              <p className="text-2xl font-bold text-white">{filteredBets.length}</p>
            </div>
            <Trophy className="w-8 h-8 text-primary-500" />
          </div>
        </div>
        <div className="bg-secondary-800 rounded-xl p-4 border border-secondary-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-secondary-400 text-sm">High Confidence</p>
              <p className="text-2xl font-bold text-green-400">
                {filteredBets.filter(b => b.confidence_score >= 40).length}
              </p>
            </div>
            <TrendingUp className="w-8 h-8 text-green-400" />
          </div>
        </div>
        <div className="bg-secondary-800 rounded-xl p-4 border border-secondary-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-secondary-400 text-sm">Medium Confidence</p>
              <p className="text-2xl font-bold text-yellow-400">
                {filteredBets.filter(b => b.confidence_score >= 25 && b.confidence_score < 40).length}
              </p>
            </div>
            <TrendingUp className="w-8 h-8 text-yellow-400" />
          </div>
        </div>
        <div className="bg-secondary-800 rounded-xl p-4 border border-secondary-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-secondary-400 text-sm">Avg. Win %</p>
              <p className="text-2xl font-bold text-primary-400">
                {filteredBets.length > 0 
                  ? (filteredBets.reduce((sum, b) => sum + b.win_probability, 0) / filteredBets.length).toFixed(1)
                  : 0}%
              </p>
            </div>
            <TrendingUp className="w-8 h-8 text-primary-400" />
          </div>
        </div>
      </div>

      {/* Best Bets List */}
      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500"></div>
        </div>
      ) : error ? (
        <div className="text-center py-12 bg-secondary-800 rounded-xl border border-red-500/50">
          <Trophy className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <p className="text-red-400">{error}</p>
          <button 
            onClick={handleRefresh}
            className="mt-4 px-4 py-2 bg-primary-500 hover:bg-primary-600 rounded-lg text-white"
          >
            Retry
          </button>
        </div>
      ) : filteredBets.length === 0 ? (
        <div className="text-center py-12 bg-secondary-800 rounded-xl border border-secondary-700">
          <Trophy className="w-12 h-12 text-secondary-600 mx-auto mb-4" />
          <p className="text-secondary-400">No predictions available.</p>
          <p className="text-sm text-secondary-500 mt-2">
            {hasActiveFilters ? "Try adjusting your filters." : 'Click "Refresh" to load predictions.'}
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredBets.map((bet, index) => (
            <div
              key={`${bet.race_id}-${bet.horse_name}`}
              className="bg-secondary-800 rounded-xl p-4 sm:p-6 border border-secondary-700 hover:border-primary-500/50 transition-colors"
            >
              <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
                {/* Race Info */}
                <div className="flex-1">
                  <div className="flex flex-wrap items-center gap-2 sm:gap-3 mb-2">
                    <span className="text-primary-500 font-bold">#{index + 1}</span>
                    <span className={`px-2 py-0.5 rounded text-xs border ${getConfidenceBadge(bet.confidence_score)}`}>
                      {bet.confidence_score}% Conf.
                    </span>
                    {bet.race_time && (
                      <span className="text-secondary-500 text-xs sm:text-sm">
                        {formatRaceTime(bet.race_time)}
                      </span>
                    )}
                  </div>
                  
                  <h3 className="text-base sm:text-lg font-bold text-white mb-1">{bet.horse_name}</h3>
                  <p className="text-secondary-400 text-sm mb-3">
                    {bet.race_name} @ {bet.venue} | {bet.distance}m
                  </p>
                  
                  <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm">
                    <div>
                      <span className="text-secondary-500">Jockey: </span>
                      <span className="text-white">{bet.jockey_name}</span>
                    </div>
                    <div>
                      <span className="text-secondary-500">Win: </span>
                      <span className="text-primary-400 font-semibold">{bet.win_probability?.toFixed(1)}%</span>
                    </div>
                  </div>
                </div>

                {/* Probability Bar */}
                <div className="text-right sm:min-w-[100px]">
                  <div className="w-24 sm:w-32 bg-secondary-700 rounded-full h-2.5 sm:h-3 overflow-hidden mb-2 mx-auto sm:mx-0">
                    <div
                      className="h-full bg-primary-500 probability-bar"
                      style={{ width: `${Math.min(bet.win_probability * 3, 100)}%` }}
                    />
                  </div>
                  <p className={`text-xl sm:text-2xl font-bold ${getConfidenceColor(bet.confidence_score)}`}>
                    {bet.confidence_score.toFixed(0)}%
                  </p>
                  <p className="text-xs text-secondary-500">Confidence</p>
                </div>
              </div>

              {/* Factors */}
              {bet.factors && (bet.factors.positive?.length > 0 || bet.factors.negative?.length > 0) && (
                <div className="mt-4 pt-4 border-t border-secondary-700">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
                    {bet.factors.positive?.length > 0 && (
                      <div>
                        <h4 className="text-xs font-medium text-green-400 mb-1">Positive Factors</h4>
                        <div className="flex flex-wrap gap-1">
                          {bet.factors.positive.map((factor, i) => (
                            <span
                              key={i}
                              className="px-2 py-0.5 bg-green-500/10 text-green-400 text-xs rounded"
                            >
                              {factor}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                    {bet.factors.negative?.length > 0 && (
                      <div>
                        <h4 className="text-xs font-medium text-red-400 mb-1">Negative Factors</h4>
                        <div className="flex flex-wrap gap-1">
                          {bet.factors.negative.map((factor, i) => (
                            <span
                              key={i}
                              className="px-2 py-0.5 bg-red-500/10 text-red-400 text-xs rounded"
                            >
                              {factor}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default Predictions;
