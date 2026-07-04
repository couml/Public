import apiClient from './client';
import type { FileRecord } from '@/types/print';
import type { PaginatedResponse } from '@/types/api';

export const filesApi = {
  initUpload: (data: { filename: string; file_size: number; file_md5: string; total_chunks: number; mime_type?: string }) =>
    apiClient.post<{ upload_id: string; file_id: string }>('/files/upload/init', data).then((r) => r.data),

  uploadChunk: (uploadId: string, chunkIndex: number, chunk: Blob) => {
    const formData = new FormData();
    formData.append('chunk', chunk);
    return apiClient.put(`/files/upload/chunk`, formData, {
      params: { upload_id: uploadId, chunk_index: chunkIndex },
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  completeUpload: (data: { upload_id: string; file_id: string }) =>
    apiClient.post<FileRecord>('/files/upload/complete', data).then((r) => r.data),

  list: (params?: { status?: string; page?: number; page_size?: number }) =>
    apiClient.get<PaginatedResponse<FileRecord>>('/files', { params }).then((r) => r.data),

  getById: (id: string) =>
    apiClient.get<FileRecord>(`/files/${id}`).then((r) => r.data),

  getPreviewUrl: (id: string) =>
    `/api/v1/files/${id}/preview`,

  getDownloadUrl: (id: string) =>
    `/api/v1/files/${id}/download`,

  deleteFile: (id: string) =>
    apiClient.delete(`/files/${id}`).then((r) => r.data),

  convert: (fileId: string, targetFormat: string) =>
    apiClient.post<FileRecord>('/files/convert', { file_id: fileId, target_format: targetFormat }).then((r) => r.data),

  getStaging: () =>
    apiClient.get<FileRecord[]>('/files/staging').then((r) => r.data),
};
