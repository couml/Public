import apiClient from './client';
import type { Printer } from '@/types/device';
import type { DriverPackage } from '@/types/driver';
import type { User } from '@/types/user';
import type { PaginatedResponse } from '@/types/api';

export const adminApi = {
  // Printers
  listPrinters: (params?: { page?: number; page_size?: number }) =>
    apiClient.get<PaginatedResponse<Printer>>('/admin/printers', { params }).then((r) => r.data),

  createPrinter: (data: Partial<Printer>) =>
    apiClient.post<Printer>('/admin/printers', data).then((r) => r.data),

  updatePrinter: (id: string, data: Partial<Printer>) =>
    apiClient.put<Printer>(`/admin/printers/${id}`, data).then((r) => r.data),

  deletePrinter: (id: string) =>
    apiClient.delete(`/admin/printers/${id}`).then((r) => r.data),

  // Drivers
  listDrivers: (params?: { page?: number; page_size?: number }) =>
    apiClient.get<PaginatedResponse<DriverPackage>>('/admin/drivers', { params }).then((r) => r.data),

  createDriver: (data: FormData) =>
    apiClient.post<DriverPackage>('/admin/drivers', data, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).then((r) => r.data),

  updateDriver: (id: string, data: Partial<DriverPackage>) =>
    apiClient.put<DriverPackage>(`/admin/drivers/${id}`, data).then((r) => r.data),

  deleteDriver: (id: string) =>
    apiClient.delete(`/admin/drivers/${id}`).then((r) => r.data),

  // Users
  listUsers: (params?: { role?: string; is_active?: boolean; page?: number; page_size?: number }) =>
    apiClient.get<PaginatedResponse<User>>('/admin/users', { params }).then((r) => r.data),

  updateUser: (id: string, data: { full_name?: string; department?: string; role?: string; is_active?: boolean }) =>
    apiClient.put<User>(`/admin/users/${id}`, data).then((r) => r.data),

  deleteUser: (id: string) =>
    apiClient.delete(`/admin/users/${id}`).then((r) => r.data),

  // Logs
  getLogs: (params?: { action?: string; user_id?: string; page?: number; page_size?: number }) =>
    apiClient.get('/admin/logs', { params }).then((r) => r.data),

  getStats: () =>
    apiClient.get('/admin/stats').then((r) => r.data),
};
