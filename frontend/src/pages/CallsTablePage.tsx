import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { Search, Filter, RefreshCw, ChevronLeft, ChevronRight, Eye } from 'lucide-react';
import { fetchCalls } from '../api/client';
import { StatusBadge } from '../components/StatusBadge';
import { CallFilterParams } from '../types';

export const CallsTablePage: React.FC = () => {
  const [page, setPage] = useState(1);
  const [pageSize] = useState(10);
  const [search, setSearch] = useState('');
  const [telecaller, setTelecaller] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [processingStatus, setProcessingStatus] = useState('');

  const filterParams: CallFilterParams = {
    page,
    page_size: pageSize,
    search: search || undefined,
    telecaller: telecaller || undefined,
    status: statusFilter || undefined,
    category: categoryFilter || undefined,
    processing_status: processingStatus || undefined,
  };

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['calls', filterParams],
    queryFn: () => fetchCalls(filterParams),
  });

  const totalPages = data ? Math.ceil(data.total / pageSize) : 1;

  const handleResetFilters = () => {
    setSearch('');
    setTelecaller('');
    setStatusFilter('');
    setCategoryFilter('');
    setProcessingStatus('');
    setPage(1);
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white tracking-tight">Call Recordings & Leads Directory</h2>
          <p className="text-sm text-slate-400">Search, filter, and inspect transcribed call logs and extracted business leads.</p>
        </div>
        <button
          onClick={() => refetch()}
          className="inline-flex items-center gap-2 px-3 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium border border-slate-700"
        >
          <RefreshCw className="h-3.5 w-3.5" /> Refresh List
        </button>
      </div>

      {/* Filter Controls Bar */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/80 p-4 space-y-4 shadow-lg">
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-5 gap-3">
          {/* Search Input */}
          <div className="relative md:col-span-2">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
            <input
              type="text"
              placeholder="Search company, telecaller, phone, summary..."
              value={search}
              onChange={(e) => { setSearch(e.target.value); setPage(1); }}
              className="w-full pl-9 pr-4 py-2 rounded-lg bg-slate-950 border border-slate-800 text-white text-xs focus:outline-none focus:ring-1 focus:ring-sky-500"
            />
          </div>

          {/* Status Filter */}
          <select
            value={statusFilter}
            onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
            className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-white text-xs focus:outline-none focus:ring-1 focus:ring-sky-500"
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

          {/* Processing Status Filter */}
          <select
            value={processingStatus}
            onChange={(e) => { setProcessingStatus(e.target.value); setPage(1); }}
            className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-white text-xs focus:outline-none focus:ring-1 focus:ring-sky-500"
          >
            <option value="">All Processing States</option>
            <option value="queued">Queued</option>
            <option value="converting">Converting</option>
            <option value="transcribing">Transcribing</option>
            <option value="extracting">Extracting</option>
            <option value="completed">Completed</option>
            <option value="failed">Failed</option>
          </select>

          {/* Reset button */}
          <button
            onClick={handleResetFilters}
            className="w-full py-2 px-3 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium border border-slate-700 flex items-center justify-center gap-1"
          >
            <Filter className="h-3.5 w-3.5" /> Reset Filters
          </button>
        </div>
      </div>

      {/* Table Section */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/80 shadow-xl overflow-hidden">
        {isLoading ? (
          <div className="p-12 text-center text-slate-500 space-y-2">
            <RefreshCw className="h-6 w-6 animate-spin mx-auto text-sky-400" />
            <p className="text-sm">Loading call recordings directory...</p>
          </div>
        ) : isError ? (
          <div className="p-8 text-center text-rose-400">
            Failed to load call recordings. Please verify server status.
          </div>
        ) : data?.items.length === 0 ? (
          <div className="p-12 text-center text-slate-500">
            No call records found matching selected filter criteria.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="border-b border-slate-800 text-slate-400 uppercase tracking-wider bg-slate-950/60">
                <tr>
                  <th className="py-3 px-4">Date & Time</th>
                  <th className="py-3 px-4">Telecaller</th>
                  <th className="py-3 px-4">Company</th>
                  <th className="py-3 px-4">Phone</th>
                  <th className="py-3 px-4">Call Status</th>
                  <th className="py-3 px-4">Contact Person</th>
                  <th className="py-3 px-4">Follow-up</th>
                  <th className="py-3 px-4">AI Processing</th>
                  <th className="py-3 px-4">Confidence</th>
                  <th className="py-3 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {data?.items.map((call) => (
                  <tr key={call.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="py-3 px-4 font-mono text-slate-400">
                      {new Date(call.created_at).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' })}
                    </td>
                    <td className="py-3 px-4 font-medium text-white">{call.telecaller_name}</td>
                    <td className="py-3 px-4">{call.company_name}</td>
                    <td className="py-3 px-4 font-mono text-slate-400">{call.phone_number || call.submitted_phone_number}</td>
                    <td className="py-3 px-4">
                      <StatusBadge status={call.call_status} />
                    </td>
                    <td className="py-3 px-4 text-slate-300">{call.contact_person_name || '-'}</td>
                    <td className="py-3 px-4 font-mono text-amber-300">{call.follow_up_date || '-'}</td>
                    <td className="py-3 px-4">
                      <StatusBadge status={call.processing_status} type="processing" />
                    </td>
                    <td className="py-3 px-4 font-mono text-emerald-400">
                      {call.confidence_score ? `${Math.round(call.confidence_score * 100)}%` : '-'}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <Link 
                        to={`/calls/${call.id}`}
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-sky-500/10 hover:bg-sky-500/20 text-sky-400 font-medium transition-all border border-sky-500/20"
                      >
                        <Eye className="h-3.5 w-3.5" /> View
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Footer */}
        {data && data.total > 0 && (
          <div className="p-4 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400 bg-slate-950/40">
            <span>
              Showing {((page - 1) * pageSize) + 1} to {Math.min(page * pageSize, data.total)} of {data.total} records
            </span>
            <div className="flex items-center gap-2">
              <button
                disabled={page <= 1}
                onClick={() => setPage((p) => p - 1)}
                className="p-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 disabled:opacity-40"
              >
                <ChevronLeft className="h-4 w-4" />
              </button>
              <span className="font-mono text-white">Page {page} of {totalPages}</span>
              <button
                disabled={page >= totalPages}
                onClick={() => setPage((p) => p + 1)}
                className="p-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 disabled:opacity-40"
              >
                <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
