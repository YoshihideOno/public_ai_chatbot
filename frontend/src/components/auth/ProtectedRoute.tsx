/**
 * 認証・認可によるルート保護コンポーネント
 * 
 * このファイルは、ユーザーの認証状態とロールに基づいてページへのアクセスを制御する
 * コンポーネントを提供します。認証されていないユーザーはログインページにリダイレクトし、
 * 必要なロールを持たないユーザーにはアクセス拒否メッセージを表示します。
 * 
 * 主な機能:
 * - 認証状態のチェック
 * - ロールベースのアクセス制御
 * - 未認証ユーザーのログインページへのリダイレクト
 * - 権限不足時のエラーメッセージ表示
 * - 管理者・テナント管理者・オペレーター用の専用ルートコンポーネント
 */

'use client';

import React from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

/**
 * ProtectedRouteコンポーネントのプロパティ型定義
 * @param children - 保護されたコンテンツ
 * @param requiredRole - アクセスに必要なロール（オプション）
 * @param fallback - 認証失敗時に表示するフォールバックコンテンツ（オプション）
 */
interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredRole?: 'PLATFORM_ADMIN' | 'TENANT_ADMIN' | 'OPERATOR' | 'AUDITOR';
  fallback?: React.ReactNode;
}

/**
 * 認証・認可によるルート保護コンポーネント
 * ユーザーの認証状態とロールをチェックして、適切なコンテンツを表示します
 * 
 * @param children - 保護されたコンテンツ
 * @param requiredRole - アクセスに必要なロール（オプション）
 * @param fallback - 認証失敗時に表示するフォールバックコンテンツ（オプション）
 * @returns 認証・認可チェック後のコンテンツまたはエラーメッセージ
 */
export function ProtectedRoute({ 
  children, 
  requiredRole, 
  fallback 
}: ProtectedRouteProps) {
  const { user, isLoading, isAuthenticated } = useAuth();
  const router = useRouter();

  // 認証状態をチェックして、未認証の場合はログインページにリダイレクト
  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [isLoading, isAuthenticated, router]);

  // ローディング中の場合はスピナーを表示
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  // 認証されていない場合はフォールバックコンテンツを表示
  if (!isAuthenticated) {
    return fallback || null;
  }

  // 必要なロールを持たない場合はアクセス拒否メッセージを表示
  if (requiredRole && user?.role !== requiredRole) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-red-600 mb-4">アクセス拒否</h1>
          <p className="text-muted-foreground">
            このページにアクセスする権限がありません。
          </p>
        </div>
      </div>
    );
  }

  // 認証・認可チェックを通過した場合は子コンテンツを表示
  return <>{children}</>;
}

/**
 * プラットフォーム管理者専用ルートコンポーネント
 * PLATFORM_ADMINロールを持つユーザーのみアクセス可能
 * 
 * @param children - 保護されたコンテンツ
 * @returns プラットフォーム管理者のみがアクセス可能なコンテンツ
 */
export function AdminRoute({ children }: { children: React.ReactNode }) {
  return (
    <ProtectedRoute requiredRole="PLATFORM_ADMIN">
      {children}
    </ProtectedRoute>
  );
}

/**
 * テナント管理者専用ルートコンポーネント
 * TENANT_ADMINロールを持つユーザーのみアクセス可能
 * 
 * @param children - 保護されたコンテンツ
 * @returns テナント管理者のみがアクセス可能なコンテンツ
 */
export function TenantAdminRoute({ children }: { children: React.ReactNode }) {
  return (
    <ProtectedRoute requiredRole="TENANT_ADMIN">
      {children}
    </ProtectedRoute>
  );
}

/**
 * オペレーター専用ルートコンポーネント
 * OPERATORロールを持つユーザーのみアクセス可能
 * 
 * @param children - 保護されたコンテンツ
 * @returns オペレーターのみがアクセス可能なコンテンツ
 */
export function OperatorRoute({ children }: { children: React.ReactNode }) {
  return (
    <ProtectedRoute requiredRole="OPERATOR">
      {children}
    </ProtectedRoute>
  );
}
