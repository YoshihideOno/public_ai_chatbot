'use client';

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { apiClient } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { 
  Users, 
  Building2, 
  BarChart3,
  TrendingUp,
  Clock,
  CheckCircle,
  AlertCircle,
  Activity,
  Database,
  Settings,
  XCircle,
  Download,
  Copy
} from 'lucide-react';
import Link from 'next/link';
import { format } from 'date-fns';
import { ja } from 'date-fns/locale';

/**
 * ダッシュボード画面
 * 
 * ログイン後のユーザーに表示されるメイン画面です。
 * ユーザーの権限に応じて異なる内容を表示し、
 * システムの統計情報や最近の活動を確認できます。
 * 
 * 表示内容:
 * - ユーザー情報
 * - 統計カード（質問数、アクティブユーザー、応答時間、評価率）
 * - システム状況（コンテンツ状況、テナント状況）
 * - 最近の活動履歴
 */
function DashboardContent() {
  const [stats, setStats] = useState({
    totalUsers: 0,
    totalTenants: 0,
    activeTenants: 0,
    totalContents: 0,
    totalQueries: 0,
    activeUsers: 0,
    indexedContents: 0,
    processingContents: 0,
    failedContents: 0,
  });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [systemConfigStatus, setSystemConfigStatus] = useState<{
    hasChatModel: boolean;
    hasEmbeddingModel: boolean;
    hasApiKey: boolean;
    chatModelName: string | null;
    embeddingModelName: string | null;
    apiKeyCount: number;
    hasIndexedContent: boolean;
    indexedCount: number;
    isReady: boolean;
    isLoading: boolean;
    error: string | null;
  }>({
    hasChatModel: false,
    hasEmbeddingModel: false,
    hasApiKey: false,
    chatModelName: null,
    embeddingModelName: null,
    apiKeyCount: 0,
    hasIndexedContent: false,
    indexedCount: 0,
    isReady: false,
    isLoading: false,
    error: null,
  });

  const { user } = useAuth();
  const widgetScriptUrl = process.env.NEXT_PUBLIC_WIDGET_CDN_URL || 'https://cdn.rag-chatbot.com/widget.js';
  const [activities, setActivities] = useState<{
    id: string;
    action: string;
    entity_type?: string;
    message?: string;
    created_at: string;
  }[]>([]);
  const [tenant, setTenant] = useState<{ id: string; api_key: string } | null>(null);

  // APIベースURLを計算（クライアントサイド）
  const apiBaseUrl = useMemo(() => {
    if (typeof window !== 'undefined') {
      // 環境変数から取得（ビルド時に注入される）
      if (process.env.NEXT_PUBLIC_API_URL) {
        return process.env.NEXT_PUBLIC_API_URL;
      }
      // 開発環境ではローカルのAPIサーバーを参照
      if (window.location.origin === 'http://localhost:3000') {
        return 'http://localhost:8000/api/v1';
      }
      // 本番環境では、現在のオリジンからAPI URLを構築
      // APIが別ドメインにある場合は環境変数で設定する必要がある
      return `${window.location.origin}/api/v1`;
    }
    // サーバーサイドでは環境変数から取得、なければ相対パス
    return process.env.NEXT_PUBLIC_API_URL || '/api/v1';
  }, []);

  /**
   * 埋め込みコード情報を取得
   * 
   * テナントに所属する全ユーザーが埋め込みコードを参照できるようにするため、
   * 埋め込みスニペット情報を取得します。
   */
  const fetchTenantForEmbed = useCallback(async () => {
    if (!user?.tenant_id) {
      console.log('fetchTenantForEmbed: user.tenant_id is not set');
      return;
    }

    try {
      console.log('Fetching embed snippet for tenant:', user.tenant_id);
      const embedData = await apiClient.getEmbedSnippet(user.tenant_id);
      console.log('Embed snippet data received:', embedData);
      if (embedData) {
        setTenant({
          id: embedData.tenant_id,
          api_key: embedData.api_key || ''
        });
      }
    } catch (err) {
      console.error('Failed to fetch embed snippet:', err);
      if (err && typeof err === 'object') {
        if ('response' in err) {
          const axiosError = err as { response?: { status?: number; data?: unknown }; request?: unknown; message?: string };
          console.error('Error status:', axiosError.response?.status);
          console.error('Error data:', axiosError.response?.data);
          console.error('Error message:', axiosError.message);
        } else if ('message' in err) {
          const error = err as { message?: string; code?: string };
          console.error('Network error:', error.message);
          console.error('Error code:', error.code);
        }
      }
      // エラーが発生してもダッシュボード表示は続行
    }
  }, [user?.tenant_id]);

  const fetchDashboardStats = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      // ダッシュボード統計を取得
      const dashboardStats = await apiClient.getDashboardStats('month');
      const storageStats = dashboardStats.storage_stats;
      
      // プラットフォーム管理者の場合、テナント状況の実データを取得
      let totalTenants = 0;
      let activeTenants = 0;
      let totalUsers = 0;
      
      if (user?.role === 'PLATFORM_ADMIN') {
        try {
          // テナント一覧を取得（最大1000件）
          const tenants = await apiClient.getTenants(0, 1000);
          totalTenants = tenants.length;
          activeTenants = tenants.filter(t => t.status === 'ACTIVE').length;
          
          // ユーザー一覧を取得（最大1000件、削除済みは除外される）
          const users = await apiClient.getUsers(0, 1000);
          totalUsers = users.length;
        } catch (err) {
          console.error('Failed to fetch tenant/user stats:', err);
          // エラーが発生してもダッシュボード表示は続行
        }
      }
      
      setStats({
        totalUsers: totalUsers || (dashboardStats.usage_stats?.total_queries || 0),
        totalTenants: totalTenants || (dashboardStats.usage_stats?.unique_users || 0),
        activeTenants: activeTenants,
        totalContents: storageStats?.total_files || 0,
        totalQueries: dashboardStats.usage_stats?.total_queries || 0,
        activeUsers: dashboardStats.usage_stats?.unique_users || 0,
        indexedContents: storageStats?.indexed_files ?? storageStats?.total_files ?? 0,
        processingContents: storageStats?.processing_files ?? 0,
        failedContents: storageStats?.failed_files ?? 0,
      });
    } catch (err: unknown) {
      console.error('Failed to fetch dashboard stats:', err);
      setError('統計データの取得に失敗しました');
    } finally {
      setIsLoading(false);
    }
  }, [user?.role]);

  /**
   * システム設定状況を取得
   * 
   * チャット用モデル、ベクトル埋め込みモデル、APIキーの設定状況を確認し、
   * システムが使用可能かどうかを判定します。
   */
  const fetchSystemConfigStatus = useCallback(async () => {
    if (!user?.tenant_id) {
      setSystemConfigStatus({
        hasChatModel: false,
        hasEmbeddingModel: false,
        hasApiKey: false,
        chatModelName: null,
        embeddingModelName: null,
        apiKeyCount: 0,
        hasIndexedContent: false,
        indexedCount: 0,
        isReady: false,
        isLoading: false,
        error: null,
      });
      return;
    }

    try {
      setSystemConfigStatus(prev => ({ ...prev, isLoading: true, error: null }));

      // テナント情報 / APIキー / コンテンツ統計を並行取得
      const [tenant, apiKeys, contentStats] = await Promise.all([
        apiClient.getTenant(user.tenant_id),
        apiClient.getApiKeys().catch(() => ({ api_keys: [], total_count: 0 })),
        apiClient.getContentStatsSummary().catch(() => ({ total_files: 0, status_counts: {}, total_chunks: 0, total_size_mb: 0, file_types: {} })),
      ]);

      const chatModel = tenant?.settings?.default_model || null;
      const embeddingModel = tenant?.settings?.embedding_model || null;
      
      // 有効なAPIキー（is_active = true）のみをカウント
      const activeApiKeys = apiKeys.api_keys?.filter(apiKey => apiKey.is_active) || [];
      const apiKeyCount = activeApiKeys.length;
      
      // APIキーの必要数の判定
      // チャット用モデルとベクトル埋め込みモデルが同一の場合は1つ、異なる場合は2つ必要
      const requiredApiKeyCount = (chatModel && embeddingModel && chatModel === embeddingModel) ? 1 : 2;
      const hasApiKey = apiKeyCount >= requiredApiKeyCount;

      // モデル設定 + APIキー登録の両方が揃っている場合のみ「設定済み」とみなす
      const hasChatModel = !!chatModel && apiKeyCount >= 1;
      const hasEmbeddingModel = !!embeddingModel && apiKeyCount >= 1;
      
      const statusCounts: Record<string, number> = contentStats.status_counts ?? {};
      const indexedCount = statusCounts['INDEXED'] ?? 0;
      const hasIndexedContent = indexedCount >= 1;
      // チャットボット利用可能な条件: モデル設定 + APIキー + インデックス済みコンテンツ
      const isReady = hasChatModel && hasEmbeddingModel && hasApiKey && hasIndexedContent;

      setSystemConfigStatus({
        hasChatModel,
        hasEmbeddingModel,
        hasApiKey,
        chatModelName: tenant?.settings?.default_model || null,
        embeddingModelName: tenant?.settings?.embedding_model || null,
        apiKeyCount,
        hasIndexedContent,
        indexedCount,
        isReady,
        isLoading: false,
        error: null,
      });
    } catch (err: unknown) {
      console.error('Failed to fetch system config status:', err);
      setSystemConfigStatus(prev => ({
        ...prev,
        isLoading: false,
        error: '設定状況の取得に失敗しました',
      }));
    }
  }, [user?.tenant_id]);

  useEffect(() => {
    fetchDashboardStats();
    fetchSystemConfigStatus();
    fetchTenantForEmbed();
  }, [fetchDashboardStats, fetchSystemConfigStatus, fetchTenantForEmbed]);

  // 最近の活動取得
  useEffect(() => {
    let timer: NodeJS.Timeout | null = null;
    let isCancelled = false;
    const fetchActivities = async (skipAudit: boolean = false) => {
      try {
        const items = await apiClient.getRecentActivities(10, skipAudit);
        if (!isCancelled) setActivities(items);
      } catch {
        // サイレント
      }
    };
    // 初回（監査ログを記録）
    fetchActivities(false);
    // 軽いポーリング（10秒、監査ログを記録しない）
    timer = setInterval(() => {
      fetchActivities(true);
    }, 10000);
    return () => {
      isCancelled = true;
      if (timer) clearInterval(timer);
    };
  }, []);

  const getRoleBadgeVariant = (role: string) => {
    switch (role) {
      case 'PLATFORM_ADMIN':
        return 'destructive';
      case 'TENANT_ADMIN':
        return 'default';
      case 'OPERATOR':
        return 'secondary';
      case 'AUDITOR':
        return 'outline';
      default:
        return 'outline';
    }
  };

  const getRoleLabel = (role: string) => {
    switch (role) {
      case 'PLATFORM_ADMIN':
        return 'プラットフォーム管理者';
      case 'TENANT_ADMIN':
        return 'テナント管理者';
      case 'OPERATOR':
        return '運用者';
      case 'AUDITOR':
        return '監査者';
      default:
        return role;
    }
  };

  /**
   * ユーザーの権限に応じたダッシュボードタイトルを取得
   * 
   * 戻り値:
   *   string: ダッシュボードタイトル
   */
  const getDashboardTitle = () => {
    switch (user?.role) {
      case 'PLATFORM_ADMIN':
        return 'プラットフォーム管理ダッシュボード';
      case 'TENANT_ADMIN':
        return 'テナント管理ダッシュボード';
      case 'OPERATOR':
        return '運用ダッシュボード';
      case 'AUDITOR':
        return '監査ダッシュボード';
      default:
        return 'ダッシュボード';
    }
  };

  /**
   * ユーザーの権限に応じたダッシュボード説明を取得
   * 
   * 戻り値:
   *   string: ダッシュボード説明
   */
  const getDashboardDescription = () => {
    switch (user?.role) {
      case 'PLATFORM_ADMIN':
        return 'プラットフォーム全体の管理と監視';
      case 'TENANT_ADMIN':
        return 'テナントの管理と運用状況の確認';
      case 'OPERATOR':
        return '日常的な運用業務の管理';
      case 'AUDITOR':
        return 'システムの監査とログ確認';
      default:
        return 'システムの概要と統計情報';
    }
  };

  /**
   * ユーザーの権限に応じた統計データを取得
   * 
   * 戻り値:
   *   boolean: 統計データを表示するかどうか
   */
  const shouldShowStats = () => {
    return user?.role === 'PLATFORM_ADMIN' || user?.role === 'TENANT_ADMIN';
  };

  /**
   * ユーザーの権限に応じたシステム状況を取得
   * 
   * 戻り値:
   *   boolean: システム状況を表示するかどうか
   */
  const shouldShowSystemStatus = () => {
    return user?.role === 'PLATFORM_ADMIN' || user?.role === 'TENANT_ADMIN';
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">{getDashboardTitle()}</h1>
        <p className="text-muted-foreground">
          {getDashboardDescription()}
        </p>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <AlertCircle className="h-5 w-5 text-red-400" />
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">エラー</h3>
              <div className="mt-2 text-sm text-red-700">{error}</div>
            </div>
          </div>
        </div>
      )}

      {/* ユーザー情報 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Users className="mr-2 h-5 w-5" />
            ユーザー情報
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="h-12 w-12 rounded-full bg-primary flex items-center justify-center">
                <span className="text-primary-foreground font-bold text-lg">
                  {user?.username.charAt(0).toUpperCase()}
                </span>
              </div>
              <div>
                <div className="font-medium">{user?.username}</div>
                <div className="text-sm text-muted-foreground">{user?.email}</div>
                <Badge variant={getRoleBadgeVariant(user?.role || '')} className="mt-1">
                  {getRoleLabel(user?.role || '')}
                </Badge>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* システム設定状況 */}
      {user?.tenant_id && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Settings className="mr-2 h-5 w-5" />
              システム設定状況
            </CardTitle>
            <CardDescription>
              システムを使用するために必要な設定の確認
            </CardDescription>
          </CardHeader>
          <CardContent>
            {systemConfigStatus.isLoading ? (
              <div className="flex items-center justify-center py-4">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary"></div>
              </div>
            ) : systemConfigStatus.error ? (
              <div className="text-sm text-muted-foreground">{systemConfigStatus.error}</div>
            ) : (
              <div className="space-y-4">
                <div className="space-y-2">
                  {/* コンテンツ（インデックス済み） */}
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      {systemConfigStatus.hasIndexedContent ? (
                        <CheckCircle className="h-5 w-5 text-green-600" />
                      ) : (
                        <XCircle className="h-5 w-5 text-red-600" />
                      )}
                      <span className="text-sm font-medium">コンテンツ</span>
                    </div>
                    <span className="text-sm text-muted-foreground">
                      インデックス済み {systemConfigStatus.indexedCount}
                    </span>
                  </div>

                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      {systemConfigStatus.hasChatModel ? (
                        <CheckCircle className="h-5 w-5 text-green-600" />
                      ) : (
                        <XCircle className="h-5 w-5 text-red-600" />
                      )}
                      <span className="text-sm font-medium">チャット用モデル</span>
                    </div>
                    <span className="text-sm text-muted-foreground">
                      {systemConfigStatus.hasChatModel
                        ? systemConfigStatus.chatModelName || '設定済み'
                        : '未設定'}
                    </span>
                  </div>

                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      {systemConfigStatus.hasEmbeddingModel ? (
                        <CheckCircle className="h-5 w-5 text-green-600" />
                      ) : (
                        <XCircle className="h-5 w-5 text-red-600" />
                      )}
                      <span className="text-sm font-medium">ベクトル埋め込みモデル</span>
                    </div>
                    <span className="text-sm text-muted-foreground">
                      {systemConfigStatus.hasEmbeddingModel
                        ? systemConfigStatus.embeddingModelName || '設定済み'
                        : '未設定'}
                    </span>
                  </div>

                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      {systemConfigStatus.hasApiKey ? (
                        <CheckCircle className="h-5 w-5 text-green-600" />
                      ) : (
                        <XCircle className="h-5 w-5 text-red-600" />
                      )}
                      <span className="text-sm font-medium">APIキー</span>
                    </div>
                    <span className="text-sm text-muted-foreground">
                      {systemConfigStatus.hasApiKey
                        ? `${systemConfigStatus.apiKeyCount}件有効`
                        : (() => {
                            const chatModel = systemConfigStatus.chatModelName;
                            const embeddingModel = systemConfigStatus.embeddingModelName;
                            const requiredCount = (chatModel && embeddingModel && chatModel === embeddingModel) ? 1 : 2;
                            return `不足（${requiredCount}件必要、現在有効${systemConfigStatus.apiKeyCount}件）`;
                          })()}
                    </span>
                  </div>
                </div>

                <div className="border-t pt-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      {systemConfigStatus.isReady ? (
                        <>
                          <CheckCircle className="h-5 w-5 text-green-600" />
                          <span className="text-sm font-medium text-green-600">チャットボット利用可能</span>
                        </>
                      ) : (
                        <>
                          <AlertCircle className="h-5 w-5 text-amber-600" />
                          <span className="text-sm font-medium text-amber-600">設定が必要</span>
                        </>
                      )}
                    </div>
                  </div>
                  {!systemConfigStatus.isReady && (
                    <div className="mt-3">
                      <p className="text-sm text-muted-foreground mb-3">
                        システムを使用するには、以下の設定が必要です：
                      </p>
                      <ul className="text-sm text-muted-foreground mb-3 list-disc list-inside space-y-1">
                        {!systemConfigStatus.hasChatModel && (
                          <li>チャット用モデルの選択</li>
                        )}
                        {!systemConfigStatus.hasEmbeddingModel && (
                          <li>ベクトル埋め込みモデルの選択</li>
                        )}
                        {!systemConfigStatus.hasApiKey && (
                          <li>
                            APIキーの登録
                            {systemConfigStatus.chatModelName && systemConfigStatus.embeddingModelName && (
                              <span className="ml-1">
                                （{systemConfigStatus.chatModelName === systemConfigStatus.embeddingModelName
                                  ? 'モデルが同一のため1件'
                                  : 'モデルが異なるため2件'}必要）
                              </span>
                            )}
                          </li>
                        )}
                        {!systemConfigStatus.hasIndexedContent && (
                          <li>インデックス済みコンテンツの登録（コンテンツ管理からファイルをアップロードしてください）</li>
                        )}
                      </ul>
                      <Link href="/settings">
                        <Button variant="default" size="sm">
                          <Settings className="mr-2 h-4 w-4" />
                          テナント設定を開く
                        </Button>
                      </Link>
                    </div>
                  )}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* 統計カード - 管理者のみ表示 */}
      {shouldShowStats() && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">総質問数</CardTitle>
            <BarChart3 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.totalQueries.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">
              <TrendingUp className="inline h-3 w-3 mr-1" />
              +12% 先月比
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">アクティブユーザー</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.activeUsers.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">
              <TrendingUp className="inline h-3 w-3 mr-1" />
              +8% 先月比
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">平均応答時間</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">3.2秒</div>
            <p className="text-xs text-muted-foreground">
              <TrendingUp className="inline h-3 w-3 mr-1 text-red-500" />
              -0.5秒 先月比
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">評価率</CardTitle>
            <CheckCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">72%</div>
            <p className="text-xs text-muted-foreground">
              <TrendingUp className="inline h-3 w-3 mr-1" />
              +5% 先月比
            </p>
          </CardContent>
        </Card>
        </div>
      )}

      {/* システム状況 - 管理者のみ表示 */}
      {shouldShowSystemStatus() && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Database className="mr-2 h-5 w-5" />
              コンテンツ状況
            </CardTitle>
            <CardDescription>
              ナレッジベースのコンテンツ処理状況
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <CheckCircle className="h-4 w-4 text-green-600" />
                <span className="text-sm">インデックス済み</span>
              </div>
              <Badge variant="default">{stats.indexedContents}</Badge>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Activity className="h-4 w-4 text-blue-600" />
                <span className="text-sm">処理中</span>
              </div>
              <Badge variant="secondary">{stats.processingContents}</Badge>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <AlertCircle className="h-4 w-4 text-red-600" />
                <span className="text-sm">失敗</span>
              </div>
              <Badge variant="destructive">{stats.failedContents}</Badge>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Building2 className="mr-2 h-5 w-5" />
              テナント状況
            </CardTitle>
            <CardDescription>
              システムテナントの利用状況
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm">総テナント数</span>
              <Badge variant="outline">{stats.totalTenants}</Badge>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm">アクティブテナント</span>
              <Badge variant="default">{stats.activeTenants}</Badge>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm">総ユーザー数</span>
              <Badge variant="outline">{stats.totalUsers}</Badge>
            </div>
          </CardContent>
        </Card>
        </div>
      )}

      {/* 最近の活動 */}
      <Card>
        <CardHeader>
          <CardTitle>最近の活動</CardTitle>
          <CardDescription>
            システム内での最近の活動履歴
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {activities.length === 0 ? (
              <div className="text-sm text-muted-foreground">最近の活動はありません</div>
            ) : (
              activities.map((a) => (
                <div key={a.id} className="flex items-center space-x-4">
                  <div className="h-2 w-2 bg-blue-500 rounded-full"></div>
                  <div className="flex-1">
                    <p className={`text-sm font-medium ${
                      (a.action?.includes('content_') || a.message?.includes('インデックス'))
                        ? 'text-red-600'
                        : ''
                    }`}>
                      {a.action}{a.entity_type ? `（${a.entity_type}）` : ''}
                    </p>
                    {a.message && (
                      <p className={`text-xs line-clamp-2 ${
                        (a.action?.includes('content_failed') || a.message?.includes('失敗'))
                          ? 'text-red-600 font-semibold'
                          : 'text-muted-foreground'
                      }`}>
                        {a.message}
                      </p>
                    )}
                    <p className="text-xs text-muted-foreground">
                      {a.created_at ? format(new Date(a.created_at), 'yyyy/MM/dd HH:mm', { locale: ja }) : '-'}
                    </p>
                  </div>
                </div>
              ))
            )}
          </div>
        </CardContent>
      </Card>

      {/* 埋め込みコード */}
      {user?.tenant_id && tenant && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Download className="mr-2 h-5 w-5" />
              埋め込みコード
            </CardTitle>
            <CardDescription>
              ウェブサイトにチャットウィジェットを埋め込むためのコード
              <span className="mt-1 block text-sm text-red-600">
                完全なAPIキーを含むコードをコピーするには必ず「コピー」ボタンをご利用ください。テキストエリアから直接コピーするとAPIキーが欠落します。
              </span>
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>埋め込みスニペット</Label>
              <Textarea
                value={`<!-- チャットウィジェット埋め込みコード -->
<script>
  (function(w,d,s,o,f,js,fjs){
    w['RAGChatWidget']=o;w[o]=w[o]||function(){(w[o].q=w[o].q||[]).push(arguments)};
    js=d.createElement(s),fjs=d.getElementsByTagName(s)[0];
    js.id=o;js.src=f;js.async=1;fjs.parentNode.insertBefore(js,fjs);
  }(window,document,'script','ragChat','${widgetScriptUrl}'));
  
  ragChat('init', {
    tenantId: '${tenant.id}',
    apiKey: '${tenant.api_key ? `${tenant.api_key.slice(0, 20)}...` : 'YOUR_API_KEY'}',
    apiBaseUrl: '${apiBaseUrl}',
    theme: 'light',
    position: 'bottom-right',
    initialMessage: 'こんにちは！何かお手伝いできることはありますか？' // オプション: 初期メッセージ
  });
</script>`}
                readOnly
                className="font-mono text-sm min-h-[200px]"
              />
              <div className="flex justify-end">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={async () => {
                    // 完全な埋め込みコード（APIキーを含む）
                    const embedCode = `<!-- チャットウィジェット埋め込みコード -->
<script>
  (function(w,d,s,o,f,js,fjs){
    w['RAGChatWidget']=o;w[o]=w[o]||function(){(w[o].q=w[o].q||[]).push(arguments)};
    js=d.createElement(s),fjs=d.getElementsByTagName(s)[0];
    js.id=o;js.src=f;js.async=1;fjs.parentNode.insertBefore(js,fjs);
  }(window,document,'script','ragChat','${widgetScriptUrl}'));
  
  ragChat('init', {
    tenantId: '${tenant.id}',
    apiKey: '${tenant.api_key || 'YOUR_API_KEY'}',
    apiBaseUrl: '${apiBaseUrl}',
    theme: 'light',
    position: 'bottom-right',
    initialMessage: 'こんにちは！何かお手伝いできることはありますか？' // オプション: 初期メッセージ
  });
</script>`;
                    try {
                      await navigator.clipboard.writeText(embedCode);
                      alert('クリップボードにコピーしました');
                    } catch (err) {
                      console.error('Failed to copy to clipboard:', err);
                    }
                  }}
                >
                  <Copy className="mr-2 h-4 w-4" />
                  コピー
                </Button>
              </div>
            </div>

            <Alert>
              <AlertDescription>
                このコードをウェブサイトのHTMLに貼り付けると、チャットウィジェットが表示されます。
              </AlertDescription>
            </Alert>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

/**
 * ダッシュボードページ
 * 
 * 認証が必要なダッシュボード画面を表示します。
 * ログインしていない場合は自動的にログイン画面にリダイレクトされます。
 */
export default function Dashboard() {
  return (
    <ProtectedRoute>
      <DashboardContent />
    </ProtectedRoute>
  );
}
