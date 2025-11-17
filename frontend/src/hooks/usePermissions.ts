'use client';

/**
 * 権限判定用カスタムフック
 * 
 * AuthContextのユーザー情報を元に、フロント側の表示・導線制御に使う
 * 権限判定を提供します。
 */

import { useAuth } from '@/contexts/AuthContext';
import { PermissionService } from '@/lib/permissions';
import type { User } from '@/lib/api';

type UserRole = User['role'];

export function usePermissions() {
  const { user } = useAuth();
  const role = user?.role as UserRole | undefined;

  return {
    canViewUsers: PermissionService.canViewUsers(role),
    canManageUsers: PermissionService.canManageUsers(role),
    canDeleteUser: (targetRole?: UserRole) => PermissionService.canDeleteUser(role, targetRole),
  };
}


