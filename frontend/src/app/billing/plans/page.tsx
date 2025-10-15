'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/contexts/AuthContext';
import { apiClient } from '@/lib/api';

export default function BillingPlansPage() {
  const { user } = useAuth();
  const [loadingPlan, setLoadingPlan] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const selectPlan = async (plan: 'BASIC' | 'PRO', billingCycle: 'MONTHLY' | 'YEARLY' = 'MONTHLY') => {
    try {
      setError(null);
      setLoadingPlan(`${plan}_${billingCycle}`);
      const { url } = await apiClient.createCheckoutSession(plan, billingCycle);
      window.location.href = url;
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Checkoutセッションの作成に失敗しました');
      setLoadingPlan(null);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">プラン選択</h1>
        <p className="text-muted-foreground">ご希望のプランを選択して、Stripeでお支払いに進みます。</p>
      </div>

      {error && (
        <div className="text-red-600 text-sm">{error}</div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Basic</CardTitle>
            <CardDescription>中小企業向けプラン</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div>¥5,000 / 月</div>
            <ul className="text-sm list-disc pl-5">
              <li>質問 1,000/月</li>
              <li>ストレージ 1GB</li>
              <li>ユーザー 5</li>
            </ul>
            <div className="flex gap-3">
              <Button disabled={loadingPlan !== null} onClick={() => selectPlan('BASIC', 'MONTHLY')}>
                {loadingPlan === 'BASIC_MONTHLY' ? '遷移中...' : '月額で選択'}
              </Button>
              <Button variant="secondary" disabled={loadingPlan !== null} onClick={() => selectPlan('BASIC', 'YEARLY')}>
                {loadingPlan === 'BASIC_YEARLY' ? '遷移中...' : '年額で選択（20%OFF）'}
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Pro</CardTitle>
            <CardDescription>成長企業向けプラン</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div>¥20,000 / 月</div>
            <ul className="text-sm list-disc pl-5">
              <li>質問 10,000/月</li>
              <li>ストレージ 10GB</li>
              <li>ユーザー 無制限</li>
              <li>サポート: メール+チャット</li>
            </ul>
            <div className="flex gap-3">
              <Button disabled={loadingPlan !== null} onClick={() => selectPlan('PRO', 'MONTHLY')}>
                {loadingPlan === 'PRO_MONTHLY' ? '遷移中...' : '月額で選択'}
              </Button>
              <Button variant="secondary" disabled={loadingPlan !== null} onClick={() => selectPlan('PRO', 'YEARLY')}>
                {loadingPlan === 'PRO_YEARLY' ? '遷移中...' : '年額で選択（20%OFF）'}
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}


