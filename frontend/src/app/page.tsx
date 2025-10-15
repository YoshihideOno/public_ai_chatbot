'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { apiClient } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import { 
  Users, 
  Building2, 
  FileText, 
  BarChart3,
  TrendingUp,
  Clock,
  CheckCircle,
  AlertCircle,
  Activity,
  Database
} from 'lucide-react';
import { format } from 'date-fns';
import { ja } from 'date-fns/locale';

export default function Dashboard() {
  const [stats, setStats] = useState({
    totalUsers: 0,
    totalTenants: 0,
    totalContents: 0,
    totalQueries: 0,
    activeUsers: 0,
    indexedContents: 0,
    processingContents: 0,
    failedContents: 0,
  });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const { user } = useAuth();

  useEffect(() => {
    fetchDashboardStats();
  }, []);

  const fetchDashboardStats = async () => {
    try {
      setIsLoading(true);
      setError(null);

      // ダッシュボード統計を取得
      const dashboardStats = await apiClient.getDashboardStats('month');
      
      setStats({
        totalUsers: dashboardStats.usage_stats?.total_queries || 0,
        totalTenants: dashboardStats.usage_stats?.unique_users || 0,
        totalContents: dashboardStats.storage_stats?.total_files || 0,
        totalQueries: dashboardStats.usage_stats?.total_queries || 0,
        activeUsers: dashboardStats.usage_stats?.unique_users || 0,
        indexedContents: dashboardStats.storage_stats?.total_files || 0,
        processingContents: 0,
        failedContents: 0,
      });
    } catch (err: any) {
      console.error('Failed to fetch dashboard stats:', err);
      setError('統計データの取得に失敗しました');
    } finally {
      setIsLoading(false);
    }
  };

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
        <h1 className="text-3xl font-bold">ダッシュボード</h1>
        <p className="text-muted-foreground">
          システムの概要と統計情報
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
        </CardContent>
      </Card>

      {/* 統計カード */}
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

      {/* システム状況 */}
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
              <Badge variant="default">{stats.totalTenants}</Badge>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm">総ユーザー数</span>
              <Badge variant="outline">{stats.totalUsers}</Badge>
            </div>
          </CardContent>
        </Card>
      </div>

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
            <div className="flex items-center space-x-4">
              <div className="h-2 w-2 bg-green-500 rounded-full"></div>
              <div className="flex-1">
                <p className="text-sm font-medium">新しいコンテンツがアップロードされました</p>
                <p className="text-xs text-muted-foreground">
                  {format(new Date(), 'yyyy/MM/dd HH:mm', { locale: ja })}
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <div className="h-2 w-2 bg-blue-500 rounded-full"></div>
              <div className="flex-1">
                <p className="text-sm font-medium">テナント「Acme Corp」が作成されました</p>
                <p className="text-xs text-muted-foreground">
                  {format(new Date(Date.now() - 3600000), 'yyyy/MM/dd HH:mm', { locale: ja })}
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <div className="h-2 w-2 bg-yellow-500 rounded-full"></div>
              <div className="flex-1">
                <p className="text-sm font-medium">APIキーが再発行されました</p>
                <p className="text-xs text-muted-foreground">
                  {format(new Date(Date.now() - 7200000), 'yyyy/MM/dd HH:mm', { locale: ja })}
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}