import dayjs from 'dayjs';
import 'dayjs/locale/zh-cn';

dayjs.locale('zh-cn');

/**
 * Format file size in bytes to a human-readable string.
 * e.g. 1536000 -> "1.5 MB"
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B';

  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  const k = 1024;
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  const value = bytes / Math.pow(k, i);
  const formatted = value % 1 === 0 ? value.toFixed(0) : value.toFixed(1);

  return `${formatted} ${units[i]}`;
}

/**
 * Format a date to standard string: "2024-01-15 14:30"
 */
export function formatDate(date: string | Date): string {
  return dayjs(date).format('YYYY-MM-DD HH:mm');
}

/**
 * Format a date to relative time: "3分钟前", "2小时前"
 */
export function formatRelativeTime(date: string | Date): string {
  const now = dayjs();
  const target = dayjs(date);
  const diffSeconds = now.diff(target, 'second');

  if (diffSeconds < 60) return '刚刚';
  if (diffSeconds < 3600) return `${Math.floor(diffSeconds / 60)}分钟前`;
  if (diffSeconds < 86400) return `${Math.floor(diffSeconds / 3600)}小时前`;
  if (diffSeconds < 2592000) return `${Math.floor(diffSeconds / 86400)}天前`;
  if (diffSeconds < 31536000) return `${Math.floor(diffSeconds / 2592000)}个月前`;

  return formatDate(date);
}

/**
 * Format duration in seconds to readable string: "2分30秒"
 */
export function formatDuration(seconds: number): string {
  if (seconds < 60) return `${seconds}秒`;

  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;

  if (remainingSeconds === 0) return `${minutes}分钟`;

  return `${minutes}分${remainingSeconds}秒`;
}

/**
 * Format a number with thousands separators: "1,234"
 */
export function formatNumber(n: number): string {
  return n.toLocaleString('en-US');
}
