export type DeviceStatus = 'online' | 'offline' | 'busy' | 'error';
export type AlertType = 'paper_out' | 'paper_jam' | 'paper_low' | 'toner_low' | 'toner_empty' | 'offline' | 'service_required' | 'fuser_warning' | 'drum_low';
export type AlertSeverity = 'info' | 'warning' | 'critical';

export interface Printer {
  id: string;
  name: string;
  brand: string;
  model: string;
  serial_number: string | null;
  ip_address: string;
  mac_address: string | null;
  location: string | null;
  status: DeviceStatus;
  toner_level: number;
  toner_type: string | null;
  paper_level: number;
  total_pages_printed: number;
  firmware_version: string | null;
  supports_color: boolean;
  supports_duplex: boolean;
  max_paper_size: string;
  last_seen_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface PrinterStatusLog {
  id: string;
  printer_id: string;
  status: DeviceStatus;
  toner_level: number | null;
  paper_level: number | null;
  error_code: string | null;
  error_message: string | null;
  ip_address: string | null;
  response_time_ms: number | null;
  recorded_at: string;
}

export interface PrinterAlert {
  id: string;
  printer_id: string;
  alert_type: AlertType;
  severity: AlertSeverity;
  message: string;
  is_resolved: boolean;
  resolved_by: string | null;
  resolved_at: string | null;
  created_at: string;
}

export interface PrinterStats {
  total_pages: number;
  pages_today: number;
  pages_this_week: number;
  pages_this_month: number;
  total_errors: number;
  uptime_percentage: number;
}

export interface DeviceStatusUpdate {
  id: string;
  status: DeviceStatus;
  toner_level: number;
  paper_level: number;
  timestamp: string;
}
