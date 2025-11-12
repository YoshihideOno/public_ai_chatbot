/**
 * アカウント設定ページ
 * 
 * ログインユーザーのプロフィール情報やパスワード変更など、
 * アカウントに関する設定を行うためのページコンポーネント。
 * 現時点では基本情報の表示のみを提供し、今後機能拡張予定。
 */

'use client';

import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { useAuth } from '@/contexts/AuthContext';
import TenantApiKeys from '@/components/settings/TenantApiKeys';
import TenantLlmModels from '@/components/settings/TenantLlmModels';
import TenantChunkSettings from '@/components/settings/TenantChunkSettings';
import TenantWebhookSettings from '@/components/settings/TenantWebhookSettings';
import { apiClient, Tenant } from '@/lib/api';

export default function SettingsPage() {
  const { user } = useAuth();
  const isTenantAdmin = user?.role === 'TENANT_ADMIN' || user?.role === 'PLATFORM_ADMIN';
  const [tenant, setTenant] = useState<Tenant | null>(null);
  const [loadingTenant, setLoadingTenant] = useState(false);
  const [tenantError, setTenantError] = useState<string | null>(null);

  useEffect(() => {
    const loadTenant = async () => {
      if (!user?.tenant_id) return;
      try {
        setLoadingTenant(true);
        setTenantError(null);
        const t = await apiClient.getTenant(user.tenant_id);
        setTenant(t);
      } catch {
        setTenantError('テナント情報の取得に失敗しました');
      } finally {
        setLoadingTenant(false);
      }
    };
    loadTenant();
  }, [user?.tenant_id]);

  return (
    <ProtectedRoute>
      <div className="container mx-auto py-8 space-y-6">
        <div>
          <h1 className="text-3xl font-bold">アカウント設定</h1>
          <p className="text-muted-foreground mt-2">プロフィール情報の確認と管理を行います。</p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>基本情報</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <div className="text-sm text-muted-foreground">ユーザー名</div>
                <div className="text-base font-medium">{user?.username || '-'}</div>
              </div>
              <div>
                <div className="text-sm text-muted-foreground">メールアドレス</div>
                <div className="text-base font-medium">{user?.email || '-'}</div>
              </div>
              <div>
                <div className="text-sm text-muted-foreground">ロール</div>
                <div className="text-base font-medium">{user?.role || '-'}</div>
              </div>
              <div>
                <div className="text-sm text-muted-foreground">テナントID</div>
                <div className="text-base font-medium">{user?.tenant_id || '-'}</div>
              </div>
            </div>
          </CardContent>
        </Card>

        {isTenantAdmin && (
          <div className="space-y-6">
          <Card>
            <CardHeader>
                <CardTitle>テナント設定 - 概要</CardTitle>
            </CardHeader>
            <CardContent>
                  {!user?.tenant_id ? (
                    <p className="text-sm text-muted-foreground">テナント未所属のため概要情報は表示できません。</p>
                  ) : loadingTenant ? (
                    <p className="text-sm text-muted-foreground">読み込み中...</p>
                  ) : tenantError ? (
                    <p className="text-sm text-red-600">{tenantError}</p>
                  ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                      <div>
                        <div className="text-muted-foreground">テナント名</div>
                        <div className="font-medium">{tenant?.name || '-'}</div>
                      </div>
                      <div>
                        <div className="text-muted-foreground">ドメイン</div>
                        <div className="font-medium">{tenant?.domain || '-'}</div>
                      </div>
                      <div>
                        <div className="text-muted-foreground">プラン</div>
                        <div className="font-medium">{tenant?.plan || '-'}</div>
                      </div>
                      <div>
                        <div className="text-muted-foreground">ステータス</div>
                        <div className="font-medium">{tenant?.status || '-'}</div>
                      </div>
                      <div>
                        <div className="text-muted-foreground">ユーザー上限</div>
                        <div className="font-medium">{tenant?.settings?.max_users ?? '-'}</div>
                      </div>
                      <div>
                        <div className="text-muted-foreground">コンテンツ上限</div>
                        <div className="font-medium">{tenant?.settings?.max_contents ?? '-'}</div>
                      </div>
                      <div>
                        <div className="text-muted-foreground">ストレージ上限(MB)</div>
                        <div className="font-medium">{tenant?.settings?.max_storage_mb ?? '-'}</div>
                      </div>
                      <div>
                      <div className="text-muted-foreground">チャット用モデル / ベクトル埋め込みモデル</div>
                        <div className="font-medium">{tenant?.settings?.default_model || '-'} / {tenant?.settings?.embedding_model || '-'}</div>
                      </div>
                    </div>
                  )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>テナント設定 - コンテンツ処理完了通知</CardTitle>
              </CardHeader>
              <CardContent>
                <TenantWebhookSettings />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>テナント設定 - LLMモデル</CardTitle>
              </CardHeader>
              <CardContent>
                <TenantLlmModels />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>テナント設定 - APIキー</CardTitle>
              </CardHeader>
              <CardContent>
                  <TenantApiKeys />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>テナント設定 - テキスト分割</CardTitle>
              </CardHeader>
              <CardContent>
                <TenantChunkSettings />
            </CardContent>
          </Card>
          </div>
        )}
      </div>
    </ProtectedRoute>
  );
}


