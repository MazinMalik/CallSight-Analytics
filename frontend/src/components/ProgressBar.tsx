import React from 'react';
import { CheckCircle2, Loader2, AlertCircle } from 'lucide-react';
import { ProcessingStatus } from '../types';

interface ProgressBarProps {
  status: ProcessingStatus;
  stage?: string | null;
  errorMessage?: string | null;
}

const STAGES: { id: ProcessingStatus; label: string }[] = [
  { id: 'queued', label: '1. Queued' },
  { id: 'converting', label: '2. Converting Audio' },
  { id: 'transcribing', label: '3. IndicConformer Speech-to-Text' },
  { id: 'extracting', label: '4. Qwen 4B Lead Extraction' },
  { id: 'saving', label: '5. Saving Record & CSV' },
  { id: 'completed', label: '6. Completed' },
];

export const ProgressBar: React.FC<ProgressBarProps> = ({ status, stage, errorMessage }) => {
  const getStageIndex = (st: ProcessingStatus) => {
    switch (st) {
      case 'queued': return 0;
      case 'converting': return 1;
      case 'transcribing': return 2;
      case 'extracting': return 3;
      case 'saving': return 4;
      case 'completed': return 5;
      case 'failed': return -1;
      default: return 0;
    }
  };

  const currentIndex = getStageIndex(status);
  const isFailed = status === 'failed';
  const progressPercent = isFailed ? 100 : Math.round(((currentIndex + 1) / STAGES.length) * 100);

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900 p-6 shadow-xl space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h4 className="text-sm font-semibold text-white flex items-center gap-2">
            {!isFailed && status !== 'completed' && <Loader2 className="h-4 w-4 text-sky-400 animate-spin" />}
            {status === 'completed' && <CheckCircle2 className="h-4 w-4 text-emerald-400" />}
            {isFailed && <AlertCircle className="h-4 w-4 text-rose-400" />}
            Job Processing Status: <span className="capitalize text-sky-300">{status}</span>
          </h4>
          <p className="text-xs text-slate-400 mt-1">{stage || 'Processing in progress...'}</p>
        </div>
        <span className="text-xs font-mono text-slate-400">{progressPercent}%</span>
      </div>

      {/* Bar container */}
      <div className="w-full bg-slate-800 h-2.5 rounded-full overflow-hidden">
        <div 
          className={`h-full transition-all duration-500 rounded-full ${
            isFailed 
              ? 'bg-rose-500' 
              : status === 'completed' 
                ? 'bg-emerald-500' 
                : 'bg-gradient-to-r from-sky-500 via-indigo-500 to-purple-500 animate-pulse'
          }`}
          style={{ width: `${progressPercent}%` }}
        />
      </div>

      {/* Stage indicators */}
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-2 pt-2">
        {STAGES.map((s, idx) => {
          const isDone = currentIndex > idx || status === 'completed';
          const isCurrent = currentIndex === idx && !isFailed;
          return (
            <div 
              key={s.id} 
              className={`p-2 rounded-lg text-center border text-[11px] font-medium transition-all ${
                isDone 
                  ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' 
                  : isCurrent 
                    ? 'bg-sky-500/10 border-sky-500/40 text-sky-300 ring-1 ring-sky-500/50' 
                    : 'bg-slate-800/40 border-slate-800 text-slate-500'
              }`}
            >
              {s.label}
            </div>
          );
        })}
      </div>

      {isFailed && errorMessage && (
        <div className="p-3 bg-rose-500/10 border border-rose-500/30 rounded-lg text-xs text-rose-300">
          <strong>Error Details:</strong> {errorMessage}
        </div>
      )}
    </div>
  );
};
