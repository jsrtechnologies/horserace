import React from 'react';
import { NavLink } from 'react-router-dom';
import { 
  LayoutDashboard, 
  Flag, 
  TrendingUp, 
  Settings,
  Trophy
} from 'lucide-react';

const Sidebar = () => {
  const navItems = [
    { path: '/', icon: LayoutDashboard, label: 'Dashboard' },
    { path: '/races', icon: Flag, label: 'Races' },
    { path: '/predictions', icon: TrendingUp, label: 'Predictions' },
    { path: '/settings', icon: Settings, label: 'Settings' },
  ];

  return (
    <aside className="fixed left-0 top-0 h-screen w-64 bg-secondary-800 border-r border-secondary-700 flex flex-col">
      {/* Logo */}
      <div className="p-6 border-b border-secondary-700">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-primary-500 rounded-lg flex items-center justify-center">
            <Trophy className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-white">AusRace</h1>
            <p className="text-xs text-secondary-400">AI Predictor</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4">
        <ul className="space-y-2">
          {navItems.map((item) => (
            <li key={item.path}>
              <NavLink
                to={item.path}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                    isActive
                      ? 'bg-primary-500/20 text-primary-400'
                      : 'text-secondary-300 hover:bg-secondary-700 hover:text-white'
                  }`
                }
              >
                <item.icon className="w-5 h-5" />
                <span className="font-medium">{item.label}</span>
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-secondary-700">
        <div className="text-xs text-secondary-500 text-center">
          <p>AusRace Predictor AI v1.0</p>
          <p>Australian Horse Racing ML</p>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
