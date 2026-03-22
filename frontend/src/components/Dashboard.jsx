import React, { useState, useEffect, useMemo } from 'react';
import { 
  Calendar, 
  MapPin, 
  Clock, 
  TrendingUp, 
  RefreshCw,
  Cloud,
  Search,
  Filter,
  X
} from 'lucide-react';
import { racesApi, predictionsApi, scrapingApi } from '../services/api';

const Dashboard = () => {
  const [upcomingRaces, setUpcomingRaces] = useState([]);
  const [bestBets, setBestBets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    venues: 0,
    meetings: 0,
    races: 0,
    horses: 0
  });
  const [error, setError] = useState(null);
  
  // Filter states
  const [searchTerm, setSearchTerm] = useState('');
  const [venueFilter, setVenueFilter] = useState('all');
  const [trackFilter, setTrackFilter] = useState('all');
  const [distanceFilter, setDistanceFilter] = useState('all');
  const [showFilters, setShowFilters] = useState(false);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Fetch races
      const racesRes = await racesApi.getUpcoming(48);
      if (racesRes.data && racesRes.data.races) {
        setUpcomingRaces(racesRes.data.races || []);
      }
        
      // Fetch predictions
      try {
        const betsRes = await predictionsApi.getBestBetsToday(5);
        if (betsRes.data && betsRes.data.best_bets) {
          setBestBets(betsRes.data.best_bets || []);
        }
      } catch (e) {
        console.log("No predictions available");
        setBestBets([]);
      }

      // Fetch stats
      try {
        const statusRes = await scrapingApi.getStats();
        if (statusRes.data) {
          setStats({
            venues: statusRes.data.venues || 0,
            meetings: statusRes.data.meetings || 0,
            races: statusRes.data.races || 0,
            horses: statusRes.data.horses || 0
          });
        }
      } catch (e) {
        console.log("No stats available");
      }

    } catch (error) {
      console.error("Error fetching dashboard data:", error);
      setError("Failed to load data. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = () => {
    setLoading(true);
    fetchDashboardData();
  };

  // Get unique venues for filter
  const venues = useMemo(() => {
    const uniqueVenues = [...new Set(upcomingRaces.map(r => r.venue))];
    return uniqueVenues.sort();
  }, [upcomingRaces]);

  // Apply filters
  const filteredRaces = useMemo(() => {
    return upcomingRaces.filter(race => {
      // Search filter
      if (searchTerm) {
        const term = searchTerm.toLowerCase();
        if (!race.venue?.toLowerCase().includes(term) && 
            !race.race_name?.toLowerCase().includes(term)) {
          return false;
        }
      }
      
      // Venue filter
      if (venueFilter !== 'all' && race.venue !== venueFilter) {
        return false;
      }
      
      // Track filter
      if (trackFilter !== 'all') {
        const rating = race.track_rating?.toLowerCase() || '';
        if (trackFilter === 'good' && !rating.includes('good')) return false;
        if (trackFilter === 'soft' && !rating.includes('soft')) return false;
        if (trackFilter === 'heavy' && !rating.includes('heavy')) return false;
      }
      
      // Distance filter
      if (distanceFilter !== 'all') {
        const dist = race.distance;
        if (distanceFilter === 'sprint' && dist > 1400) return false;
        if (distanceFilter === 'middle' && (dist < 1400 || dist > 2000)) return false;
        if (distanceFilter === 'staying' && dist <= 2000) return false;
      }
      
      return true;
    });
  }, [upcomingRaces, searchTerm, venueFilter, trackFilter, distanceFilter]);

  const hasActiveFilters = searchTerm || venueFilter !== 'all' || trackFilter !== 'all' || distanceFilter !== 'all';

  const handleClearFilters = () => {
    setSearchTerm('');
    setVenueFilter('all');
    setTrackFilter('all');
    setDistanceFilter('all');
  };

  const formatTime = (timeStr) => {
    if (!timeStr) return '';
    const date = new Date(timeStr);
    return date.toLocaleTimeString('en-AU', { hour: '2-digit', minute: '2-digit' });
  };

  const getTrackRatingColor = (rating) => {
    if (!rating) return 'bg-secondary-600';
    const lower = rating.toLowerCase();
    if (lower.includes('heavy')) return 'bg-red-600';
    if (lower.includes('soft')) return 'bg-yellow-600';
    if (lower.includes('good')) return 'bg-green-600';
    return 'bg-secondary-600';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-4 md:space-y-6 animate-fadeIn pt-14 lg:pt-0">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl md:text-2xl font-bold text-white">Dashboard</h1>
          <p className="text-sm md:text-base text-secondary-400">Australian Horse Racing Predictions</p>
        </div>
        
        <div className="flex flex-wrap items-center gap-2">
          {/* Search */}
          <div className="relative">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-secondary-400" />
            <input
              type="text"
              placeholder="Search..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="bg-secondary-800 border border-secondary-700 rounded-lg pl-9 pr-3 py-1.5 text-white text-sm focus:outline-none focus:border-primary-500 w-32"
            />
          </div>
          
          {/* Filter Toggle */}
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border transition-colors text-sm ${
              showFilters || hasActiveFilters 
                ? 'bg-primary-500/20 border-primary-500 text-primary-400' 
                : 'bg-secondary-800 border-secondary-700 hover:bg-secondary-700'
            }`}
          >
            <Filter className="w-4 h-4" />
            <span className="hidden sm:inline">Filters</span>
          </button>
          
          {/* Clear Filters */}
          {hasActiveFilters && (
            <button
              onClick={handleClearFilters}
              className="flex items-center gap-1 px-2 py-1.5 text-secondary-400 hover:text-white text-sm"
            >
              <X className="w-4 h-4" />
            </button>
          )}
          
          <button
            onClick={handleRefresh}
            className="flex items-center justify-center gap-2 px-4 py-2 bg-primary-500 hover:bg-primary-600 rounded-lg transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            <span className="hidden sm:inline">Refresh Data</span>
            <span className="sm:hidden">Refresh</span>
          </button>
        </div>
      </div>

      {/* Filters Panel */}
      {showFilters && (
        <div className="bg-secondary-800 rounded-xl p-4 border border-secondary-700 animate-fadeIn">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
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

            {/* Track Condition Filter */}
            <div>
              <label className="block text-sm text-secondary-400 mb-2 flex items-center gap-1">
                <Cloud className="w-4 h-4" />
                Track Condition
              </label>
              <select
                value={trackFilter}
                onChange={(e) => setTrackFilter(e.target.value)}
                className="w-full bg-secondary-700 border border-secondary-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-primary-500"
              >
                <option value="all">All Conditions</option>
                <option value="good">Good</option>
                <option value="soft">Soft</option>
                <option value="heavy">Heavy</option>
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
                className="w-full bg-secondary-700 border border-secondary-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-primary-500"
              >
                <option value="all">All Distances</option>
                <option value="sprint">Sprint (&lt;1400m)</option>
                <option value="middle">Middle (1400-2000m)</option>
                <option value="staying">Staying (&gt;2000m)</option>
              </select>
            </div>
          </div>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 text-red-400">
          {error}
        </div>
      )}

      {/* Stats Cards - Responsive Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 md:gap-4">
        <div className="bg-secondary-800 rounded-xl p-3 md:p-4 border border-secondary-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs md:text-sm text-secondary-400">Venues</p>
              <p className="text-xl md:text-2xl font-bold text-white">{stats.venues}</p>
            </div>
            <MapPin className="w-6 md:w-8 h-6 md:h-8 text-primary-500" />
          </div>
        </div>
        <div className="bg-secondary-800 rounded-xl p-3 md:p-4 border border-secondary-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs md:text-sm text-secondary-400">Meetings</p>
              <p className="text-xl md:text-2xl font-bold text-white">{stats.meetings}</p>
            </div>
            <Calendar className="w-6 md:w-8 h-6 md:h-8 text-primary-500" />
          </div>
        </div>
        <div className="bg-secondary-800 rounded-xl p-3 md:p-4 border border-secondary-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs md:text-sm text-secondary-400">Races</p>
              <p className="text-xl md:text-2xl font-bold text-white">{stats.races}</p>
            </div>
            <Clock className="w-6 md:w-8 h-6 md:h-8 text-primary-500" />
          </div>
        </div>
        <div className="bg-secondary-800 rounded-xl p-3 md:p-4 border border-secondary-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs md:text-sm text-secondary-400">Horses</p>
              <p className="text-xl md:text-2xl font-bold text-white">{stats.horses}</p>
            </div>
            <TrendingUp className="w-6 md:w-8 h-6 md:h-8 text-primary-500" />
          </div>
        </div>
      </div>

      {/* Best Bets Section */}
      {bestBets.length > 0 && (
        <div className="bg-secondary-800 rounded-xl p-4 md:p-6 border border-secondary-700">
          <h2 className="text-base md:text-lg font-bold text-white mb-3 md:mb-4 flex items-center gap-2"> 
            <TrendingUp className="w-5 h-5 text-primary-500" />
            Best Bets Today
          </h2>
          <div className="space-y-2 md:space-y-3">
            {bestBets.map((bet, index) => (
              <div 
                key={`${bet.race_id}-${bet.horse_name}`}
                className="flex items-center justify-between p-3 md:p-4 bg-secondary-700/50 rounded-lg"
              >
                <div className="flex items-center gap-2 md:gap-4 min-w-0">
                  <span className="text-primary-500 font-bold shrink-0">#{index + 1}</span>
                  <div className="min-w-0">
                    <p className="font-semibold text-white text-sm md:text-base truncate">{bet.horse_name}</p>
                    <p className="text-xs md:text-sm text-secondary-400 truncate">
                      {bet.race_name} @ {bet.venue}
                    </p>
                  </div>
                </div>
                <div className="text-right shrink-0 ml-2">
                  <p className="text-base md:text-lg font-bold text-primary-400">
                    {bet.win_probability?.toFixed(0)}%
                  </p>
                  <p className="text-xs text-secondary-400 hidden sm:block">
                    Confidence: {bet.confidence_score?.toFixed(0)}%
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Upcoming Races */}
      <div className="bg-secondary-800 rounded-xl p-4 md:p-6 border border-secondary-700">
        <h2 className="text-base md:text-lg font-bold text-white mb-3 md:mb-4 flex items-center gap-2">
          <Calendar className="w-5 h-5 text-primary-500" />
          <span className="hidden sm:inline">Upcoming Races (Next 48 Hours)</span>
          <span className="sm:hidden">Upcoming Races</span>
          {hasActiveFilters && (
            <span className="ml-2 text-xs text-secondary-400">
              ({filteredRaces.length} of {upcomingRaces.length})
            </span>
          )}
        </h2>
        
        {filteredRaces.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-secondary-400 mb-4">
              {hasActiveFilters ? "No races match your filters." : "No upcoming races found."}
            </p>
            {hasActiveFilters && (
              <button 
                onClick={handleClearFilters}
                className="text-primary-400 hover:text-primary-300 text-sm"
              >
                Clear filters
              </button>
            )}
          </div>
        ) : (
          <div className="overflow-x-auto scroll-container -mx-4 md:mx-0 px-4 md:px-0">
            <table className="w-full min-w-[500px] md:min-w-0">
              <thead>
                <tr className="text-left text-xs md:text-sm text-secondary-400 border-b border-secondary-700">
                  <th className="pb-2 md:pb-3">Time</th>
                  <th className="pb-2 md:pb-3">Venue</th>
                  <th className="pb-2 md:pb-3">Race</th>
                  <th className="pb-2 md:pb-3 hidden sm:table-cell">Dist</th>
                  <th className="pb-2 md:pb-3">Track</th>
                  <th className="pb-2 md:pb-3 hidden md:table-cell">Weather</th>
                </tr>
              </thead>
              <tbody>
                {filteredRaces.map((race, index) => (
                  <tr 
                    key={`${race.id}-${race.venue}`}
                    className="border-b border-secondary-700/50 hover:bg-secondary-700/30"
                  >
                    <td className="py-2 md:py-3 font-mono text-primary-400 text-sm"> 
                      {formatTime(race.race_time)}
                    </td>
                    <td className="py-2 md:py-3 text-white text-sm">{race.venue}</td>
                    <td className="py-2 md:py-3 text-secondary-300 text-sm">
                      {race.race_name || `Race ${race.race_number}`}
                    </td>
                    <td className="py-2 md:py-3 text-secondary-300 text-sm hidden sm:table-cell">{race.distance}m</td>
                    <td className="py-2 md:py-3">
                      <span className={`px-2 py-0.5 md:py-1 rounded text-xs text-white ${getTrackRatingColor(race.track_rating)}`}>
                        {race.track_rating || 'N/A'}
                      </span>
                    </td>
                    <td className="py-2 md:py-3 text-secondary-300 text-sm hidden md:table-cell">
                      <div className="flex items-center gap-1">
                        <Cloud className="w-3 md:w-4 h-3 md:h-4" />
                        {race.weather || 'N/A'}
                      </div>
                    </td>
                  </tr>
))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;
