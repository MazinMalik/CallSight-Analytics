export type CallStatus = 
  | 'interested'
  | 'ordered'
  | 'not_interested'
  | 'did_not_pick'
  | 'callback_requested'
  | 'follow_up_required'
  | 'wrong_number'
  | 'unavailable'
  | 'unclear';

export type ProcessingStatus = 
  | 'queued'
  | 'converting'
  | 'transcribing'
  | 'extracting'
  | 'saving'
  | 'completed'
  | 'failed';

export interface CallRecord {
  id: string;
  created_at: string;
  updated_at: string;
  telecaller_name: string;
  company_name: string;
  submitted_phone_number: string;
  submitted_category?: string | null;
  submitted_notes?: string | null;
  
  audio_filename?: string | null;
  audio_path?: string | null;
  audio_duration: number;
  
  processing_status: ProcessingStatus;
  processing_stage?: string | null;
  error_message?: string | null;
  processing_time_seconds: number;
  
  transcript?: string | null;
  extracted_json?: Record<string, any> | null;
  
  contact_person_name?: string | null;
  phone_number?: string | null;
  alternate_phone_number?: string | null;
  email?: string | null;
  business_category?: string | null;
  call_status: CallStatus;
  customer_intent?: string | null;
  products_or_services_discussed: string[];
  order_details?: string | null;
  quantity?: string | null;
  budget_or_price?: string | null;
  follow_up_date?: string | null;
  follow_up_time?: string | null;
  customer_requirements?: string | null;
  objections: string[];
  summary?: string | null;
  confidence_score: number;
}

export interface CallListResponse {
  total: number;
  page: number;
  page_size: number;
  items: CallRecord[];
}

export interface DashboardStats {
  total_calls: number;
  calls_today: number;
  interested_leads: number;
  orders_confirmed: number;
  did_not_pick: number;
  follow_ups_required: number;
  processing_failures: number;
  success_rate: number;
  status_distribution: Record<string, number>;
  calls_per_telecaller: Record<string, number>;
  calls_per_category: Record<string, number>;
  calls_per_day: Record<string, number>;
  recent_calls: CallRecord[];
}

export interface CallStatusResponse {
  call_id: string;
  processing_status: ProcessingStatus;
  processing_stage?: string | null;
  error_message?: string | null;
  processing_time_seconds: number;
  updated_at: string;
}

export interface CallFilterParams {
  page?: number;
  page_size?: number;
  telecaller?: string;
  status?: string;
  category?: string;
  processing_status?: string;
  search?: string;
  start_date?: string;
  end_date?: string;
}
