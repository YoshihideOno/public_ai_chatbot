/**
 * テナントLLMモデル設定コンポーネント
 * 
 * 既定の回答モデルと埋め込みモデルを選択し、テナント設定として保存する。
 */

'use client';

import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { apiClient, TenantSettings } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';

export function TenantLlmModels() {
  const { user } = useAuth();
  const tenantId = user?.tenant_id || '';

  const [providers, setProviders] = useState<Array<{ provider: string; models: string[] }>>([]);
  const [error, setError] = useState<string | null>(null);
  const [showSuccessDialog, setShowSuccessDialog] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const UNSELECTED_VALUE = "__none__";
  const [defaultModel, setDefaultModel] = useState<string>(UNSELECTED_VALUE);
  const [embeddingModel, setEmbeddingModel] = useState<string>(UNSELECTED_VALUE);

  const allModels = useMemo(() => Array.from(new Set(providers.flatMap(p => p.models))), [providers]);

  const load = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const p = await apiClient.getProvidersAndModels();
      setProviders(p.providers || []);
      if (tenantId) {
        // テナント情報を取得して現在の設定を反映（getTenantを利用）
        try {
          const tenant = await apiClient.getTenant(tenantId);
          setDefaultModel(tenant?.settings?.default_model || UNSELECTED_VALUE);
          setEmbeddingModel(tenant?.settings?.embedding_model || UNSELECTED_VALUE);
        } catch {}
      }
    } catch {
      setError('モデル一覧の取得に失敗しました');
    } finally {
      setIsLoading(false);
    }
  }, [tenantId]);

  useEffect(() => { void load(); }, [load]);

  const onSave = async () => {
    try {
      setIsLoading(true);
      setError(null);
      if (!tenantId) {
        setError('テナントIDが取得できません');
        return;
      }
      const settings: Partial<TenantSettings> = {
        default_model: (defaultModel === UNSELECTED_VALUE ? null : defaultModel) as string | null | undefined,
        embedding_model: (embeddingModel === UNSELECTED_VALUE ? null : embeddingModel) as string | null | undefined,
      };
      console.log('保存する設定:', settings);
      await apiClient.updateTenantSettings(tenantId, settings);
      setShowSuccessDialog(true);
      // 保存後に再読み込み
      await load();
    } catch (e: unknown) {
      console.error('保存エラー:', e);
      const errorMessage = e instanceof Error ? e.message : 'モデル設定の保存に失敗しました';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {error && (
        <Alert variant="destructive"><AlertDescription>{error}</AlertDescription></Alert>
      )}

      <Dialog open={showSuccessDialog} onOpenChange={setShowSuccessDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>保存完了</DialogTitle>
            <DialogDescription>
              設定を正常に保存しました。
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button onClick={() => setShowSuccessDialog(false)}>閉じる</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Card>
        <CardHeader>
          <CardTitle>チャット用モデル</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground mb-3">ユーザーとの会話で回答を生成する際に使用するLLMモデルです。精度とコストのバランスを考慮して選択してください。<br />モデルの選択に迷ったら gpt-4o-mini を選択してください。</p>
          <Select value={defaultModel} onValueChange={setDefaultModel}>
            <SelectTrigger><SelectValue placeholder="選択" /></SelectTrigger>
            <SelectContent>
              <SelectItem value={UNSELECTED_VALUE}>未選択</SelectItem>
              {allModels.map(m => (<SelectItem key={m} value={m}>{m}</SelectItem>))}
            </SelectContent>
          </Select>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>ベクトル埋め込みモデル</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground mb-3">ドキュメント検索（RAG）のためにテキストをベクトル化するモデルです。検索精度や既存のベクトルストアと互換性のあるモデルを選択してください。<br />モデルの選択に迷ったら gpt-3.5-turbo を選択してください。</p>
          <Select value={embeddingModel} onValueChange={setEmbeddingModel}>
            <SelectTrigger><SelectValue placeholder="選択" /></SelectTrigger>
            <SelectContent>
              <SelectItem value={UNSELECTED_VALUE}>未選択</SelectItem>
              {allModels.map(m => (<SelectItem key={m} value={m}>{m}</SelectItem>))}
            </SelectContent>
          </Select>
        </CardContent>
      </Card>

      <div className="text-right">
        <Button onClick={onSave} disabled={isLoading}>保存</Button>
      </div>
    </div>
  );
}

export default TenantLlmModels;


