export interface ScanDocument {
  id: string;
  user_id: string | null;
  printer_id: string | null;
  filename: string;
  file_size: number;
  mime_type: string | null;
  storage_path: string;
  page_count: number | null;
  ocr_text: string | null;
  ocr_status: 'pending' | 'processing' | 'completed' | 'failed';
  tags: string[];
  category: string | null;
  is_shared: boolean;
  share_token: string | null;
  share_expires_at: string | null;
  created_at: string;
}
