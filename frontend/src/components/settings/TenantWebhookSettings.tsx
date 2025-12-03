/**
 * テナントコンテンツ処理完了通知設定コンポーネント
 * 
 * コンテンツ処理完了時のメール通知の有効/無効を設定するコンポーネント
 */

'use client';

import { useCallback, useEffect, useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { apiClient } from "@/lib/api";
import { useTenant } from "@/contexts/TenantContext";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Input } from "@/components/ui/input";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";

export default function TenantWebhookSettings() {
  const { user } = useAuth();
  const tenantId = user?.tenant_id ?? null;
  const { tenant, reloadTenant } = useTenant();

  const [enableNotification, setEnableNotification] = useState<boolean>(true);
  const [widgetOrigins, setWidgetOrigins] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [showSuccessDialog, setShowSuccessDialog] = useState(false);

  /**
   * TenantContext から取得した設定値をローカル状態に反映
   */
  useEffect(() => {
    if (!tenant) {
      // テナント情報がまだない場合はデフォルトtrue（従来挙動を維持）
      setEnableNotification(true);
      setWidgetOrigins('');
      return;
    }
    const settings = tenant.settings || {};
    setEnableNotification(
      typeof settings.enable_webhook === "boolean" ? settings.enable_webhook : true,
    );
    // allowed_widget_origins はCSV形式で保存されている前提
    // TenantContextの型に含まれていない可能性があるため、安全にアクセス
    const anyTenant = tenant as typeof tenant & { allowed_widget_origins?: string | null };
    setWidgetOrigins(anyTenant.allowed_widget_origins || '');
  }, [tenant]);

  const onSave = useCallback(async () => {
    if (!tenantId) {
      setError("テナントIDが取得できません");
      return;
    }
    try {
      setIsLoading(true);
      setError(null);
      setSuccess(null);

      // コンテンツ処理完了通知の設定を更新
      await apiClient.updateTenantSettings(tenantId, {
        enable_webhook: enableNotification,
      });

      // 設置ドメイン（allowed_widget_origins）を更新
      await apiClient.updateTenant(tenantId, {
        allowed_widget_origins: widgetOrigins || null,
      });

      // グローバルなテナント情報を更新して他画面にも反映
      await reloadTenant();
      setSuccess("設定を保存しました");
      setShowSuccessDialog(true);
    } catch (error: unknown) {
      console.error('Failed to save webhook settings', error);
      const message = error instanceof Error ? error.message : "設定の保存に失敗しました";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }, [tenantId, enableNotification, reloadTenant]);

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

      <div className="space-y-6">
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

        <div className="space-y-1">
          <Label htmlFor="widget_origins">設置ドメイン</Label>
          <p className="text-sm text-muted-foreground">
            ウィジェットを設置するドメインをカンマ区切りで指定します（例: https://example.com,https://sub.example.com）
          </p>
          <Input
            id="widget_origins"
            value={widgetOrigins}
            onChange={(e) => setWidgetOrigins(e.target.value)}
            placeholder="https://example.com"
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

