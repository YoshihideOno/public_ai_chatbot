/**
 * 統計・分析ページ
 * 
 * このファイルは統計・分析画面を表示するためのページコンポーネントを定義します。
 * 利用統計、ストレージ統計、トップクエリなどの統計情報を表示します。
 * 
 * 主な機能:
 * - 利用統計の表示
 * - ストレージ統計の表示
 * - トップクエリの表示
 * - 期間選択機能
 */

'use client';

import { StatsView } from '@/components/stats/StatsView';
import { QueryAnalyticsControls } from '@/components/stats/QueryAnalyticsControls';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';

export default function StatsPage() {
  return (
    <ProtectedRoute>
      <div className="space-y-6">
        <QueryAnalyticsControls />
        <StatsView />
      </div>
    </ProtectedRoute>
  );
}

