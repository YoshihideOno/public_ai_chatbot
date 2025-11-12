"""
権限判定サービス

このファイルはシステム全体のRBAC（ロールベースアクセス制御）ロジックを一元管理します。
バックエンドが単一の真実の源（Source of Truth）となり、フロントエンドはこのルールに整合させます。

主な機能:
- ユーザー管理機能に関する閲覧/編集/削除の可否判定
- テナント境界・ロール組み合わせの基本判定支援
"""

from typing import Optional
from app.models.user import UserRole


class PermissionService:
    """権限判定を一元管理するサービスクラス

    取り扱う概念:
    - UserRole: ユーザーのロールに基づくRBAC

    継承: なし
    """

    @staticmethod
    def can_view_users(current_role: Optional[UserRole]) -> bool:
        """ユーザー管理の閲覧権限可否

        引数:
            current_role: 現在のユーザーロール
        戻り値:
            bool: 閲覧可能か
        """
        if current_role is None:
            return False
        return current_role in [UserRole.PLATFORM_ADMIN, UserRole.TENANT_ADMIN, UserRole.AUDITOR]

    @staticmethod
    def can_manage_users(current_role: Optional[UserRole]) -> bool:
        """ユーザー管理の編集権限可否

        引数:
            current_role: 現在のユーザーロール
        戻り値:
            bool: 編集可能か
        """
        if current_role is None:
            return False
        return current_role in [UserRole.PLATFORM_ADMIN, UserRole.TENANT_ADMIN]

    @staticmethod
    def can_delete_user(current_role: Optional[UserRole], target_role: Optional[UserRole]) -> bool:
        """ユーザー削除権限可否

        引数:
            current_role: 現在のユーザーロール
            target_role: 対象ユーザーのロール
        戻り値:
            bool: 削除可能か

        注意:
            - 管理者（PLATFORM_ADMIN/TENANT_ADMIN）の削除は不可
            - 現在の仕様ではオペレーター/監査者は削除不可
        """
        if current_role not in [UserRole.PLATFORM_ADMIN, UserRole.TENANT_ADMIN]:
            return False
        if target_role in [UserRole.PLATFORM_ADMIN, UserRole.TENANT_ADMIN]:
            return False
        return True


