import React, { useState } from 'react';
import { Download, FileSpreadsheet, Filter, CheckCircle2 } from 'lucide-react';
import { getExportCsvUrl } from '../api/client';

export const ExportPage: React.FC = () => {
  const [telecaller, setTelecaller] = useState('');
  const [status, setStatus] = useState('');
  const [category, setCategory] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');

  const handleDownload = () => {
    const url = getExportCsvUrl({
      telecaller: telecaller || undefined,
      status: status || undefined,
      category: category || undefined,
      start_date: startDate || undefined,
      end_date: endDate || undefined,
    });
    window.open(url, '_blank');
  };

  return (
    <div className="max-w-3xl mx-auto space-y-8">
      <div>
        <h2 className="text-2xl font-bold text-white tracking-tight">CSV Business Reports & Exports</h2>
        <p className="text-sm text-slate-400">Download formatted CSV reports containing full call transcripts, lead status, objections, and confidence metrics.</p>
      </div>

      <div className="rounded-xl border border-slate-800 bg-slate-900/80 p-6 md:p-8 space-y-6 shadow-xl">
        <div className="flex items-center gap-3 border-b border-slate-800 pb-4">
          <div className="p-3 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <FileSpreadsheet className="h-6 w-6" />
          </div>
          <div>
            <h3 className="text-base font-semibold text-white">Export Filter Options</h3>
            <p className="text-xs text-slate-400">Select parameters to filter exported CSV records or download full master report.</p>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 text-xs">
          <div>
            <label className="block font-semibold text-slate-300 uppercase tracking-wider mb-2">
              Telecaller Name
            </label>
            <input
              type="text"
              placeholder="e.g. Rahul Sharma"
              value={telecaller}
              onChange={(e) => setTelecaller(e.target.value)}
              className="w-full px-4 py-2.5 rounded-lg bg-slate-950 border border-slate-800 text-white focus:outline-none focus:ring-2 focus:ring-sky-500"
            />
          </div>

          <div>
            <label className="block font-semibold text-slate-300 uppercase tracking-wider mb-2">
              Call Status
            </label>
            <select
              value={status}
              onChange={(e) => setStatus(e.target.value)}
              className="w-full px-4 py-2.5 rounded-lg bg-slate-950 border border-slate-800 text-white focus:outline-none focus:ring-2 focus:ring-sky-500"
            >
              <option value="">All Call Statuses</option>
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
          </div>

          <div>
            <label className="block font-semibold text-slate-300 uppercase tracking-wider mb-2">
              Business Category
            </label>
            <input
              type="text"
              placeholder="e.g. Software & IT"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="w-full px-4 py-2.5 rounded-lg bg-slate-950 border border-slate-800 text-white focus:outline-none focus:ring-2 focus:ring-sky-500"
            />
          </div>

          <div>
            <label className="block font-semibold text-slate-300 uppercase tracking-wider mb-2">
              Start Date
            </label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="w-full px-4 py-2.5 rounded-lg bg-slate-950 border border-slate-800 text-white focus:outline-none focus:ring-2 focus:ring-sky-500"
            />
          </div>

          <div>
            <label className="block font-semibold text-slate-300 uppercase tracking-wider mb-2">
              End Date
            </label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="w-full px-4 py-2.5 rounded-lg bg-slate-950 border border-slate-800 text-white focus:outline-none focus:ring-2 focus:ring-sky-500"
            />
          </div>
        </div>

        <div className="p-4 bg-slate-950/60 rounded-lg border border-slate-800 space-y-2 text-xs text-slate-400">
          <p className="font-semibold text-slate-200 flex items-center gap-1.5">
            <CheckCircle2 className="h-4 w-4 text-emerald-400" /> Export CSV Specifications:
          </p>
          <ul className="list-disc list-inside space-y-1 text-slate-400">
            <li>Includes metadata: ID, Telecaller, Company, Phone, Email, Status, Intent, Budget</li>
            <li>Arrays such as objections and products are formatted as semicolon-separated values.</li>
            <li>Contains full AI speech transcript and duration breakdown.</li>
          </ul>
        </div>

        <div className="pt-2 flex justify-end">
          <button
            onClick={handleDownload}
            className="inline-flex items-center gap-2 px-6 py-3 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-white font-medium text-sm transition-all shadow-lg shadow-emerald-500/25"
          >
            <Download className="h-4 w-4" /> Download Filtered CSV Report
          </button>
        </div>
      </div>
    </div>
  );
};
