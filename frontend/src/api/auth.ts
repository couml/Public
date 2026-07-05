import apiClient from './client';
import type { LoginRequest, RegisterRequest, TokenResponse, User } from '@/types/user';

export const authApi = {
  login: (data: LoginRequest) =>
    apiClient.post<TokenResponse>('/auth/login', data).then((r) => r.data),

  register: (data: RegisterRequest) =>
    apiClient.post<TokenResponse>('/auth/register', data).then((r) => r.data),

  refresh: (refreshToken: string) =>
    apiClient.post<TokenResponse>('/auth/refresh', { refresh_token: refreshToken }).then((r) => r.data),

  me: () =>
    apiClient.get<User>('/auth/me').then((r) => r.data),

  logout: () =>
    apiClient.post('/auth/logout').then((r) => r.data),
};
