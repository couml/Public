import apiClient from './client';
import type { DriverPackage } from '@/types/driver';
import type { PaginatedResponse } from '@/types/api';

export const driversApi = {
  list: (params?: { brand?: string; model?: string; os?: string; search?: string; page?: number; page_size?: number }) =>
    apiClient.get<PaginatedResponse<DriverPackage>>('/drivers', { params }).then((r) => r.data),

  getBrands: () =>
    apiClient.get<string[]>('/drivers/brands').then((r) => r.data),

  getModels: (brand: string) =>
    apiClient.get<string[]>(`/drivers/models`, { params: { brand } }).then((r) => r.data),

  getHP136a: () =>
    apiClient.get('/drivers/hp-136a').then((r) => r.data),

  getById: (id: string) =>
    apiClient.get<DriverPackage>(`/drivers/${id}`).then((r) => r.data),

  getDownloadUrl: (id: string) =>
    `/api/v1/drivers/${id}/download`,

  getVersions: (id: string) =>
    apiClient.get<DriverPackage[]>(`/drivers/${id}/versions`).then((r) => r.data),
};
