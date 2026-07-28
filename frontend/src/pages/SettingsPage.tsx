import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Settings, Server, Cpu, Database, ShieldCheck, RefreshCw } from 'lucide-react';
import { fetchHealth } from '../api/client';

export const SettingsPage: React.FC = () => {
  const { data: health, isLoading, refetch } = useQuery({
    queryKey: ['health'],
    queryFn: fetchHealth,
  });

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div>
        <h2 className="text-2xl font-bold text-white tracking-tight">System Settings & Health Status</h2>
        <p className="text-sm text-slate-400">View backend environment settings, Ollama Qwen 4B configuration, and IndicConformer status.</p>
      </div>

      {/* Health Card */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/80 p-6 md:p-8 space-y-6 shadow-xl">
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <div className="flex items-center gap-3">
            <div className="p-3 rounded-xl bg-sky-500/10 text-sky-400 border border-sky-500/20">
              <Server className="h-6 w-6" />
            </div>
            <div>
              <h3 className="text-base font-semibold text-white">Backend Health Diagnostics</h3>
              <p className="text-xs text-slate-400">Live API server and local LLM connectivity status.</p>
            </div>
          </div>
          <button
            onClick={() => refetch()}
            className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs flex items-center gap-1.5"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${isLoading ? 'animate-spin' : ''}`} /> Refresh
          </button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
          <div className="p-4 bg-slate-950 rounded-lg border border-slate-800 space-y-1">
            <span className="text-slate-400 block font-medium">API Environment:</span>
            <p className="text-sm font-mono text-sky-400 font-semibold uppercase">{health?.app_env || 'development'}</p>
          </div>

          <div className="p-4 bg-slate-950 rounded-lg border border-slate-800 space-y-1">
            <span className="text-slate-400 block font-medium">Ollama Qwen Status:</span>
            <p className="text-sm font-mono flex items-center gap-2 font-semibold">
              <span className={`w-2 h-2 rounded-full ${health?.ollama_connected ? 'bg-emerald-400' : 'bg-amber-400 animate-pulse'}`} />
              {health?.ollama_connected ? 'Connected (Live LLM)' : 'Offline / Mock Dev Mode'}
            </p>
          </div>

          <div className="p-4 bg-slate-950 rounded-lg border border-slate-800 space-y-1">
            <span className="text-slate-400 block font-medium">Target LLM Model:</span>
            <p className="text-sm font-mono text-indigo-300">{health?.ollama_model || 'qwen3:4b'}</p>
          </div>

          <div className="p-4 bg-slate-950 rounded-lg border border-slate-800 space-y-1">
            <span className="text-slate-400 block font-medium">Speech-to-Text Engine:</span>
            <p className="text-sm font-mono text-purple-300">{health?.transcription_engine || 'indic_conformer'}</p>
          </div>
        </div>
      </div>

      {/* Architecture overview card */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/80 p-6 md:p-8 space-y-4 shadow-xl">
        <h3 className="text-base font-semibold text-white flex items-center gap-2">
          <ShieldCheck className="h-5 w-5 text-emerald-400" /> Deployment & Architecture Specifications
        </h3>

        <div className="space-y-3 text-xs text-slate-300">
          <p>
            <strong>Frontend Host:</strong> Configured for separate serverless static deployment on <strong>Vercel</strong>.
          </p>
          <p>
            <strong>Backend VM:</strong> Configured for deployment on <strong>Oracle Cloud Free Tier Ubuntu (ARM64/x86)</strong>.
          </p>
          <p>
            <strong>Security:</strong> The frontend never communicates directly with Ollama. All audio transcription and LLM prompt generation are processed securely behind the FastAPI backend.
          </p>
        </div>
      </div>
    </div>
  );
};
