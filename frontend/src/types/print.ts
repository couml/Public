export type PrintJobStatus = 'queued' | 'converting' | 'waiting' | 'printing' | 'completed' | 'failed' | 'cancelled';
export type FileRecordStatus = 'uploading' | 'uploaded' | 'converting' | 'converted' | 'failed';

export interface FileRecord {
  id: string;
  user_id: string;
  original_filename: string;
  file_size: number;
  mime_type: string | null;
  file_md5: string;
  storage_path: string;
  status: FileRecordStatus;
  converted_format: string | null;
  converted_path: string | null;
  page_count: number | null;
  is_temporary: boolean;
  expires_at: string | null;
  created_at: string;
}

export interface PrintJob {
  id: string;
  user_id: string;
  printer_id: string;
  file_id: string;
  job_name: string | null;
  status: PrintJobStatus;
  copies: number;
  color_mode: 'color' | 'grayscale';
  duplex: boolean;
  paper_size: string;
  page_range: string | null;
  n_up: string;
  orientation: 'portrait' | 'landscape';
  pin_code: string | null;
  total_pages: number | null;
  pages_printed: number;
  error_message: string | null;
  queued_at: string;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
}

export interface PrintJobCreate {
  printer_id: string;
  file_id: string;
  copies?: number;
  color_mode?: 'color' | 'grayscale';
  duplex?: boolean;
  paper_size?: string;
  page_range?: string;
  n_up?: string;
  orientation?: 'portrait' | 'landscape';
  pin_code?: string;
}

export interface PrintJobStats {
  total_jobs: number;
  completed_today: number;
  failed_today: number;
  total_pages_today: number;
  avg_wait_seconds: number;
}

export interface UploadTask {
  file: File;
  fileId?: string;
  uploadId?: string;
  progress: number;
  status: 'pending' | 'hashing' | 'uploading' | 'completed' | 'failed';
  error?: string;
  totalChunks: number;
  uploadedChunks: number;
}
