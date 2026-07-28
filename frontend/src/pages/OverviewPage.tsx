import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { 
  PhoneCall, 
  Calendar, 
  ThumbsUp, 
  ShoppingCart, 
  PhoneOff, 
  Clock, 
  CheckCircle,
  ArrowRight
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { fetchStats } from '../api/client';
import { StatCard } from '../components/StatCard';
import { StatusBadge } from '../components/StatusBadge';

export const OverviewPage: React.FC = () => {
  const { data: stats, isLoading, error, refetch } = useQuery({
    queryKey: ['stats'],
    queryFn: fetchStats,
    refetchInterval: 15000,
  });

  if (isLoading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-8 w-48 bg-slate-800 rounded" />
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-28 bg-slate-900 border border-slate-800 rounded-xl" />
          ))}
        </div>
      </div>
    );
  }

  if (error || !stats) {
    return (
      <div className="p-6 bg-rose-500/10 border border-rose-500/30 rounded-xl text-rose-300">
        <p className="font-semibold">Failed to load overview dashboard stats.</p>
        <button onClick={() => refetch()} className="mt-2 text-xs bg-rose-500/20 px-3 py-1 rounded">
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white tracking-tight">Executive Dashboard</h2>
          <p className="text-sm text-slate-400">Real-time overview of telecaller recordings, AI transcription, and lead extraction.</p>
        </div>
        <Link 
          to="/upload" 
          className="inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-sky-500 hover:bg-sky-400 text-white font-medium text-sm transition-all shadow-lg shadow-sky-500/25"
        >
          <PhoneCall className="h-4 w-4" />
          Upload New Recording
        </Link>
      </div>

      {/* Primary KPI Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard 
          title="Total Calls Processed" 
          value={stats.total_calls} 
          subtitle="Lifetime recordings uploaded"
          icon={PhoneCall}
          iconColor="text-sky-400"
          accentColor="from-sky-500/10 to-transparent"
        />
        <StatCard 
          title="Calls Processed Today" 
          value={stats.calls_today} 
          subtitle="Processed in last 24h"
          icon={Calendar}
          iconColor="text-indigo-400"
          accentColor="from-indigo-500/10 to-transparent"
        />
        <StatCard 
          title="Interested Leads" 
          value={stats.interested_leads} 
          subtitle="High intent prospects"
          icon={ThumbsUp}
          iconColor="text-emerald-400"
          accentColor="from-emerald-500/10 to-transparent"
        />
        <StatCard 
          title="Confirmed Orders" 
          value={stats.orders_confirmed} 
          subtitle="Deals closed via call"
          icon={ShoppingCart}
          iconColor="text-blue-400"
          accentColor="from-blue-500/10 to-transparent"
        />
      </div>

      {/* Secondary KPI Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatCard 
          title="Follow-ups Required" 
          value={stats.follow_ups_required} 
          subtitle="Action needed"
          icon={Clock}
          iconColor="text-amber-400"
          accentColor="from-amber-500/10 to-transparent"
        />
        <StatCard 
          title="Did Not Pick / Missed" 
          value={stats.did_not_pick} 
          subtitle="Unanswered calls"
          icon={PhoneOff}
          iconColor="text-slate-400"
          accentColor="from-slate-500/10 to-transparent"
        />
        <StatCard 
          title="AI Processing Success Rate" 
          value={`${stats.success_rate}%`} 
          subtitle={`${stats.processing_failures} failures recorded`}
          icon={CheckCircle}
          iconColor="text-emerald-400"
          accentColor="from-emerald-500/10 to-transparent"
        />
      </div>

      {/* Visual Distribution Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Status Distribution */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/80 p-6 space-y-4">
          <h3 className="text-base font-semibold text-white">Call Status Breakdown</h3>
          <div className="space-y-3">
            {Object.entries(stats.status_distribution).map(([statusKey, count]) => {
              const pct = stats.total_calls > 0 ? Math.round((count / stats.total_calls) * 100) : 0;
              return (
                <div key={statusKey} className="space-y-1">
                  <div className="flex items-center justify-between text-xs font-medium">
                    <StatusBadge status={statusKey} />
                    <span className="text-slate-400 font-mono">{count} calls ({pct}%)</span>
                  </div>
                  <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                    <div className="bg-sky-500 h-full rounded-full transition-all duration-300" style={{ width: `${pct}%` }} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Telecaller Performance */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/80 p-6 space-y-4">
          <h3 className="text-base font-semibold text-white">Calls by Telecaller</h3>
          {Object.keys(stats.calls_per_telecaller).length === 0 ? (
            <p className="text-sm text-slate-500 italic py-4">No telecaller data logged yet.</p>
          ) : (
            <div className="space-y-3">
              {Object.entries(stats.calls_per_telecaller).map(([name, count]) => {
                const pct = stats.total_calls > 0 ? Math.round((count / stats.total_calls) * 100) : 0;
                return (
                  <div key={name} className="space-y-1">
                    <div className="flex items-center justify-between text-xs font-medium">
                      <span className="text-slate-200">{name}</span>
                      <span className="text-slate-400 font-mono">{count} calls</span>
                    </div>
                    <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                      <div className="bg-indigo-500 h-full rounded-full transition-all duration-300" style={{ width: `${pct}%` }} />
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Recent Uploads Table Widget */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/80 p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-base font-semibold text-white">Recent Call Recordings</h3>
          <Link to="/calls" className="text-xs text-sky-400 hover:text-sky-300 flex items-center gap-1 font-medium">
            View All Calls <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </div>

        {stats.recent_calls.length === 0 ? (
          <div className="py-8 text-center text-slate-500 text-sm">
            No call recordings present. Click "Upload New Recording" to begin processing.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="border-b border-slate-800 text-slate-400 uppercase tracking-wider bg-slate-950/40">
                <tr>
                  <th className="py-3 px-4">Telecaller</th>
                  <th className="py-3 px-4">Company</th>
                  <th className="py-3 px-4">Phone</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Processing State</th>
                  <th className="py-3 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {stats.recent_calls.map((call) => (
                  <tr key={call.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="py-3 px-4 font-medium text-white">{call.telecaller_name}</td>
                    <td className="py-3 px-4">{call.company_name}</td>
                    <td className="py-3 px-4 font-mono text-slate-400">{call.submitted_phone_number}</td>
                    <td className="py-3 px-4">
                      <StatusBadge status={call.call_status} />
                    </td>
                    <td className="py-3 px-4">
                      <StatusBadge status={call.processing_status} type="processing" />
                    </td>
                    <td className="py-3 px-4 text-right">
                      <Link to={`/calls/${call.id}`} className="text-sky-400 hover:text-sky-300 font-medium">
                        View Details
                      </Link>
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
