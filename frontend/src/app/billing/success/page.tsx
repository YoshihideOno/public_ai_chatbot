'use client';

import React from 'react';
import Link from 'next/link';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

export default function BillingSuccessPage() {
  return (
    <div className="flex items-center justify-center h-[60vh]">
      <Card className="max-w-md w-full">
        <CardHeader>
          <CardTitle>お支払いが完了しました</CardTitle>
          <CardDescription>ご契約ありがとうございます。設定は数分以内に反映されます。</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-muted-foreground">引き続きサービスをご利用いただけます。問題が発生した場合はサポートまでお問い合わせください。</p>
          <div className="flex gap-3">
            <Link href="/dashboard"><Button>ダッシュボードへ</Button></Link>
            <Link href="/billing/plans"><Button variant="secondary">プランに戻る</Button></Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}


