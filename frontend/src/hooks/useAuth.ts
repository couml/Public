import { useEffect } from 'react';
import { useAuthStore } from '@/store/authStore';

export function useAuth() {
  const { user, isAuthenticated, isLoading, login, register, logout, fetchMe } = useAuthStore();

  useEffect(() => {
    if (isAuthenticated && !user && !isLoading) {
      fetchMe();
    }
  }, [isAuthenticated, user, isLoading, fetchMe]);

  return { user, isAuthenticated, isLoading, login, register, logout, fetchMe };
}
