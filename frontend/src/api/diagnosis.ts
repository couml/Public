import apiClient from './client';
import type { DiagnosisSession, DiagnosisMessage } from '@/types/diagnosis';
import type { PaginatedResponse } from '@/types/api';

export const diagnosisApi = {
  createSession: (data?: { printer_id?: string; title?: string }) =>
    apiClient.post<DiagnosisSession>('/diagnosis/sessions', data || {}).then((r) => r.data),

  listSessions: (params?: { page?: number; page_size?: number }) =>
    apiClient.get<PaginatedResponse<DiagnosisSession>>('/diagnosis/sessions', { params }).then((r) => r.data),

  getSession: (id: string) =>
    apiClient.get<DiagnosisSession>(`/diagnosis/sessions/${id}`).then((r) => r.data),

  sendMessage: (sessionId: string, message: string) =>
    apiClient.post<DiagnosisMessage>(`/diagnosis/sessions/${sessionId}/messages`, { message }).then((r) => r.data),

  getReportUrl: (sessionId: string) =>
    `/api/v1/diagnosis/sessions/${sessionId}/report`,

  getErrorCodes: () =>
    apiClient.get('/diagnosis/error-codes').then((r) => r.data),

  predict: (printerId: string) =>
    apiClient.post('/diagnosis/predict', { printer_id: printerId }).then((r) => r.data),
};
