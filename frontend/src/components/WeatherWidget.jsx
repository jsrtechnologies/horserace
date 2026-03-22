import React from 'react';
import { Cloud, Wind, Droplets, Thermometer, Sun } from 'lucide-react';

const WeatherWidget = ({ weather, trackRating, venue }) => {
  const getTrackRatingColor = (rating) => {
    if (!rating) return 'bg-secondary-600';
    const lower = rating.toLowerCase();
    if (lower.includes('heavy')) return 'bg-red-600';
    if (lower.includes('soft')) return 'bg-yellow-600';
    if (lower.includes('good')) return 'bg-green-600';
    return 'bg-secondary-600';
  };

  const getTrackCondition = (rating) => {
    if (!rating) return 'Unknown';
    const lower = rating.toLowerCase();
    if (lower.includes('heavy')) return 'Heavy Track';
    if (lower.includes('soft')) return 'Soft Track';
    if (lower.includes('good')) return 'Good Track';
    return 'Track Condition';
  };

  const getWeatherIcon = (weather) => {
    if (!weather) return <Cloud className="w-8 h-8" />;
    const lower = weather.toLowerCase();
    if (lower.includes('rain')) return <Droplets className="w-8 h-8 text-blue-400" />;
    if (lower.includes('cloud') || lower.includes('overcast')) return <Cloud className="w-8 h-8 text-gray-400" />;
    if (lower.includes('sun') || lower.includes('fine') || lower.includes('clear')) return <Sun className="w-8 h-8 text-yellow-400" />;
    return <Cloud className="w-8 h-8" />;
  };

  return (
    <div className="bg-secondary-800 rounded-xl border border-secondary-700 p-4">
      <h3 className="text-sm font-medium text-secondary-400 mb-4">Track Conditions</h3>
      
      <div className="space-y-4">
        {/* Venue */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-secondary-700 rounded-lg flex items-center justify-center">
            <span className="text-lg">🏇</span>
          </div>
          <div>
            <p className="text-sm text-secondary-400">Venue</p>
            <p className="font-semibold text-white">{venue || 'Unknown'}</p>
          </div>
        </div>

        {/* Weather */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-secondary-700 rounded-lg flex items-center justify-center">
            {getWeatherIcon(weather)}
          </div>
          <div>
            <p className="text-sm text-secondary-400">Weather</p>
            <p className="font-semibold text-white">{weather || 'Loading...'}</p>
          </div>
        </div>

        {/* Track Rating */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-secondary-700 rounded-lg flex items-center justify-center">
            <Thermometer className="w-5 h-5 text-primary-400" />
          </div>
          <div>
            <p className="text-sm text-secondary-400">Track</p>
            <span className={`px-2 py-1 rounded text-xs text-white ${getTrackRatingColor(trackRating)}`}>
              {trackRating || 'Loading...'}
            </span>
          </div>
        </div>
      </div>

      {/* Track Condition Legend */}
      <div className="mt-4 pt-4 border-t border-secondary-700">
        <p className="text-xs text-secondary-500 mb-2">Track Condition Guide</p>
        <div className="grid grid-cols-3 gap-2 text-xs">
          <div className="flex items-center gap-1">
            <span className="w-2 h-2 bg-green-500 rounded-full"></span>
            <span className="text-secondary-400">Good</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="w-2 h-2 bg-yellow-500 rounded-full"></span>
            <span className="text-secondary-400">Soft</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="w-2 h-2 bg-red-500 rounded-full"></span>
            <span className="text-secondary-400">Heavy</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default WeatherWidget;
