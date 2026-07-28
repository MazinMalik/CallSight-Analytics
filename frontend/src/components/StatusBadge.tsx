import React from 'react';
import { CallStatus, ProcessingStatus } from '../types';

interface StatusBadgeProps {
  status: CallStatus | ProcessingStatus | string;
  type?: 'call' | 'processing';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, type = 'call' }) => {
  if (type === 'processing') {
    const procStyles: Record<string, { label: string; style: string }> = {
      queued: { label: 'Queued', style: 'bg-amber-500/10 text-amber-400 border-amber-500/20' },
      converting: { label: 'Converting', style: 'bg-blue-500/10 text-blue-400 border-blue-500/20' },
      transcribing: { label: 'Transcribing', style: 'bg-purple-500/10 text-purple-400 border-purple-500/20' },
      extracting: { label: 'Extracting', style: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20' },
      saving: { label: 'Saving', style: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20' },
      completed: { label: 'Completed', style: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' },
      failed: { label: 'Failed', style: 'bg-rose-500/10 text-rose-400 border-rose-500/20' },
    };

    const cfg = procStyles[status] || { label: status, style: 'bg-slate-500/10 text-slate-400 border-slate-500/20' };

    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${cfg.style}`}>
        <span className="w-1.5 h-1.5 rounded-full bg-current mr-1.5 animate-pulse" />
        {cfg.label}
      </span>
    );
  }

  const callStyles: Record<string, { label: string; style: string }> = {
    interested: { label: 'Interested', style: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30' },
    ordered: { label: 'Ordered', style: 'bg-blue-500/10 text-blue-400 border-blue-500/30' },
    not_interested: { label: 'Not Interested', style: 'bg-rose-500/10 text-rose-400 border-rose-500/30' },
    did_not_pick: { label: 'Did Not Pick', style: 'bg-slate-500/10 text-slate-400 border-slate-500/30' },
    callback_requested: { label: 'Callback Requested', style: 'bg-amber-500/10 text-amber-400 border-amber-500/30' },
    follow_up_required: { label: 'Follow-up Required', style: 'bg-purple-500/10 text-purple-400 border-purple-500/30' },
    wrong_number: { label: 'Wrong Number', style: 'bg-orange-500/10 text-orange-400 border-orange-500/30' },
    unavailable: { label: 'Unavailable', style: 'bg-zinc-500/10 text-zinc-400 border-zinc-500/30' },
    unclear: { label: 'Unclear', style: 'bg-gray-500/10 text-gray-400 border-gray-500/30' },
  };

  const cfg = callStyles[status] || { label: status, style: 'bg-slate-500/10 text-slate-400 border-slate-500/30' };

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border ${cfg.style}`}>
      {cfg.label}
    </span>
  );
};
