import React from 'react';
import { Cloud, Wind, Droplets, MapPin, Clock } from 'lucide-react';

const RaceCard = ({ race, onSelect, selected }) => {
  const formatTime = (timeStr) => {
    if (!timeStr) return '';
    const date = new Date(timeStr);
    return date.toLocaleTimeString('en-AU', { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  const getTrackRatingColor = (rating) => {
    if (!rating) return 'bg-secondary-600';
    const lower = rating.toLowerCase();
    if (lower.includes('heavy')) return 'bg-red-600';
    if (lower.includes('soft')) return 'bg-yellow-600';
    if (lower.includes('good')) return 'bg-green-600';
    return 'bg-secondary-600';
  };

  const getWeatherIcon = (weather) => {
    if (!weather) return <Cloud className="w-5 h-5" />;
    const lower = weather.toLowerCase();
    if (lower.includes('rain')) return <Droplets className="w-5 h-5 text-blue-400" />;
    if (lower.includes('cloud') || lower.includes('overcast')) return <Cloud className="w-5 h-5 text-gray-400" />;
    return <Cloud className="w-5 h-5 text-yellow-400" />;
  };

  return (
    <div
      onClick={() => onSelect(race)}
      className={`p-4 rounded-xl border cursor-pointer transition-all ${
        selected
          ? 'bg-primary-500/20 border-primary-500'
          : 'bg-secondary-800 border-secondary-700 hover:border-secondary-600'
      }`}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div>
          <h3 className="font-semibold text-white">
            {race.race_name || `Race ${race.race_number}`}
          </h3>
          <div className="flex items-center gap-2 text-sm text-secondary-400 mt-1">
            <MapPin className="w-4 h-4" />
            {race.venue}
          </div>
        </div>
        <div className="text-right">
          <div className="flex items-center gap-1 text-primary-400 font-mono">
            <Clock className="w-4 h-4" />
            {formatTime(race.race_time)}
          </div>
          <p className="text-sm text-secondary-400 mt-1">{race.distance}m</p>
        </div>
      </div>

      {/* Track Info */}
      <div className="flex items-center gap-3">
        <span className={`px-2 py-1 rounded text-xs text-white ${getTrackRatingColor(race.track_rating)}`}>
          {race.track_rating || 'Track: N/A'}
        </span>
        <div className="flex items-center gap-1 text-secondary-400 text-sm">
          {getWeatherIcon(race.weather)}
          {race.weather || 'Weather: N/A'}
        </div>
      </div>
    </div>
  );
};

export default RaceCard;
