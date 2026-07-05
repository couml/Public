import apiClient from './client';
import type { ScanDocument } from '@/types/document';
import type { PaginatedResponse } from '@/types/api';

export const documentsApi = {
  list: (params?: { category?: string; tag?: string; page?: number; page_size?: number }) =>
    apiClient.get<PaginatedResponse<ScanDocument>>('/documents', { params }).then((r) => r.data),

  getById: (id: string) =>
    apiClient.get<ScanDocument>(`/documents/${id}`).then((r) => r.data),

  getDownloadUrl: (id: string) =>
    `/api/v1/documents/${id}/download`,

  triggerOcr: (id: string) =>
    apiClient.post(`/documents/${id}/ocr`).then((r) => r.data),

  share: (id: string, expiresHours?: number) =>
    apiClient.post(`/documents/${id}/share`, { expires_hours: expiresHours || 24 }).then((r) => r.data),

  updateTags: (id: string, tags: string[], category?: string) =>
    apiClient.put(`/documents/${id}/tags`, { tags, category }).then((r) => r.data),

  getSharedDocument: (token: string) =>
    apiClient.get<ScanDocument>(`/documents/shared/${token}`).then((r) => r.data),
};
