import { useAuthStore } from '@/store/authStore';

export function usePermission() {
  const user = useAuthStore((s) => s.user);

  const isAdmin = user?.role === 'admin';
  const isITStaff = user?.role === 'it_staff';
  const canManage = isAdmin || isITStaff;

  const hasRole = (...roles: string[]) => {
    if (!user) return false;
    return roles.includes(user.role);
  };

  return { isAdmin, isITStaff, canManage, hasRole, role: user?.role };
}
