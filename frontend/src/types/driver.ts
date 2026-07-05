export interface DriverPackage {
  id: string;
  brand: string;
  model: string;
  os_platform: 'windows' | 'macos' | 'linux';
  version: string;
  file_size: number;
  storage_path: string;
  release_date: string;
  changelog: string | null;
  is_active: boolean;
  download_count: number;
  created_at: string;
  updated_at: string;
}

export interface HP136aPage {
  drivers: DriverPackage[];
  manuals: { title: string; url: string; size: string }[];
  faqs: { question: string; answer: string }[];
  install_guides: Record<string, string>;
}
