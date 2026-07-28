import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQueryClient } from '@tanstack/react-query';
import { 
  Upload, 
  AlertCircle, 
  ArrowRight, 
  FileAudio, 
  Trash2, 
  FileText, 
  Sparkles, 
  CheckCircle2, 
  PlusCircle
} from 'lucide-react';
import { uploadCallRecording, fetchCallStatus, fetchCallDetail } from '../api/client';
import { ProgressBar } from '../components/ProgressBar';
import { StatusBadge } from '../components/StatusBadge';
import { ProcessingStatus, CallRecord } from '../types';

export const UploadPage: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Form State (All optional except selectedFile)
  const [telecallerName, setTelecallerName] = useState('');
  const [companyName, setCompanyName] = useState('');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [category, setCategory] = useState('');
  const [notes, setNotes] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [audioPreviewUrl, setAudioPreviewUrl] = useState<string | null>(null);
  const [audioDuration, setAudioDuration] = useState<number | null>(null);

  // UI & Job State
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [activeCallId, setActiveCallId] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<ProcessingStatus | null>(null);
  const [jobStage, setJobStage] = useState<string | null>(null);
  const [jobError, setJobError] = useState<string | null>(null);
  const [completedRecord, setCompletedRecord] = useState<CallRecord | null>(null);

  const handleFileChange = (file: File | null) => {
    setErrorMsg(null);
    if (!file) {
      setSelectedFile(null);
      setAudioPreviewUrl(null);
      return;
    }

    if (file.size > 50 * 1024 * 1024) {
      setErrorMsg('Selected file exceeds maximum limit of 50 MB.');
      return;
    }

    setSelectedFile(file);
    const url = URL.createObjectURL(file);
    setAudioPreviewUrl(url);

    const audioEl = new Audio(url);
    audioEl.onloadedmetadata = () => {
      setAudioDuration(audioEl.duration);
      if (audioEl.duration > 15 * 60) {
        setErrorMsg(`Audio duration (${Math.round(audioEl.duration / 60)} mins) exceeds maximum 15 minutes limit.`);
      }
    };
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileChange(e.dataTransfer.files[0]);
    }
  };

  // Job status polling effect
  useEffect(() => {
    if (!activeCallId) return;

    const interval = setInterval(async () => {
      try {
        const res = await fetchCallStatus(activeCallId);
        setJobStatus(res.processing_status);
        setJobStage(res.processing_stage || null);
        setJobError(res.error_message || null);

        if (res.processing_status === 'completed') {
          clearInterval(interval);
          const detail = await fetchCallDetail(activeCallId);
          setCompletedRecord(detail);
          queryClient.invalidateQueries({ queryKey: ['calls'] });
          queryClient.invalidateQueries({ queryKey: ['stats'] });
        } else if (res.processing_status === 'failed') {
          clearInterval(interval);
          queryClient.invalidateQueries({ queryKey: ['calls'] });
          queryClient.invalidateQueries({ queryKey: ['stats'] });
        }
      } catch (err) {
        console.error('Status polling error:', err);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [activeCallId, queryClient]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);

    // ONLY Audio File is mandatory
    if (!selectedFile) {
      setErrorMsg('Please select or drop an audio recording file.');
      return;
    }

    try {
      setIsSubmitting(true);
      setCompletedRecord(null);
      const formData = new FormData();
      if (telecallerName.trim()) formData.append('telecaller_name', telecallerName.trim());
      if (companyName.trim()) formData.append('company_name', companyName.trim());
      if (phoneNumber.trim()) formData.append('phone_number', phoneNumber.trim());
      if (category) formData.append('category', category);
      if (notes.trim()) formData.append('notes', notes.trim());
      formData.append('file', selectedFile);

      const res = await uploadCallRecording(formData);
      setActiveCallId(res.call_id);
      setJobStatus('queued');
      setJobStage('Queued for processing');
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to upload audio recording. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const resetForm = () => {
    setActiveCallId(null);
    setJobStatus(null);
    setJobStage(null);
    setJobError(null);
    setCompletedRecord(null);
    setSelectedFile(null);
    setAudioPreviewUrl(null);
    setTelecallerName('');
    setCompanyName('');
    setPhoneNumber('');
    setCategory('');
    setNotes('');
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div>
        <h2 className="text-2xl font-bold text-white tracking-tight">Upload Call Recording</h2>
        <p className="text-sm text-slate-400">Upload audio for automated speech transcription and Qwen 4B lead extraction. All metadata fields are optional.</p>
      </div>

      {errorMsg && (
        <div className="p-4 bg-rose-500/10 border border-rose-500/30 rounded-xl text-rose-300 text-sm flex items-center gap-3">
          <AlertCircle className="h-5 w-5 text-rose-400 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Live Job Progress Bar */}
      {jobStatus && (
        <div className="space-y-6">
          <ProgressBar status={jobStatus} stage={jobStage} errorMessage={jobError} />
        </div>
      )}

      {/* Output Display after completion: 1. Transcribed Text -> 2. Qwen 4B Extracted Insights */}
      {completedRecord && (
        <div className="space-y-6 animate-fadeIn">
          {/* Banner */}
          <div className="p-4 bg-emerald-500/10 border border-emerald-500/30 rounded-xl flex items-center justify-between">
            <div className="flex items-center gap-3">
              <CheckCircle2 className="h-6 w-6 text-emerald-400 shrink-0" />
              <div>
                <h3 className="text-sm font-semibold text-emerald-300">Processing Completed Successfully!</h3>
                <p className="text-xs text-slate-300">
                  Call audio processed for <strong>{completedRecord.company_name}</strong>.
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={resetForm}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-white text-xs font-medium border border-slate-700"
              >
                <PlusCircle className="h-3.5 w-3.5" /> Upload Another Call
              </button>
              <button
                onClick={() => navigate(`/calls/${completedRecord.id}`)}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-white text-xs font-medium shadow"
              >
                Full Detail View <ArrowRight className="h-3.5 w-3.5" />
              </button>
            </div>
          </div>

          {/* 1. DIRECT TRANSCRIBED SPEECH TEXT FROM TRANSCRIBER */}
          <div className="rounded-xl border border-sky-500/30 bg-slate-900/90 p-6 space-y-3 shadow-xl ring-1 ring-sky-500/20">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                <FileText className="h-4 w-4 text-sky-400" /> 1. Direct Speech Transcript
              </h3>
              <span className="text-[11px] font-mono px-2.5 py-0.5 rounded bg-sky-500/10 text-sky-300 border border-sky-500/20">
                Speech-to-Text Model Output
              </span>
            </div>
            <div className="p-4 bg-slate-950 rounded-xl border border-slate-800/80 text-xs text-slate-100 leading-relaxed font-sans whitespace-pre-wrap selection:bg-sky-500/30">
              {completedRecord.transcript || 'No transcript text generated.'}
            </div>
          </div>

          {/* 2. EXTRACTED INFORMATION FROM QWEN 4B */}
          <div className="rounded-xl border border-indigo-500/30 bg-slate-900/90 p-6 space-y-6 shadow-xl ring-1 ring-indigo-500/20">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-indigo-400" /> 2. Extracted Business Lead Intelligence (Qwen 4B LLM)
              </h3>
              <StatusBadge status={completedRecord.call_status} />
            </div>

            {/* AI Summary */}
            <div className="p-4 bg-slate-950/80 rounded-xl border border-slate-800 space-y-1">
              <span className="text-xs font-semibold text-sky-400 uppercase tracking-wider">Call Summary:</span>
              <p className="text-xs text-slate-200 leading-relaxed font-sans">{completedRecord.summary || 'N/A'}</p>
            </div>

            {/* Extracted Fields Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4 text-xs">
              <div className="p-3 bg-slate-950 rounded-lg border border-slate-800/80 space-y-1">
                <span className="text-slate-400 block text-[11px]">Contact Person Name:</span>
                <p className="font-semibold text-white">{completedRecord.contact_person_name || 'N/A'}</p>
              </div>

              <div className="p-3 bg-slate-950 rounded-lg border border-slate-800/80 space-y-1">
                <span className="text-slate-400 block text-[11px]">Phone Number:</span>
                <p className="font-mono text-slate-200">{completedRecord.phone_number || completedRecord.submitted_phone_number}</p>
              </div>

              <div className="p-3 bg-slate-950 rounded-lg border border-slate-800/80 space-y-1">
                <span className="text-slate-400 block text-[11px]">Business Category:</span>
                <p className="font-semibold text-slate-200">{completedRecord.business_category || completedRecord.submitted_category || 'N/A'}</p>
              </div>

              <div className="p-3 bg-slate-950 rounded-lg border border-slate-800/80 space-y-1 md:col-span-3">
                <span className="text-slate-400 block text-[11px]">Customer Intent:</span>
                <p className="text-slate-200">{completedRecord.customer_intent || 'N/A'}</p>
              </div>

              <div className="p-3 bg-slate-950 rounded-lg border border-slate-800/80 space-y-1 md:col-span-2">
                <span className="text-slate-400 block text-[11px]">Products / Services Discussed:</span>
                <div className="flex flex-wrap gap-1.5 mt-1">
                  {completedRecord.products_or_services_discussed.length > 0 ? (
                    completedRecord.products_or_services_discussed.map((prod, idx) => (
                      <span key={idx} className="px-2 py-0.5 rounded bg-sky-500/10 text-sky-300 border border-sky-500/20 text-[11px]">
                        {prod}
                      </span>
                    ))
                  ) : (
                    <span className="text-slate-500 italic">None logged</span>
                  )}
                </div>
              </div>

              <div className="p-3 bg-slate-950 rounded-lg border border-slate-800/80 space-y-1">
                <span className="text-slate-400 block text-[11px]">Budget / Quoted Price:</span>
                <p className="font-semibold text-emerald-400">{completedRecord.budget_or_price || 'N/A'}</p>
              </div>

              <div className="p-3 bg-slate-950 rounded-lg border border-slate-800/80 space-y-1">
                <span className="text-slate-400 block text-[11px]">Quantity / Licenses:</span>
                <p className="font-semibold text-slate-200">{completedRecord.quantity || 'N/A'}</p>
              </div>

              <div className="p-3 bg-slate-950 rounded-lg border border-slate-800/80 space-y-1">
                <span className="text-slate-400 block text-[11px]">Follow-up Date:</span>
                <p className="font-mono text-amber-300 font-semibold">{completedRecord.follow_up_date || 'N/A'}</p>
              </div>

              <div className="p-3 bg-slate-950 rounded-lg border border-slate-800/80 space-y-1">
                <span className="text-slate-400 block text-[11px]">AI Confidence Score:</span>
                <p className="font-mono text-emerald-400 font-bold">{Math.round(completedRecord.confidence_score * 100)}%</p>
              </div>

              <div className="p-3 bg-slate-950 rounded-lg border border-slate-800/80 space-y-1 md:col-span-3">
                <span className="text-slate-400 block text-[11px]">Customer Objections:</span>
                <div className="flex flex-wrap gap-1.5 mt-1">
                  {completedRecord.objections.length > 0 ? (
                    completedRecord.objections.map((obj, idx) => (
                      <span key={idx} className="px-2 py-0.5 rounded bg-rose-500/10 text-rose-300 border border-rose-500/20 text-[11px]">
                        {obj}
                      </span>
                    ))
                  ) : (
                    <span className="text-slate-500 italic">No objections logged</span>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Upload Form view */}
      {(!jobStatus || jobStatus === 'failed') && (
        <form onSubmit={handleSubmit} className="rounded-xl border border-slate-800 bg-slate-900/80 p-6 md:p-8 space-y-6 shadow-xl">
          {/* Mandatory Audio Dropzone at top */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
              Call Audio Recording File <span className="text-rose-400">* (Required)</span>
            </label>

            {!selectedFile ? (
              <div
                onDragOver={(e) => e.preventDefault()}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                className="border-2 border-dashed border-slate-800 hover:border-sky-500/60 rounded-xl p-8 text-center bg-slate-950/50 hover:bg-slate-950 transition-all cursor-pointer group"
              >
                <input
                  type="file"
                  ref={fileInputRef}
                  onChange={(e) => e.target.files?.[0] && handleFileChange(e.target.files[0])}
                  accept=".mp3,.wav,.m4a,.aac,.ogg,.webm"
                  className="hidden"
                />
                <div className="mx-auto w-12 h-12 rounded-full bg-slate-800/80 group-hover:bg-sky-500/10 flex items-center justify-center text-slate-400 group-hover:text-sky-400 transition-colors">
                  <Upload className="h-6 w-6" />
                </div>
                <p className="mt-4 text-sm font-medium text-slate-200">
                  Drag and drop audio file here, or <span className="text-sky-400 underline">browse computer</span>
                </p>
                <p className="mt-1 text-xs text-slate-500">
                  Supports MP3, WAV, M4A, AAC, OGG, WebM (Max 50 MB & 15 mins)
                </p>
              </div>
            ) : (
              <div className="p-4 bg-slate-950 border border-slate-800 rounded-xl space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-sky-500/10 text-sky-400">
                      <FileAudio className="h-6 w-6" />
                    </div>
                    <div>
                      <p className="text-sm font-medium text-white truncate max-w-xs">{selectedFile.name}</p>
                      <p className="text-xs text-slate-400">
                        Size: {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
                        {audioDuration && ` | Duration: ${Math.floor(audioDuration / 60)}m ${Math.round(audioDuration % 60)}s`}
                      </p>
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={() => handleFileChange(null)}
                    className="p-1.5 text-slate-400 hover:text-rose-400 rounded-lg hover:bg-slate-900"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>

                {audioPreviewUrl && (
                  <audio controls src={audioPreviewUrl} className="w-full h-8 rounded" />
                )}
              </div>
            )}
          </div>

          {/* Optional Metadata Section */}
          <div className="border-t border-slate-800/80 pt-6">
            <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-4">
              Optional Metadata Details (Non-compulsory)
            </h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">
                  Telecaller Name (Optional)
                </label>
                <input
                  type="text"
                  placeholder="e.g. Rahul Sharma"
                  value={telecallerName}
                  onChange={(e) => setTelecallerName(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-lg bg-slate-950 border border-slate-800 text-white text-sm focus:outline-none focus:ring-2 focus:ring-sky-500/50 focus:border-sky-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">
                  Company Name (Optional)
                </label>
                <input
                  type="text"
                  placeholder="e.g. Acme Corp India"
                  value={companyName}
                  onChange={(e) => setCompanyName(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-lg bg-slate-950 border border-slate-800 text-white text-sm focus:outline-none focus:ring-2 focus:ring-sky-500/50 focus:border-sky-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">
                  Customer Phone Number (Optional)
                </label>
                <input
                  type="text"
                  placeholder="e.g. +91 9876543210"
                  value={phoneNumber}
                  onChange={(e) => setPhoneNumber(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-lg bg-slate-950 border border-slate-800 text-white text-sm focus:outline-none focus:ring-2 focus:ring-sky-500/50 focus:border-sky-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">
                  Business Category (Optional)
                </label>
                <select
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-lg bg-slate-950 border border-slate-800 text-white text-sm focus:outline-none focus:ring-2 focus:ring-sky-500/50 focus:border-sky-500"
                >
                  <option value="">-- Select Category --</option>
                  <option value="Software & IT">Software & IT</option>
                  <option value="Real Estate">Real Estate</option>
                  <option value="Financial Services">Financial Services</option>
                  <option value="Healthcare">Healthcare</option>
                  <option value="Education & EdTech">Education & EdTech</option>
                  <option value="Manufacturing & Retail">Manufacturing & Retail</option>
                  <option value="Other">Other</option>
                </select>
              </div>
            </div>

            <div className="mt-4">
              <label className="block text-xs font-medium text-slate-400 mb-1">
                Telecaller Notes / Observations (Optional)
              </label>
              <textarea
                rows={2}
                placeholder="e.g. Customer asked for pricing demo next week."
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                className="w-full px-4 py-2.5 rounded-lg bg-slate-950 border border-slate-800 text-white text-sm focus:outline-none focus:ring-2 focus:ring-sky-500/50 focus:border-sky-500"
              />
            </div>
          </div>

          <div className="pt-4 flex justify-end">
            <button
              type="submit"
              disabled={isSubmitting || !selectedFile}
              className="inline-flex items-center gap-2 px-6 py-3 rounded-lg bg-sky-500 hover:bg-sky-400 text-white font-medium text-sm transition-all shadow-lg shadow-sky-500/25 disabled:opacity-50"
            >
              {isSubmitting ? (
                <>Uploading & Transcribing...</>
              ) : (
                <>
                  <Upload className="h-4 w-4" /> Start AI Transcription & Extraction
                </>
              )}
            </button>
          </div>
        </form>
      )}
    </div>
  );
};
