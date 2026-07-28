import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  ArrowLeft, 
  RotateCw, 
  Mic, 
  Save, 
  Trash2, 
  FileText, 
  CheckCircle, 
  User, 
  Building, 
  Phone, 
  Calendar, 
  Sparkles,
  MessageSquare
} from 'lucide-react';
import { fetchCallDetail, updateCallRecord, deleteCallRecord, reprocessCallExtraction, retranscribeCallAudio } from '../api/client';
import { StatusBadge } from '../components/StatusBadge';
import { CallStatus } from '../types';

export const CallDetailsPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [isEditing, setIsEditing] = useState(false);
  const [editForm, setEditForm] = useState<any>({});
  const [actionMsg, setActionMsg] = useState<string | null>(null);

  const { data: call, isLoading, isError } = useQuery({
    queryKey: ['call', id],
    queryFn: () => fetchCallDetail(id!),
    enabled: !!id,
  });

  const updateMutation = useMutation({
    mutationFn: (payload: any) => updateCallRecord(id!, payload),
    onSuccess: (updated) => {
      queryClient.setQueryData(['call', id], updated);
      queryClient.invalidateQueries({ queryKey: ['calls'] });
      queryClient.invalidateQueries({ queryKey: ['stats'] });
      setIsEditing(false);
      setActionMsg('Call details saved successfully.');
      setTimeout(() => setActionMsg(null), 4000);
    },
  });

  const reprocessMutation = useMutation({
    mutationFn: () => reprocessCallExtraction(id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['call', id] });
      queryClient.invalidateQueries({ queryKey: ['calls'] });
      queryClient.invalidateQueries({ queryKey: ['stats'] });
      setActionMsg('Rerunning Qwen lead extraction in background...');
      setTimeout(() => setActionMsg(null), 4000);
    },
  });

  const retranscribeMutation = useMutation({
    mutationFn: () => retranscribeCallAudio(id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['call', id] });
      queryClient.invalidateQueries({ queryKey: ['calls'] });
      queryClient.invalidateQueries({ queryKey: ['stats'] });
      setActionMsg('Re-queued audio for IndicConformer transcription...');
      setTimeout(() => setActionMsg(null), 4000);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: () => deleteCallRecord(id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['calls'] });
      queryClient.invalidateQueries({ queryKey: ['stats'] });
      navigate('/calls');
    },
  });

  if (isLoading) {
    return (
      <div className="p-12 text-center text-slate-400 space-y-2">
        <RotateCw className="h-6 w-6 animate-spin mx-auto text-sky-400" />
        <p className="text-sm">Fetching call details & AI transcript...</p>
      </div>
    );
  }

  if (isError || !call) {
    return (
      <div className="p-8 text-center text-rose-400">
        Call record not found or server error.
      </div>
    );
  }

  const startEdit = () => {
    setEditForm({
      contact_person_name: call.contact_person_name || '',
      phone_number: call.phone_number || call.submitted_phone_number || '',
      email: call.email || '',
      call_status: call.call_status,
      customer_intent: call.customer_intent || '',
      order_details: call.order_details || '',
      quantity: call.quantity || '',
      budget_or_price: call.budget_or_price || '',
      follow_up_date: call.follow_up_date || '',
      follow_up_time: call.follow_up_time || '',
      customer_requirements: call.customer_requirements || '',
      summary: call.summary || '',
      transcript: call.transcript || '',
    });
    setIsEditing(true);
  };

  const handleSave = () => {
    updateMutation.mutate(editForm);
  };

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      {/* Top Navigation Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <button
          onClick={() => navigate('/calls')}
          className="inline-flex items-center gap-2 text-xs font-medium text-slate-400 hover:text-white transition-colors"
        >
          <ArrowLeft className="h-4 w-4" /> Back to Calls Directory
        </button>

        <div className="flex items-center gap-2 flex-wrap">
          <button
            onClick={() => reprocessMutation.mutate()}
            disabled={reprocessMutation.isPending || !call.transcript}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-500/10 hover:bg-indigo-500/20 text-indigo-400 text-xs font-medium border border-indigo-500/30 disabled:opacity-40"
          >
            <RotateCw className={`h-3.5 w-3.5 ${reprocessMutation.isPending ? 'animate-spin' : ''}`} />
            Reprocess (Qwen 4B)
          </button>

          <button
            onClick={() => retranscribeMutation.mutate()}
            disabled={retranscribeMutation.isPending}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-purple-500/10 hover:bg-purple-500/20 text-purple-400 text-xs font-medium border border-purple-500/30 disabled:opacity-40"
          >
            <Mic className={`h-3.5 w-3.5 ${retranscribeMutation.isPending ? 'animate-spin' : ''}`} />
            Retranscribe Audio
          </button>

          <button
            onClick={() => deleteMutation.mutate()}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 text-xs font-medium border border-rose-500/30"
          >
            <Trash2 className="h-3.5 w-3.5" /> Delete
          </button>
        </div>
      </div>

      {actionMsg && (
        <div className="p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-lg text-xs text-emerald-300 flex items-center gap-2">
          <CheckCircle className="h-4 w-4 text-emerald-400" />
          {actionMsg}
        </div>
      )}

      {/* Main Header Banner */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/90 p-6 shadow-xl space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
          <div>
            <div className="flex items-center gap-3">
              <h2 className="text-xl font-bold text-white">{call.company_name}</h2>
              <StatusBadge status={call.call_status} />
              <StatusBadge status={call.processing_status} type="processing" />
            </div>
            <p className="text-xs text-slate-400 mt-1 flex items-center gap-4">
              <span>Telecaller: <strong>{call.telecaller_name}</strong></span>
              <span>Category: <strong>{call.business_category || call.submitted_category || 'N/A'}</strong></span>
              <span>Audio Duration: <strong>{call.audio_duration}s</strong></span>
            </p>
          </div>

          {!isEditing ? (
            <button
              onClick={startEdit}
              className="px-4 py-2 rounded-lg bg-sky-500/10 hover:bg-sky-500/20 text-sky-400 border border-sky-500/30 text-xs font-medium"
            >
              Edit Extracted Fields
            </button>
          ) : (
            <div className="flex items-center gap-2">
              <button
                onClick={handleSave}
                disabled={updateMutation.isPending}
                className="px-4 py-2 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-white text-xs font-medium inline-flex items-center gap-1.5"
              >
                <Save className="h-3.5 w-3.5" /> Save Changes
              </button>
              <button
                onClick={() => setIsEditing(false)}
                className="px-3 py-2 rounded-lg bg-slate-800 text-slate-400 hover:text-white text-xs"
              >
                Cancel
              </button>
            </div>
          )}
        </div>
      </div>

      {/* 1. DIRECT TRANSCRIBED SPEECH TEXT FROM TRANSCRIBER (FIRST) */}
      <div className="rounded-xl border border-sky-500/30 bg-slate-900/90 p-6 space-y-4 shadow-xl ring-1 ring-sky-500/20">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
            <FileText className="h-4 w-4 text-sky-400" /> 1. Direct Transcribed Speech Text (IndicConformer STT)
          </h3>
          <span className="text-[11px] font-mono px-2.5 py-0.5 rounded bg-sky-500/10 text-sky-300 border border-sky-500/20">
            Hindi / English Mixed Output
          </span>
        </div>

        {isEditing ? (
          <div>
            <label className="block text-xs font-semibold text-slate-400 mb-1">Edit Speech Transcript:</label>
            <textarea
              rows={6}
              value={editForm.transcript}
              onChange={(e) => setEditForm({ ...editForm, transcript: e.target.value })}
              className="w-full p-3 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white font-sans focus:outline-none focus:ring-1 focus:ring-sky-500"
            />
          </div>
        ) : (
          <div className="p-4 bg-slate-950 rounded-xl border border-slate-800/80 text-xs text-slate-100 leading-relaxed font-sans whitespace-pre-wrap selection:bg-sky-500/30 max-h-[400px] overflow-y-auto">
            {call.transcript || 'No transcript generated yet.'}
          </div>
        )}
      </div>

      {/* 2. EXTRACTED LEAD INTELLIGENCE FROM QWEN 4B (SECOND) */}
      <div className="rounded-xl border border-indigo-500/30 bg-slate-900/90 p-6 space-y-6 shadow-xl ring-1 ring-indigo-500/20">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-indigo-400" /> 2. Extracted Business Lead Intelligence (Qwen 4B LLM)
          </h3>
          <StatusBadge status={call.call_status} />
        </div>

        {/* AI Summary */}
        <div className="p-4 bg-slate-950/80 rounded-xl border border-slate-800 space-y-2">
          <h4 className="text-xs font-semibold text-sky-400 uppercase tracking-wider flex items-center gap-1.5">
            <MessageSquare className="h-3.5 w-3.5" /> Call Summary
          </h4>
          {isEditing ? (
            <textarea
              rows={2}
              value={editForm.summary}
              onChange={(e) => setEditForm({ ...editForm, summary: e.target.value })}
              className="w-full p-2 bg-slate-950 border border-slate-800 rounded text-xs text-white"
            />
          ) : (
            <p className="text-xs text-slate-200 leading-relaxed font-sans">{call.summary || 'Summary pending processing.'}</p>
          )}
        </div>

        {/* Extracted Fields Form / Display */}
        <div className="space-y-4 text-xs">
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
            <div>
              <span className="text-slate-400 block mb-1">Contact Person:</span>
              {isEditing ? (
                <input
                  type="text"
                  value={editForm.contact_person_name}
                  onChange={(e) => setEditForm({ ...editForm, contact_person_name: e.target.value })}
                  className="w-full p-2 bg-slate-950 border border-slate-800 rounded text-white"
                />
              ) : (
                <p className="font-semibold text-white">{call.contact_person_name || 'N/A'}</p>
              )}
            </div>

            <div>
              <span className="text-slate-400 block mb-1">Phone Number:</span>
              {isEditing ? (
                <input
                  type="text"
                  value={editForm.phone_number}
                  onChange={(e) => setEditForm({ ...editForm, phone_number: e.target.value })}
                  className="w-full p-2 bg-slate-950 border border-slate-800 rounded text-white"
                />
              ) : (
                <p className="font-mono text-slate-300">
                  {call.phone_number || call.submitted_phone_number} {call.alternate_phone_number && `(${call.alternate_phone_number})`}
                </p>
              )}
            </div>

            <div>
              <span className="text-slate-400 block mb-1">Call Status:</span>
              {isEditing ? (
                <select
                  value={editForm.call_status}
                  onChange={(e) => setEditForm({ ...editForm, call_status: e.target.value as CallStatus })}
                  className="w-full p-2 bg-slate-950 border border-slate-800 rounded text-white"
                >
                  <option value="interested">Interested</option>
                  <option value="ordered">Ordered</option>
                  <option value="not_interested">Not Interested</option>
                  <option value="did_not_pick">Did Not Pick</option>
                  <option value="callback_requested">Callback Requested</option>
                  <option value="follow_up_required">Follow-up Required</option>
                  <option value="wrong_number">Wrong Number</option>
                  <option value="unavailable">Unavailable</option>
                  <option value="unclear">Unclear</option>
                </select>
              ) : (
                <StatusBadge status={call.call_status} />
              )}
            </div>
          </div>

          <div>
            <span className="text-slate-400 block mb-1">Customer Intent:</span>
            {isEditing ? (
              <textarea
                value={editForm.customer_intent}
                onChange={(e) => setEditForm({ ...editForm, customer_intent: e.target.value })}
                className="w-full p-2 bg-slate-950 border border-slate-800 rounded text-white"
              />
            ) : (
              <p className="text-slate-200">{call.customer_intent || 'N/A'}</p>
            )}
          </div>

          <div>
            <span className="text-slate-400 block mb-1">Products / Services Discussed:</span>
            <div className="flex flex-wrap gap-1.5 mt-1">
              {call.products_or_services_discussed.length > 0 ? (
                call.products_or_services_discussed.map((p, idx) => (
                  <span key={idx} className="px-2 py-0.5 rounded bg-sky-500/10 text-sky-300 border border-sky-500/20">
                    {p}
                  </span>
                ))
              ) : (
                <span className="text-slate-500 italic">None logged</span>
              )}
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <span className="text-slate-400 block mb-1">Quantity / Licenses:</span>
              <p className="font-semibold text-slate-200">{call.quantity || 'N/A'}</p>
            </div>
            <div>
              <span className="text-slate-400 block mb-1">Budget / Price:</span>
              <p className="font-semibold text-emerald-400">{call.budget_or_price || 'N/A'}</p>
            </div>
            <div>
              <span className="text-slate-400 block mb-1">Follow-up Date:</span>
              <p className="font-mono text-amber-300">{call.follow_up_date || 'N/A'}</p>
            </div>
            <div>
              <span className="text-slate-400 block mb-1">Follow-up Time:</span>
              <p className="font-mono text-slate-300">{call.follow_up_time || 'N/A'}</p>
            </div>
          </div>

          <div>
            <span className="text-slate-400 block mb-1">Customer Objections:</span>
            <div className="flex flex-wrap gap-1.5 mt-1">
              {call.objections.length > 0 ? (
                call.objections.map((o, idx) => (
                  <span key={idx} className="px-2 py-0.5 rounded bg-rose-500/10 text-rose-300 border border-rose-500/20">
                    {o}
                  </span>
                ))
              ) : (
                <span className="text-slate-500 italic">No objections raised</span>
              )}
            </div>
          </div>

          <div>
            <span className="text-slate-400 block mb-1">AI Confidence Score:</span>
            <p className="font-mono text-emerald-400 font-bold">
              {Math.round(call.confidence_score * 100)}%
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
