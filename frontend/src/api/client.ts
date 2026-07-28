import axios from 'axios';
import { CallRecord, CallListResponse, DashboardStats, CallStatusResponse, CallFilterParams } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const fetchHealth = async () => {
  const { data } = await apiClient.get('/health');
  return data;
};

export const fetchStats = async (): Promise<DashboardStats> => {
  const { data } = await apiClient.get<DashboardStats>('/stats');
  return data;
};

export const uploadCallRecording = async (formData: FormData) => {
  const { data } = await apiClient.post<{ call_id: string; processing_status: string }>('/calls', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return data;
};

export const fetchCalls = async (params: CallFilterParams): Promise<CallListResponse> => {
  const { data } = await apiClient.get<CallListResponse>('/calls', { params });
  return data;
};

export const fetchCallDetail = async (callId: string): Promise<CallRecord> => {
  const { data } = await apiClient.get<CallRecord>(`/calls/${callId}`);
  return data;
};

export const fetchCallStatus = async (callId: string): Promise<CallStatusResponse> => {
  const { data } = await apiClient.get<CallStatusResponse>(`/calls/${callId}/status`);
  return data;
};

export const updateCallRecord = async (callId: string, payload: Partial<CallRecord>): Promise<CallRecord> => {
  const { data } = await apiClient.patch<CallRecord>(`/calls/${callId}`, payload);
  return data;
};

export const deleteCallRecord = async (callId: string): Promise<void> => {
  await apiClient.delete(`/calls/${callId}`);
};

export const reprocessCallExtraction = async (callId: string): Promise<CallStatusResponse> => {
  const { data } = await apiClient.post<CallStatusResponse>(`/calls/${callId}/reprocess`);
  return data;
};

export const retranscribeCallAudio = async (callId: string): Promise<CallStatusResponse> => {
  const { data } = await apiClient.post<CallStatusResponse>(`/calls/${callId}/retranscribe`);
  return data;
};

export const getExportCsvUrl = (params: CallFilterParams = {}) => {
  const searchParams = new URLSearchParams();
  if (params.telecaller) searchParams.set('telecaller', params.telecaller);
  if (params.status) searchParams.set('status', params.status);
  if (params.category) searchParams.set('category', params.category);
  if (params.start_date) searchParams.set('start_date', params.start_date);
  if (params.end_date) searchParams.set('end_date', params.end_date);

  const queryStr = searchParams.toString();
  return `${API_BASE_URL}/export/csv${queryStr ? `?${queryStr}` : ''}`;
};
