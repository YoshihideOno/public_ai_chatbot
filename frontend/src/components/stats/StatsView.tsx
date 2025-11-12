/**
 * 統計表示コンポーネント
 * 
 * 利用統計、ストレージ統計、トップクエリなどの統計情報を表示します。
 */

'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { apiClient } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import {
  BarChart3,
  TrendingUp,
  Clock,
  Database,
  Activity,
  AlertCircle,
  Download
} from 'lucide-react';
import { format, subDays, startOfDay, endOfDay } from 'date-fns';
import { ja } from 'date-fns/locale';

export function StatsView() {
  const [usageStats, setUsageStats] = useState<any>(null);
  const [storageStats, setStorageStats] = useState<any>(null);
  const [topQueries, setTopQueries] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [period, setPeriod] = useState<'today' | 'week' | 'month'>('month');

  const { user } = useAuth();

  useEffect(() => {
    fetchStats();
  }, [period]);

  const fetchStats = async () => {
    try {
      setIsLoading(true);
      setError(null);

      // 期間を計算
      const endDate = new Date();
      let startDate: Date;
      
      if (period === 'today') {
        startDate = startOfDay(endDate);
      } else if (period === 'week') {
        startDate = subDays(endDate, 7);
      } else {
        startDate = subDays(endDate, 30);
      }

      // 利用統計を取得
      try {
        const usage = await apiClient.getUsageStats(
          startDate.toISOString(),
          endDate.toISOString(),
          'day'
        );
        setUsageStats(usage);
      } catch (err) {
        console.error('Failed to fetch usage stats:', err);
        // エラーがあっても他の統計は表示する
      }

      // ストレージ統計を取得（ダッシュボード統計から取得）
      try {
        const dashboard = await apiClient.getDashboardStats(period);
        if (dashboard.storage_stats) {
          setStorageStats(dashboard.storage_stats);
        }
        if (dashboard.top_queries) {
          setTopQueries(dashboard.top_queries);
        }
      } catch (err) {
        console.error('Failed to fetch dashboard stats:', err);
        // エラーがあっても他の統計は表示する
      }
    } catch (err: any) {
      console.error('Failed to fetch stats:', err);
      setError('統計データの取得に失敗しました');
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="container mx-auto py-8">
        <div className="text-center">読み込み中...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto py-8">
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">統計・分析</h1>
          <p className="text-muted-foreground mt-2">
            システムの利用状況やパフォーマンスを確認できます
          </p>
        </div>
        
        <div className="flex gap-2">
          <Button
            variant={period === 'today' ? 'default' : 'outline'}
            onClick={() => setPeriod('today')}
            size="sm"
          >
            今日
          </Button>
          <Button
            variant={period === 'week' ? 'default' : 'outline'}
            onClick={() => setPeriod('week')}
            size="sm"
          >
            週
          </Button>
          <Button
            variant={period === 'month' ? 'default' : 'outline'}
            onClick={() => setPeriod('month')}
            size="sm"
          >
            月
          </Button>
        </div>
      </div>

      {/* 統計カード */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">総質問数</CardTitle>
            <BarChart3 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {usageStats?.total_queries?.toLocaleString() || 0}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              期間: {period === 'today' ? '今日' : period === 'week' ? '今週' : '今月'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">ユニークユーザー</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {usageStats?.unique_users?.toLocaleString() || 0}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              アクティブユーザー数
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">平均応答時間</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {usageStats?.avg_response_time_ms 
                ? `${(usageStats.avg_response_time_ms / 1000).toFixed(2)}秒`
                : '0秒'}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              平均レスポンス時間
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">評価率</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {usageStats?.feedback_rate 
                ? `${(usageStats.feedback_rate * 100).toFixed(1)}%`
                : '0%'}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              フィードバック提供率
            </p>
          </CardContent>
        </Card>
      </div>

      {/* ストレージ統計 */}
      {storageStats && (
        <Card>
          <CardHeader>
            <CardTitle>ストレージ使用状況</CardTitle>
            <CardDescription>ファイル保存容量の使用状況</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-sm font-medium">総ファイル数</span>
                <span className="text-lg font-bold">
                  {storageStats.total_files?.toLocaleString() || 0} ファイル
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm font-medium">使用容量</span>
                <span className="text-lg font-bold">
                  {storageStats.total_size_mb?.toFixed(2) || 0} MB
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm font-medium">使用率</span>
                <span className="text-lg font-bold">
                  {storageStats.usage_percentage?.toFixed(1) || 0}%
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-primary h-2 rounded-full"
                  style={{
                    width: `${Math.min(storageStats.usage_percentage || 0, 100)}%`
                  }}
                />
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* トップクエリ */}
      {topQueries && topQueries.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>よくある質問</CardTitle>
            <CardDescription>よく使われる質問のランキング</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {topQueries.map((query: any, index: number) => (
                <div key={index} className="flex items-start justify-between p-3 border rounded-lg">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-sm font-bold text-primary">#{index + 1}</span>
                      <span className="text-sm font-medium">{query.query}</span>
                    </div>
                    <div className="flex items-center gap-4 text-xs text-muted-foreground">
                      <span>回数: {query.count}</span>
                      <span>評価率: {(query.like_rate * 100).toFixed(1)}%</span>
                      <span>平均応答: {(query.avg_response_time_ms / 1000).toFixed(2)}秒</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

