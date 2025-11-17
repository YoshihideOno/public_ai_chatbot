"use client";

// テナントのテキスト分割設定（chunk_size, chunk_overlap）を編集するコンポーネント
// 目的: テナント設定に保存された値を利用しつつ、必要に応じてユーザーが変更できるようにする

import { useCallback, useEffect, useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { apiClient } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";

export default function TenantChunkSettings() {
  const { user } = useAuth();
  const tenantId = user?.tenant_id ?? null;

  const [chunkSize, setChunkSize] = useState<number>(1024);
  const [chunkOverlap, setChunkOverlap] = useState<number>(200);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [showSuccessDialog, setShowSuccessDialog] = useState(false);

  const load = useCallback(async () => {
    if (!tenantId) return;
    try {
      setIsLoading(true);
      setError(null);
      const tenant = await apiClient.getTenant(tenantId);
      const settings = tenant?.settings || {};
      setChunkSize(typeof settings.chunk_size === "number" ? settings.chunk_size : 1024);
      setChunkOverlap(typeof settings.chunk_overlap === "number" ? settings.chunk_overlap : 200);
    } catch (error: unknown) {
      console.error('Failed to load chunk settings', error);
      setError("設定の読み込みに失敗しました");
    } finally {
      setIsLoading(false);
    }
  }, [tenantId]);

  useEffect(() => { void load(); }, [load]);

  const onSave = useCallback(async () => {
    if (!tenantId) {
      setError("テナントIDが取得できません");
      return;
    }
    try {
      setIsLoading(true);
      setError(null);
      setSuccess(null);
      // バリデーション（クライアント）
      if (chunkSize < 256 || chunkSize > 4096) {
        setError("チャンクサイズは256〜4096の範囲で入力してください");
        return;
      }
      if (chunkOverlap < 0 || chunkOverlap > 512) {
        setError("チャンクオーバーラップは0〜512の範囲で入力してください");
        return;
      }
      await apiClient.updateTenantSettings(tenantId, {
        chunk_size: chunkSize,
        chunk_overlap: chunkOverlap,
      });
      setSuccess("設定を保存しました");
      setShowSuccessDialog(true);
      await load();
    } catch (error: unknown) {
      console.error('Failed to save chunk settings', error);
      const message = error instanceof Error ? error.message : "設定の保存に失敗しました";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }, [tenantId, chunkSize, chunkOverlap, load]);

  return (
    <div className="space-y-4">
      <div className="text-sm text-muted-foreground">
        テキストをチャンク（分割）してベクトル化します。通常は既定値のままで問題ありませんが、
        AIに詳しい方はコンテンツの特性に応じて調整しても構いません。
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}
      {success && (
        <Alert>
          <AlertDescription>{success}</AlertDescription>
        </Alert>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="chunk_size">チャンクサイズ</Label>
          <Input
            id="chunk_size"
            type="number"
            value={chunkSize}
            onChange={(e) => setChunkSize(parseInt(e.target.value || "0", 10))}
            min={256}
            max={4096}
            disabled={isLoading}
          />
          <div className="text-xs text-muted-foreground">1チャンクの最大文字数（既定: 1024）</div>
        </div>
        <div className="space-y-2">
          <Label htmlFor="chunk_overlap">チャンクオーバーラップ</Label>
          <Input
            id="chunk_overlap"
            type="number"
            value={chunkOverlap}
            onChange={(e) => setChunkOverlap(parseInt(e.target.value || "0", 10))}
            min={0}
            max={512}
            disabled={isLoading}
          />
          <div className="text-xs text-muted-foreground">隣接チャンク間の重複文字数（既定: 200）</div>
        </div>
      </div>

      <div className="flex justify-end">
        <Button onClick={() => void onSave()} disabled={isLoading}>保存</Button>
      </div>

      <Dialog open={showSuccessDialog} onOpenChange={setShowSuccessDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>保存完了</DialogTitle>
          </DialogHeader>
          <div>テキスト分割の設定を保存しました。</div>
        </DialogContent>
      </Dialog>
    </div>
  );
}


