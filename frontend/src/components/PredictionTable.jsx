import React, { useState } from 'react';
import { ChevronDown, ChevronUp, Info } from 'lucide-react';

const PredictionTable = ({ predictions, onGenerate }) => {
  const [sortBy, setSortBy] = useState('win_probability');
  const [sortOrder, setSortOrder] = useState('desc');
  const [expandedHorse, setExpandedHorse] = useState(null);

  const handleSort = (field) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortOrder('desc');
    }
  };

  const sortedPredictions = [...predictions].sort((a, b) => {
    const aVal = a[sortBy] || 0;
    const bVal = b[sortBy] || 0;
    return sortOrder === 'asc' ? aVal - bVal : bVal - aVal;
  });

  const getPositionColor = (position) => {
    if (position === 1) return 'bg-yellow-500';
    if (position === 2) return 'bg-gray-400';
    if (position === 3) return 'bg-orange-600';
    return 'bg-secondary-600';
  };

  const SortIcon = ({ field }) => {
    if (sortBy !== field) return null;
    return sortOrder === 'asc' ? 
      <ChevronUp className="w-4 h-4 inline ml-1" /> : 
      <ChevronDown className="w-4 h-4 inline ml-1" />;
  };

  if (!predictions || predictions.length === 0) {
    return (
      <div className="text-center py-12 bg-secondary-800 rounded-xl border border-secondary-700">
        <p className="text-secondary-400 mb-4">No predictions available for this race.</p>
        {onGenerate && (
          <button
            onClick={onGenerate}
            className="px-4 py-2 bg-primary-500 hover:bg-primary-600 rounded-lg transition-colors"
          >
            Generate Predictions
          </button>
        )}
      </div>
    );
  }

  return (
    <div className="bg-secondary-800 rounded-xl border border-secondary-700 overflow-hidden">
      {/* Table Header */}
      <div className="grid grid-cols-12 gap-2 p-4 bg-secondary-700/50 text-sm font-medium text-secondary-400">
        <div 
          className="col-span-1 cursor-pointer hover:text-white"
          onClick={() => handleSort('predicted_position')}
        >
          Pos <SortIcon field="predicted_position" />
        </div>
        <div className="col-span-3">Horse</div>
        <div className="col-span-2">Jockey</div>
        <div className="col-span-1">Bar.</div>
        <div className="col-span-1">Wt</div>
        <div className="col-span-1">Form</div>
        <div 
          className="col-span-2 cursor-pointer hover:text-white text-right"
          onClick={() => handleSort('win_probability')}
        >
          Win% <SortIcon field="win_probability" />
        </div>
        <div className="col-span-1 text-right">Conf.</div>
      </div>

      {/* Table Body */}
      <div className="divide-y divide-secondary-700">
        {sortedPredictions.map((pred, index) => (
          <div key={pred.participant_id || index}>
            <div 
              className={`grid grid-cols-12 gap-2 p-4 items-center hover:bg-secondary-700/30 transition-colors ${
                pred.predicted_position === 1 ? 'bg-primary-500/10' : ''
              }`}
            >
              {/* Position */}
              <div className="col-span-1">
                <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold text-white ${getPositionColor(pred.predicted_position)}`}>
                  {pred.predicted_position || index + 1}
                </span>
              </div>

              {/* Horse Name */}
              <div className="col-span-3">
                <p className="font-semibold text-white">{pred.horse_name}</p>
                <p className="text-xs text-secondary-500">{pred.trainer_name}</p>
              </div>

              {/* Jockey */}
              <div className="col-span-2 text-sm text-secondary-300">
                {pred.jockey_name || 'N/A'}
              </div>

              {/* Barrier */}
              <div className="col-span-1 text-sm text-secondary-300">
                {pred.barrier || '-'}
              </div>

              {/* Weight */}
              <div className="col-span-1 text-sm text-secondary-300 font-mono">
                {pred.weight ? `${pred.weight}kg` : '-'}
              </div>

              {/* Form */}
              <div className="col-span-1 text-sm font-mono text-secondary-400">
                {pred.form || '-'}
              </div>

              {/* Win Probability */}
              <div className="col-span-2 text-right">
                <div className="flex items-center justify-end gap-2">
                  <div className="w-16 bg-secondary-700 rounded-full h-2 overflow-hidden">
                    <div 
                      className="h-full bg-primary-500 probability-bar"
                      style={{ width: `${pred.win_probability || 0}%` }}
                    />
                  </div>
                  <span className="font-bold text-primary-400 text-sm">
                    {pred.win_probability || 0}%
                  </span>
                </div>
              </div>

              {/* Confidence */}
              <div className="col-span-1 text-right">
                <span className={`text-sm font-medium ${
                  (pred.confidence_score || 0) > 30 ? 'text-green-400' : 
                  (pred.confidence_score || 0) > 15 ? 'text-yellow-400' : 
                  'text-secondary-400'
                }`}>
                  {pred.confidence_score || 0}%
                </span>
              </div>
            </div>

            {/* Expanded Factors */}
            {expandedHorse === pred.participant_id && pred.factors && (
              <div className="col-span-12 p-4 bg-secondary-700/30 border-t border-secondary-700">
                <div className="grid grid-cols-2 gap-4">
                  {/* Positive Factors */}
                  <div>
                    <h4 className="text-sm font-medium text-green-400 mb-2">Positive Factors</h4>
                    {pred.factors.positive && pred.factors.positive.length > 0 ? (
                      <ul className="space-y-1">
                        {pred.factors.positive.map((factor, i) => (
                          <li key={i} className="text-sm text-secondary-300 flex items-center gap-2">
                            <span className="w-1.5 h-1.5 bg-green-500 rounded-full"></span>
                            {factor}
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p className="text-sm text-secondary-500">No specific positive factors</p>
                    )}
                  </div>

                  {/* Negative Factors */}
                  <div>
                    <h4 className="text-sm font-medium text-red-400 mb-2">Negative Factors</h4>
                    {pred.factors.negative && pred.factors.negative.length > 0 ? (
                      <ul className="space-y-1">
                        {pred.factors.negative.map((factor, i) => (
                          <li key={i} className="text-sm text-secondary-300 flex items-center gap-2">
                            <span className="w-1.5 h-1.5 bg-red-500 rounded-full"></span>
                            {factor}
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p className="text-sm text-secondary-500">No specific negative factors</p>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default PredictionTable;
