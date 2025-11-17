/**
 * テナントコンテンツ処理完了通知設定コンポーネント
 * 
 * コンテンツ処理完了時のメール通知の有効/無効を設定するコンポーネント
 */

"use client";

import { useCallback, useEffect, useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { apiClient } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";

export default function TenantWebhookSettings() {
  const { user } = useAuth();
  const tenantId = user?.tenant_id ?? null;

  const [enableNotification, setEnableNotification] = useState<boolean>(true);
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
      setEnableNotification(typeof settings.enable_webhook === "boolean" ? settings.enable_webhook : true);
    } catch (error: unknown) {
      console.error('Failed to load webhook settings', error);
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

      await apiClient.updateTenantSettings(tenantId, {
        enable_webhook: enableNotification,
      });
      setSuccess("設定を保存しました");
      setShowSuccessDialog(true);
      await load();
    } catch (error: unknown) {
      console.error('Failed to save webhook settings', error);
      const message = error instanceof Error ? error.message : "設定の保存に失敗しました";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }, [tenantId, enableNotification, load]);

  return (
    <div className="space-y-4">
      <div className="text-sm text-muted-foreground">
        コンテンツ処理完了時に、アップロードしたユーザーにメール通知を送信します。
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

      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="space-y-0.5">
            <Label htmlFor="enable_notification">コンテンツ処理完了通知</Label>
            <p className="text-sm text-muted-foreground">
              コンテンツ処理完了時にメール通知を送信します
            </p>
          </div>
          <Switch
            id="enable_notification"
            checked={enableNotification}
            onCheckedChange={setEnableNotification}
            disabled={isLoading}
          />
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
          <div>コンテンツ処理完了通知の設定を保存しました。</div>
          <DialogFooter>
            <Button onClick={() => setShowSuccessDialog(false)}>閉じる</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

