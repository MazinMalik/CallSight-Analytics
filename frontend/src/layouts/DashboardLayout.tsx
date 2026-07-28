import React, { useState, useEffect } from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import { 
  LayoutDashboard, 
  Upload, 
  PhoneCall, 
  FileSpreadsheet, 
  Settings, 
  Activity, 
  Sparkles,
  Menu,
  X
} from 'lucide-react';
import { fetchHealth } from '../api/client';

export const DashboardLayout: React.FC = () => {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [healthStatus, setHealthStatus] = useState<{ connected: boolean; model: string } | null>(null);

  useEffect(() => {
    const checkApi = async () => {
      try {
        const res = await fetchHealth();
        setHealthStatus({ connected: res.ollama_connected, model: res.ollama_model });
      } catch {
        setHealthStatus({ connected: false, model: 'qwen3:4b' });
      }
    };
    checkApi();
    const interval = setInterval(checkApi, 30000);
    return () => clearInterval(interval);
  }, []);

  const navItems = [
    { to: '/', label: 'Overview', icon: LayoutDashboard },
    { to: '/upload', label: 'Upload Call', icon: Upload },
    { to: '/calls', label: 'All Calls', icon: PhoneCall },
    { to: '/export', label: 'CSV Exports', icon: FileSpreadsheet },
    { to: '/settings', label: 'Settings', icon: Settings },
  ];

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col md:flex-row">
      {/* Sidebar Desktop */}
      <aside className="hidden md:flex flex-col w-64 border-r border-slate-800 bg-slate-900/90 p-4 shrink-0">
        <div className="flex items-center gap-3 px-3 py-3 border-b border-slate-800">
          <div className="p-2 rounded-xl bg-gradient-to-tr from-sky-500 to-indigo-600 text-white shadow-lg shadow-sky-500/20">
            <Sparkles className="h-5 w-5" />
          </div>
          <div>
            <h1 className="font-bold text-sm text-white tracking-wide">AI Telecaller</h1>
            <p className="text-[11px] text-slate-400">IndicConformer + Qwen 4B</p>
          </div>
        </div>

        <nav className="mt-6 flex-1 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                    isActive
                      ? 'bg-sky-500/10 text-sky-400 border border-sky-500/20 font-semibold'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                  }`
                }
              >
                <Icon className="h-4 w-4" />
                {item.label}
              </NavLink>
            );
          })}
        </nav>

        {/* Status Pill */}
        <div className="mt-auto p-3 rounded-lg border border-slate-800 bg-slate-950/60 space-y-2">
          <div className="flex items-center justify-between text-xs">
            <span className="text-slate-400 flex items-center gap-1.5">
              <Activity className="h-3.5 w-3.5 text-sky-400" />
              Ollama Qwen:
            </span>
            <span className={`px-2 py-0.5 rounded text-[10px] font-mono ${
              healthStatus?.connected 
                ? 'bg-emerald-500/20 text-emerald-400' 
                : 'bg-amber-500/20 text-amber-400'
            }`}>
              {healthStatus?.connected ? 'Online' : 'Mock Dev'}
            </span>
          </div>
          <p className="text-[10px] font-mono text-slate-500 truncate">
            Model: {healthStatus?.model || 'qwen3:4b'}
          </p>
        </div>
      </aside>

      {/* Mobile Header */}
      <header className="md:hidden flex items-center justify-between p-4 border-b border-slate-800 bg-slate-900">
        <div className="flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-sky-400" />
          <span className="font-bold text-sm text-white">AI Telecaller</span>
        </div>
        <button 
          onClick={() => setMobileOpen(!mobileOpen)}
          className="p-2 text-slate-400 hover:text-white"
        >
          {mobileOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
        </button>
      </header>

      {/* Mobile Nav */}
      {mobileOpen && (
        <div className="md:hidden bg-slate-900 border-b border-slate-800 p-4 space-y-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                onClick={() => setMobileOpen(false)}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium ${
                    isActive ? 'bg-sky-500/10 text-sky-400 font-semibold' : 'text-slate-400'
                  }`
                }
              >
                <Icon className="h-4 w-4" />
                {item.label}
              </NavLink>
            );
          })}
        </div>
      )}

      {/* Main Content */}
      <main className="flex-1 p-4 md:p-8 overflow-y-auto max-w-7xl mx-auto w-full">
        <Outlet />
      </main>
    </div>
  );
};
