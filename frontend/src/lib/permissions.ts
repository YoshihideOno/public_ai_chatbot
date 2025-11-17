/**
 * 権限判定ヘルパー
 * 
 * このモジュールはフロントエンドでの権限制御を一元化し、役割に応じた画面操作可否を判定します。
 * RBACの方針に沿って、各機能ごとの許可・不許可を明示的に定義します。
 */

import { User } from '@/lib/api';

type UserRole = User['role'];

/**
 * 権限サービス
 * 
 * ロールごとの優先度テーブルを定義し、UI側の細かな権限チェックを提供します。
 */
export class PermissionService {
  /**
   * ロール優先度（数値が小さいほど権限が強い）
   */
  private static readonly ROLE_PRIORITY: Record<UserRole, number> = {
    PLATFORM_ADMIN: 0,
    TENANT_ADMIN: 1,
    OPERATOR: 2,
    AUDITOR: 3,
  };

  /**
   * ユーザー閲覧可否
   * 
   * 引数:
   *   role: 現在のユーザーロール
   * 戻り値:
   *   boolean: ユーザー一覧の閲覧可否
   */
  static canViewUsers(role?: UserRole): boolean {
    return PermissionService.isRoleAtLeast(role, ['PLATFORM_ADMIN', 'TENANT_ADMIN', 'OPERATOR']);
  }

  /**
   * ユーザー管理可否（追加・更新）
   * 
   * 引数:
   *   role: 現在のユーザーロール
   * 戻り値:
   *   boolean: 管理系操作の可否
   */
  static canManageUsers(role?: UserRole): boolean {
    return PermissionService.isRoleAtLeast(role, ['PLATFORM_ADMIN', 'TENANT_ADMIN']);
  }

  /**
   * ユーザー削除可否（ターゲットとのロール比較込み）
   * 
   * 引数:
   *   role: 実行ユーザーのロール
   *   targetRole: 削除対象ユーザーのロール
   * 戻り値:
   *   boolean: 削除可否
   */
  static canDeleteUser(role?: UserRole, targetRole?: UserRole): boolean {
    if (!PermissionService.canManageUsers(role)) {
      return false;
    }
    if (!role || !targetRole) {
      return false;
    }
    return PermissionService.ROLE_PRIORITY[role] < PermissionService.ROLE_PRIORITY[targetRole];
  }

  /**
   * 指定ロールが許可対象に含まれているかを判定
   */
  private static isRoleAtLeast(role: UserRole | undefined, allowed: UserRole[]): boolean {
    if (!role) {
      return false;
    }
    return allowed.includes(role);
  }
}
