'use client';

/**
 * クエリアナリティクス再集計コントロール
 *
 * 管理者/運用者向けに、期間・言語を指定して再集計をトリガーするUIを提供します。
 */

import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { apiClient } from '@/lib/api';

type Period = 'today' | 'week' | 'month' | 'custom';

export function QueryAnalyticsControls() {
  const [locale, setLocale] = useState<string>('ja');
  const [period, setPeriod] = useState<Period>('month');
  const [startDate, setStartDate] = useState<string>('');
  const [endDate, setEndDate] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleRebuild = async () => {
    setIsLoading(true);
    setError(null);
    setMessage(null);
    try {
      const params: Parameters<typeof apiClient.rebuildQueryAnalytics>[0] = { locale, period };
      if (period === 'custom') {
        if (!startDate || !endDate) {
          setError('custom期間では開始日と終了日が必要です');
          setIsLoading(false);
          return;
        }
        params.start_date = new Date(startDate).toISOString();
        params.end_date = new Date(endDate).toISOString();
      }
      await apiClient.rebuildQueryAnalytics(params);
      setMessage('再集計を実行しました');
    } catch (error: unknown) {
      // サーバーからのエラーメッセージを優先表示
      const apiError = error as {
        response?: { data?: { error?: { message?: string }; message?: string } };
        message?: string;
      };
      const apiMsg = apiError.response?.data?.error?.message
        || apiError.response?.data?.message
        || apiError.message
        || '再集計の実行に失敗しました';
      setError(apiMsg);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>よくある質問 自動集計</CardTitle>
        <CardDescription>期間・言語を指定して再集計を実行します</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-5 gap-3 items-end">
          <div className="md:col-span-1">
            <label className="text-sm mb-1 block">言語</label>
            <Input value={locale} onChange={(e) => setLocale(e.target.value)} placeholder="ja" />
          </div>
          <div className="md:col-span-1">
            <label className="text-sm mb-1 block">期間</label>
            <Select value={period} onValueChange={(v: Period) => setPeriod(v)}>
              <SelectTrigger>
                <SelectValue placeholder="期間" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="today">今日</SelectItem>
                <SelectItem value="week">直近7日</SelectItem>
                <SelectItem value="month">直近30日</SelectItem>
                <SelectItem value="custom">カスタム</SelectItem>
              </SelectContent>
            </Select>
          </div>
          {period === 'custom' && (
            <>
              <div className="md:col-span-1">
                <label className="text-sm mb-1 block">開始</label>
                <Input type="datetime-local" value={startDate} onChange={(e) => setStartDate(e.target.value)} />
              </div>
              <div className="md:col-span-1">
                <label className="text-sm mb-1 block">終了</label>
                <Input type="datetime-local" value={endDate} onChange={(e) => setEndDate(e.target.value)} />
              </div>
            </>
          )}
          <div className="md:col-span-1">
            <Button onClick={handleRebuild} disabled={isLoading} className="w-full">
              {isLoading ? '実行中...' : '再集計を実行'}
            </Button>
          </div>
        </div>

        {message && (
          <Alert className="mt-3">
            <AlertDescription>{message}</AlertDescription>
          </Alert>
        )}
        {error && (
          <Alert className="mt-3" variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}
      </CardContent>
    </Card>
  );
}


