'use client';

/**
 * 権限判定用カスタムフック
 * 
 * AuthContextのユーザー情報を元に、フロント側の表示・導線制御に使う
 * 権限判定を提供します。
 */

import { useAuth } from '@/contexts/AuthContext';
import { PermissionService } from '@/lib/permissions';

export function usePermissions() {
  const { user } = useAuth();
  const role = user?.role;

  return {
    canViewUsers: PermissionService.canViewUsers(role),
    canManageUsers: PermissionService.canManageUsers(role),
    canDeleteUser: (targetRole: string | undefined) => PermissionService.canDeleteUser(role, targetRole),
  };
}


