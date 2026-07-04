// ==================== Printer Brands ====================
export const PRINTER_BRANDS: string[] = [
  'HP',
  'Canon',
  'Epson',
  'Brother',
  'Samsung',
  'Xerox',
  'Kyocera',
  'Ricoh',
  'Konica Minolta',
  'Lexmark',
  'Dell',
  'Pantum',
  'Lenovo',
];

// ==================== Paper Sizes ====================
export const PAPER_SIZES: { label: string; value: string }[] = [
  { label: 'A4 (210×297mm)', value: 'A4' },
  { label: 'A3 (297×420mm)', value: 'A3' },
  { label: 'A5 (148×210mm)', value: 'A5' },
  { label: 'B5 (176×250mm)', value: 'B5' },
  { label: 'Letter (216×279mm)', value: 'Letter' },
  { label: 'Legal (216×356mm)', value: 'Legal' },
];

// ==================== Print Color Modes ====================
export const PRINT_COLOR_MODES: { label: string; value: string }[] = [
  { label: '彩色', value: 'color' },
  { label: '黑白', value: 'mono' },
  { label: '自动', value: 'auto' },
];

// ==================== Page Orientations ====================
export const PAGE_ORIENTATIONS: { label: string; value: string }[] = [
  { label: '纵向', value: 'portrait' },
  { label: '横向', value: 'landscape' },
];

// ==================== Target Formats (for diagnosis) ====================
export const TARGET_FORMATS: { label: string; value: string }[] = [
  { label: 'Word (.docx)', value: 'docx' },
  { label: 'PDF (.pdf)', value: 'pdf' },
  { label: '图片 (.png)', value: 'png' },
  { label: '图片 (.jpg)', value: 'jpg' },
];

// ==================== N-Up Options ====================
export const N_UP_OPTIONS: { label: string; value: number }[] = [
  { label: '1页/张', value: 1 },
  { label: '2页/张', value: 2 },
  { label: '4页/张', value: 4 },
  { label: '6页/张', value: 6 },
  { label: '9页/张', value: 9 },
  { label: '16页/张', value: 16 },
];

// ==================== Device Status Map ====================
export const DEVICE_STATUS_MAP: Record<string, { color: string; text: string }> = {
  online: { color: '#52c41a', text: '在线' },
  offline: { color: '#d9d9d9', text: '离线' },
  printing: { color: '#1677ff', text: '打印中' },
  error: { color: '#ff4d4f', text: '故障' },
  paper_out: { color: '#faad14', text: '缺纸' },
  toner_low: { color: '#faad14', text: '墨粉不足' },
  sleep: { color: '#d9d9d9', text: '休眠' },
  busy: { color: '#1677ff', text: '忙碌' },
};

// ==================== Alert Severity Map ====================
export const ALERT_SEVERITY_MAP: Record<string, { color: string; text: string }> = {
  critical: { color: '#ff4d4f', text: '严重' },
  warning: { color: '#faad14', text: '警告' },
  info: { color: '#1677ff', text: '信息' },
  success: { color: '#52c41a', text: '正常' },
};
