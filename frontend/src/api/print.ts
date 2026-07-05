import apiClient from './client';
import type { PrintJob, PrintJobCreate } from '@/types/print';
import type { PaginatedResponse } from '@/types/api';

export const printApi = {
  submitJob: (data: PrintJobCreate) =>
    apiClient.post<PrintJob>('/print/jobs', data).then((r) => r.data),

  list: (params?: { status?: string; page?: number; page_size?: number }) =>
    apiClient.get<PaginatedResponse<PrintJob>>('/print/jobs', { params }).then((r) => r.data),

  getById: (id: string) =>
    apiClient.get<PrintJob>(`/print/jobs/${id}`).then((r) => r.data),

  cancel: (id: string) =>
    apiClient.post(`/print/jobs/${id}/cancel`).then((r) => r.data),

  getStats: () =>
    apiClient.get('/print/jobs/stats').then((r) => r.data),
};
