import apiClient from './client';
import type { Printer, PrinterStatusLog, PrinterAlert, PrinterStats } from '@/types/device';
import type { PaginatedResponse } from '@/types/api';

export const devicesApi = {
  list: (params?: { brand?: string; status?: string; search?: string; page?: number; page_size?: number }) =>
    apiClient.get<PaginatedResponse<Printer>>('/devices', { params }).then((r) => r.data),

  getById: (id: string) =>
    apiClient.get<Printer>(`/devices/${id}`).then((r) => r.data),

  getLogs: (id: string, params?: { hours?: number; limit?: number }) =>
    apiClient.get<PrinterStatusLog[]>(`/devices/${id}/logs`, { params }).then((r) => r.data),

  getAlerts: (id: string, params?: { resolved?: boolean }) =>
    apiClient.get<PrinterAlert[]>(`/devices/${id}/alerts`, { params }).then((r) => r.data),

  resolveAlert: (deviceId: string, alertId: string) =>
    apiClient.post(`/devices/${deviceId}/alerts/${alertId}/resolve`).then((r) => r.data),

  getStats: (id: string) =>
    apiClient.get<PrinterStats>(`/devices/${id}/stats`).then((r) => r.data),

  getQueue: (id: string) =>
    apiClient.get(`/devices/${id}/queue`).then((r) => r.data),
};
