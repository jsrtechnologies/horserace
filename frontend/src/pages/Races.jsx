import React, { useState, useEffect } from 'react';
import { Calendar, RefreshCw } from 'lucide-react';
import { racesApi, predictionsApi } from '../services/api';
import { generateDemoData, generateBestBets } from '../services/demoData';
import RaceCard from '../components/RaceCard';
import PredictionTable from '../components/PredictionTable';
import WeatherWidget from '../components/WeatherWidget';

const Races = () => {
  const [races, setRaces] = useState([]);
  const [selectedRace, setSelectedRace] = useState(null);
  const [predictions, setPredictions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [date, setDate] = useState(new Date().toISOString().split('T')[0]);
  const [isDemoMode, setIsDemoMode] = useState(false);

  useEffect(() => {
    fetchRaces();
  }, [date]);

  const fetchRaces = async () => {
    try {
      setLoading(true);
      
      // Try API first
      try {
        const response = await racesApi.getAll({ date });
        if (response.data && response.data.length > 0) {
          setRaces(response.data);
          if (!selectedRace && response.data.length > 0) {
            selectRace(response.data[0]);
          }
        } else {
          // No data from API, use demo
          loadDemoRaces();
        }
      } catch (apiError) {
        console.log("API not available, using demo data");
        loadDemoRaces();
      }
    } catch (error) {
      console.error("Error fetching races:", error);
      loadDemoRaces();
    } finally {
      setLoading(false);
    }
  };

  const loadDemoRaces = () => {
    // Check localStorage for demo data
    let stored;
    try {
      stored = localStorage.getItem('ausrace_demo_data');
    } catch (e) {
      stored = null;
    }
    
    let data;
    if (stored) {
      try {
        data = JSON.parse(stored);
      } catch (e) {
        data = generateDemoData(30);
        localStorage.setItem('ausrace_demo_data', JSON.stringify(data));
      }
    } else {
      data = generateDemoData(30);
      localStorage.setItem('ausrace_demo_data', JSON.stringify(data));
    }
    
    // Filter races by selected date
    const targetDate = new Date(date);
    const filteredRaces = (data.races || []).filter(r => {
      const raceDate = new Date(r.race_time);
      return raceDate.toISOString().split('T')[0] === targetDate.toISOString().split('T')[0];
    });
    
    // If no races for selected date, get today's races
    if (filteredRaces.length === 0) {
      const today = new Date().toISOString().split('T')[0];
      const todayRaces = (data.races || []).filter(r => {
        const raceDate = new Date(r.race_time);
        return raceDate.toISOString().split('T')[0] === today;
      });
      
      if (todayRaces.length > 0) {
        setRaces(todayRaces);
        setDate(today);
        if (!selectedRace) {
          selectRace(todayRaces[0]);
        }
      } else {
        // Get first few races
        setRaces(data.races?.slice(0, 10) || []);
        if (data.races?.length > 0 && !selectedRace) {
          selectRace(data.races[0]);
        }
      }
    } else {
      setRaces(filteredRaces);
      if (filteredRaces.length > 0 && !selectedRace) {
        selectRace(filteredRaces[0]);
      }
    }
    
    setIsDemoMode(true);
  };

  const selectRace = async (race) => {
    setSelectedRace(race);
    
    // Try API first
    try {
      const response = await predictionsApi.getByRaceId(race.id);
      if (response.data && response.data.predictions) {
        setPredictions(response.data.predictions);
        return;
      }
    } catch (e) {
      console.log("API prediction failed, using demo");
    }
    
    // Use demo predictions
    loadDemoPredictions(race);
  };

  const loadDemoPredictions = (race) => {
    // Generate predictions from stored data
    const stored = localStorage.getItem('ausrace_demo_data');
    if (stored) {
      try {
        const data = JSON.parse(stored);
        const participants = (data.participants || [])
          .filter(p => p.race_id === race.id)
          .sort((a, b) => parseFloat(b.win_probability) - parseFloat(a.win_probability));
        
        if (participants.length > 0) {
          setPredictions(participants.map(p => ({
            participant_id: p.id,
            horse_name: p.horse?.name || "Unknown",
            jockey_name: p.jockey?.name || "Unknown",
            trainer_name: p.trainer?.name || "Unknown",
            barrier: p.barrier,
            weight: p.carried_weight,
            form: p.form_string,
            win_probability: parseFloat(p.win_probability),
            place_probability: parseFloat(p.fixed_place),
            predicted_position: 1,
            confidence_score: parseFloat(p.win_probability),
            factors: {
              positive: [
                parseFloat(p.win_probability) > 20 ? "High probability" : null,
                p.form_string?.startsWith("1") ? "Won last start" : null
              ].filter(Boolean),
              negative: []
            }
          })));
          return;
        }
      } catch (e) {
        console.error("Error loading demo predictions:", e);
      }
    }
    
    // Generate new predictions
    const bestBets = generateBestBets();
    const raceBets = bestBets.filter(b => b.race_id === race.id);
    
    if (raceBets.length > 0) {
      setPredictions(raceBets.map((bet, idx) => ({
        participant_id: idx + 1,
        horse_name: bet.horse_name,
        jockey_name: bet.jockey_name,
        trainer_name: "Various",
        barrier: idx + 1,
        weight: 55 + idx,
        form: `${idx + 1}-${idx + 2}-${idx + 3}-4-5`,
        win_probability: bet.win_probability,
        place_probability: bet.win_probability / 2.5,
        predicted_position: idx + 1,
        confidence_score: bet.confidence_score,
        factors: bet.factors
      })));
    } else {
      setPredictions([]);
    }
  };

  const handleGeneratePredictions = async () => {
    if (!selectedRace) return;
    
    try {
      setLoading(true);
      const response = await predictionsApi.generate(selectedRace.id);
      if (response.data && response.data.predictions) {
        setPredictions(response.data.predictions);
      }
    } catch (error) {
      console.error("Error generating predictions:", error);
      // Use demo predictions
      loadDemoPredictions(selectedRace);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateStr) => {
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-AU', { 
      weekday: 'long',
      year: 'numeric', 
      month: 'long', 
      day: 'numeric' 
    });
  };

  return (
    <div className="space-y-6 pt-14 lg:pt-0 animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-white">Race Cards</h1>
          <p className="text-secondary-400 text-sm">View races and AI predictions</p>
        </div>
        
        <div className="flex flex-wrap items-center gap-3">
          {/* Date Picker */}
          <div className="flex items-center gap-2">
            <Calendar className="w-4 h-4 sm:w-5 sm:h-5 text-secondary-400" />
            <input
              type="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
              className="bg-secondary-800 border border-secondary-700 rounded-lg px-2 py-1.5 sm:px-3 sm:py-2 text-white text-sm focus:outline-none focus:border-primary-500"
            />
          </div>

          <button
            onClick={fetchRaces}
            className="flex items-center gap-2 px-3 py-1.5 sm:px-4 sm:py-2 bg-secondary-800 hover:bg-secondary-700 rounded-lg border border-secondary-700 transition-colors text-sm"
          >
            <RefreshCw className="w-4 h-4" />
            <span className="hidden sm:inline">Refresh</span>
          </button>
        </div>
      </div>

      {/* Demo Mode Banner */}
      {isDemoMode && (
        <div className="bg-primary-500/10 border border-primary-500/30 rounded-lg p-3 flex items-center gap-2">
          <span className="text-sm text-primary-400">Demo mode - showing generated sample data</span>
        </div>
      )}

      {/* Date Display */}
      <div className="text-base sm:text-lg font-medium text-white">
        {formatDate(date)}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 lg:gap-6">
        {/* Race List */}
        <div className="lg:col-span-1 space-y-3">
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div>
            </div>
          ) : races.length === 0 ? (
            <div className="text-center py-8 bg-secondary-800 rounded-xl border border-secondary-700">
              <p className="text-secondary-400">No races found for this date.</p>
            </div>
          ) : (
            races.map((race) => (
              <RaceCard
                key={race.id}
                race={race}
                selected={selectedRace?.id === race.id}
                onSelect={selectRace}
              />
            ))
          )}
        </div>

        {/* Race Details & Predictions */}
        <div className="lg:col-span-2 space-y-4">
          {selectedRace ? (
            <>
              {/* Race Info */}
              <div className="bg-secondary-800 rounded-xl p-6 border border-secondary-700">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h2 className="text-xl font-bold text-white">
                      {selectedRace.race_name || `Race ${selectedRace.race_number}`}
                    </h2>
                    <p className="text-secondary-400">
                      {selectedRace.distance}m | {selectedRace.race_class || 'Open'}
                    </p>
                  </div>
                  <button
                    onClick={handleGeneratePredictions}
                    className="px-3 py-1.5 sm:px-4 sm:py-2 bg-primary-500 hover:bg-primary-600 rounded-lg transition-colors text-sm"
                  >
                    Generate
                  </button>
                </div>

                {/* Weather Widget */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <WeatherWidget
                    weather={selectedRace.meeting?.weather}
                    trackRating={selectedRace.meeting?.track_rating}
                    venue={selectedRace.meeting?.venue?.name}
                  />
                  
                  {/* Race Info */}
                  <div className="bg-secondary-700/50 rounded-lg p-4">
                    <h4 className="text-sm font-medium text-secondary-400 mb-2">Race Information</h4>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-secondary-400">Distance:</span>
                        <span className="text-white">{selectedRace.distance}m</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-secondary-400">Class:</span>
                        <span className="text-white">{selectedRace.race_class || 'Open'}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-secondary-400">Prize Money:</span>
                        <span className="text-white">
                          ${selectedRace.prize_money?.toLocaleString() || 'N/A'}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-secondary-400">Race Type:</span>
                        <span className="text-white">{selectedRace.race_type || 'Gallops'}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Predictions Table */}
              <PredictionTable 
                predictions={predictions}
                onGenerate={handleGeneratePredictions}
              />
            </>
          ) : (
            <div className="text-center py-12 bg-secondary-800 rounded-xl border border-secondary-700">
              <p className="text-secondary-400">Select a race to view predictions</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Races;
