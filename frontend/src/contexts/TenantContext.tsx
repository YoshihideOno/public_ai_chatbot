/**
 * テナントコンテキスト
 *
 * このファイルは現在ログイン中ユーザーのテナント情報を共有するための
 * React Context を定義します。ダッシュボードやテナント設定画面など、
 * 複数のページ／コンポーネント間でテナント情報を一元管理します。
 */

'use client';

import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  ReactNode,
} from 'react';
import { Tenant, apiClient } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import { logger } from '@/utils/logger';

/**
 * テナントコンテキストの型定義
 *
 * 属性:
 *   tenant: 現在のテナント情報（未所属の場合はnull）
 *   isLoading: テナント情報取得中かどうか
 *   error: 直近の読み込みエラー（なければnull）
 *   reloadTenant: テナント情報を再取得するための関数
 */
interface TenantContextType {
  tenant: Tenant | null;
  isLoading: boolean;
  error: string | null;
  reloadTenant: () => Promise<void>;
}

const TenantContext = createContext<TenantContextType | undefined>(undefined);

interface TenantProviderProps {
  children: ReactNode;
}

/**
 * テナントプロバイダーコンポーネント
 *
 * 認証済みユーザーのテナント情報を取得し、子コンポーネントに提供します。
 * AuthContext と連携し、user.tenant_id が変化した際に自動的に再取得します。
 */
export function TenantProvider({ children }: TenantProviderProps) {
  const { user } = useAuth();
  const tenantId = user?.tenant_id || null;

  const [tenant, setTenant] = useState<Tenant | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * テナント情報を再取得する
   *
   * 引数:
   *   なし（内部で現在のユーザーの tenant_id を使用）
   *
   * 戻り値:
   *   Promise<void>
   */
  const reloadTenant = useCallback(async () => {
    if (!tenantId) {
      // テナント未所属の場合は状態をクリア
      setTenant(null);
      setError(null);
      return;
    }

    try {
      setIsLoading(true);
      setError(null);

      const t = await apiClient.getTenant(tenantId);
      setTenant(t);
    } catch (e: unknown) {
      logger.error('テナント情報の取得に失敗しました', e);
      const message =
        e instanceof Error ? e.message : 'テナント情報の取得に失敗しました';
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }, [tenantId]);

  // user.tenant_id が変化したら自動的にテナント情報を再取得
  useEffect(() => {
    // 未ログインやテナント未所属の場合は何もしない
    if (!tenantId) {
      setTenant(null);
      setError(null);
      setIsLoading(false);
      return;
    }

    void reloadTenant();
  }, [tenantId, reloadTenant]);

  const value: TenantContextType = {
    tenant,
    isLoading,
    error,
    reloadTenant,
  };

  return <TenantContext.Provider value={value}>{children}</TenantContext.Provider>;
}

/**
 * テナントコンテキストを利用するためのカスタムフック
 *
 * 戻り値:
 *   TenantContextType: テナント情報と操作関数
 *
 * 例外:
 *   Error: TenantProvider の外側で呼び出された場合
 */
export function useTenant(): TenantContextType {
  const context = useContext(TenantContext);
  if (context === undefined) {
    throw new Error('useTenant は TenantProvider 内でのみ使用できます');
  }
  return context;
}


