/**
 * テナントAPIキー管理コンポーネント
 * 
 * テナント管理者がLLMプロバイダーのAPIキーを登録・一覧できるUIを提供する。
 */

'use client';

import React, { useCallback, useEffect, useState } from 'react';
import { apiClient } from '@/lib/api';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';
import { ExternalLink } from 'lucide-react';
import { logger } from '@/utils/logger';

/**
 * プロバイダー別APIキー取得URLマッピング
 * 各LLMプロバイダーのAPIキー取得ページへのURLを定義します。
 */
const PROVIDER_API_KEY_URLS: Record<string, string> = {
  openai: 'https://platform.openai.com/api-keys',
  anthropic: 'https://console.anthropic.com/settings/keys',
  google: 'https://aistudio.google.com/app/apikey',
};

/**
 * プロバイダー名の日本語表示マッピング
 */
const PROVIDER_DISPLAY_NAMES: Record<string, string> = {
  openai: 'OpenAI',
  anthropic: 'Anthropic',
  google: 'Google (Gemini)',
};

export function TenantApiKeys() {
  const [providers, setProviders] = useState<Array<{ provider: string; models: string[] }>>([]);
  const [apiKeys, setApiKeys] = useState<Array<{ id: string; provider: string; api_key_masked: string; model: string; is_active: boolean; created_at: string }>>([]);
  const [error, setError] = useState<string | null>(null);
  const [showVerifySuccessDialog, setShowVerifySuccessDialog] = useState(false);
  const [showRegisterSuccessDialog, setShowRegisterSuccessDialog] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [togglingApiKeyId, setTogglingApiKeyId] = useState<string | null>(null);
  const [selectedProvider, setSelectedProvider] = useState<string | undefined>(undefined);
  const [selectedModel, setSelectedModel] = useState<string | undefined>(undefined);
  const [plainApiKey, setPlainApiKey] = useState('');
  const [verifyingInline, setVerifyingInline] = useState(false);
  const [verifyOk, setVerifyOk] = useState(false);

  const load = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const p = await apiClient.getProvidersAndModels();
      setProviders(p.providers || []);
      const list = await apiClient.getApiKeys();
      setApiKeys(list.api_keys || []);
      if (!selectedProvider && p.providers?.length > 0) {
        setSelectedProvider(p.providers[0].provider);
        setSelectedModel(p.providers[0].models?.[0]);
      }
    } catch {
      setError('APIキー情報の取得に失敗しました');
    } finally {
      setIsLoading(false);
    }
  }, [selectedProvider]);

  useEffect(() => { void load(); }, [load]);

  const onCreate = async () => {
    try {
      setIsLoading(true);
      setError(null);
      setSuccess(null);
      if (!selectedProvider || !selectedModel || !plainApiKey) {
        setError('プロバイダー、モデル、APIキーを入力してください');
        return;
      }
      logger.info('APIキー登録リクエスト', { provider: selectedProvider, model: selectedModel, api_key_length: plainApiKey.length });
      await apiClient.createApiKey({ provider: selectedProvider, model: selectedModel, api_key: plainApiKey });
      setPlainApiKey('');
      setVerifyOk(false);
      setSuccess('APIキーを登録しました');
      setShowRegisterSuccessDialog(true);
      await load();
    } catch (e: unknown) {
      logger.error('APIキー登録エラー', e);
      let errorMessage = 'APIキーの登録に失敗しました';
      
      // axiosのエラーレスポンスから詳細メッセージを取得
      if (e && typeof e === 'object' && 'response' in e) {
        interface AxiosErrorLike {
          response?: {
            data?: {
              detail?: string;
              message?: string;
            };
          };
          message?: string;
        }
        const axiosError = e as AxiosErrorLike;
        if (axiosError.response?.data?.detail) {
          errorMessage = axiosError.response.data.detail;
        } else if (axiosError.response?.data?.message) {
          errorMessage = axiosError.response.data.message;
        } else if (axiosError.message) {
          errorMessage = axiosError.message;
        }
      } else if (e instanceof Error) {
        errorMessage = e.message;
      }
      
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * APIキーの有効/無効を切り替え
   * 
   * @param apiKeyId APIキーID
   * @param currentStatus 現在の有効/無効状態
   */
  const handleToggleActive = async (apiKeyId: string, currentStatus: boolean) => {
    try {
      setTogglingApiKeyId(apiKeyId);
      setError(null);
      
      const newStatus = !currentStatus;
      await apiClient.updateApiKey(apiKeyId, { is_active: newStatus });
      
      // 一覧を再読み込み
      await load();
    } catch (e: unknown) {
      logger.error('APIキー有効/無効切り替えエラー', e);
      let errorMessage = '有効/無効の切り替えに失敗しました';
      
      // axiosのエラーレスポンスから詳細メッセージを取得
      if (e && typeof e === 'object' && 'response' in e) {
        interface AxiosErrorLike {
          response?: {
            data?: {
              detail?: string;
              message?: string;
            };
          };
          message?: string;
        }
        const axiosError = e as AxiosErrorLike;
        if (axiosError.response?.data?.detail) {
          errorMessage = axiosError.response.data.detail;
        } else if (axiosError.response?.data?.message) {
          errorMessage = axiosError.response.data.message;
        } else if (axiosError.message) {
          errorMessage = axiosError.message;
        }
      } else if (e instanceof Error) {
        errorMessage = e.message;
      }
      
      setError(errorMessage);
    } finally {
      setTogglingApiKeyId(null);
    }
  };

  const modelsForProvider = providers.find(p => p.provider === selectedProvider)?.models || [];

  const handleVerifyInline = async () => {
    try {
      setVerifyingInline(true);
      setVerifyOk(false);
      setError(null);
      if (!selectedProvider || !selectedModel || !plainApiKey) {
        setError('プロバイダー、モデル、APIキーを入力してください');
        return;
      }
      const res = await apiClient.verifyApiKeyInline({ provider: selectedProvider, model: selectedModel, api_key: plainApiKey });
      if (res.valid) {
        setVerifyOk(true);
        setSuccess(`検証成功: ${res.provider} / ${res.model} (${res.message || 'OK'})`);
        setShowVerifySuccessDialog(true);
      } else {
        setVerifyOk(false);
        setError(`検証失敗: ${res.error_code || 'error'} - ${res.message || ''}`);
      }
    } catch (e: unknown) {
      setVerifyOk(false);
      logger.error('APIキー検証エラー', e);
      setError('APIキーの検証に失敗しました');
    } finally {
      setVerifyingInline(false);
    }
  };

  // 入力が変わったら検証状態をリセット
  useEffect(() => {
    setVerifyOk(false);
  }, [selectedProvider, selectedModel, plainApiKey]);

  return (
    <div className="space-y-6">
      {error && (
        <Alert variant="destructive"><AlertDescription>{error}</AlertDescription></Alert>
      )}

      <Dialog open={showVerifySuccessDialog} onOpenChange={setShowVerifySuccessDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>検証成功</DialogTitle>
            <DialogDescription>
              APIキーが有効であることを確認しました。
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button onClick={() => setShowVerifySuccessDialog(false)}>閉じる</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={showRegisterSuccessDialog} onOpenChange={setShowRegisterSuccessDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>登録完了</DialogTitle>
            <DialogDescription>
              APIキーを正常に登録しました。
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button onClick={() => setShowRegisterSuccessDialog(false)}>閉じる</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Card>
        <CardHeader>
          <CardTitle>APIキー登録</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <div className="text-sm mb-2">プロバイダー</div>
              <Select value={selectedProvider} onValueChange={(v) => { setSelectedProvider(v); setSelectedModel(undefined); }}>
                <SelectTrigger><SelectValue placeholder="選択" /></SelectTrigger>
                <SelectContent>
                  {providers.map(p => (<SelectItem key={p.provider} value={p.provider}>{p.provider}</SelectItem>))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <div className="text-sm mb-2">モデル</div>
              <Select value={selectedModel} onValueChange={(v) => setSelectedModel(v)}>
                <SelectTrigger><SelectValue placeholder="選択" /></SelectTrigger>
                <SelectContent>
                  {modelsForProvider.map(m => (<SelectItem key={m} value={m}>{m}</SelectItem>))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <div className="text-sm mb-2">APIキー</div>
              <Input value={plainApiKey} onChange={(e) => setPlainApiKey(e.target.value)} placeholder="sk-..." type="password" autoComplete="new-password" />
            </div>
          </div>
          <div className="flex items-center justify-end gap-2">
            <Button variant="outline" onClick={() => void handleVerifyInline()} disabled={isLoading || verifyingInline}>
              {verifyingInline ? '検証中...' : '検証'}
            </Button>
            <Button onClick={onCreate} disabled={isLoading || !verifyOk}>登録</Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>APIキー取得方法</CardTitle>
        </CardHeader>
        <CardContent>
          <Accordion type="single" collapsible className="w-full">
            {providers.map((provider) => {
              const apiKeyUrl = PROVIDER_API_KEY_URLS[provider.provider];
              const displayName = PROVIDER_DISPLAY_NAMES[provider.provider] || provider.provider;
              
              if (!apiKeyUrl) {
                return null;
              }

              return (
                <AccordionItem key={provider.provider} value={provider.provider}>
                  <AccordionTrigger>{displayName}</AccordionTrigger>
                  <AccordionContent>
                    <div className="space-y-3">
                      <p className="text-sm text-muted-foreground">
                        まだsign upしていない方は先にsign upの上ログインしてください。
                      </p>
                      <div>
                        <a
                          href={apiKeyUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-2 text-sm text-primary hover:underline"
                        >
                          <span>APIキー取得ページ</span>
                          <ExternalLink className="h-4 w-4" />
                        </a>
                      </div>
                    </div>
                  </AccordionContent>
                </AccordionItem>
              );
            })}
          </Accordion>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>登録済みAPIキー</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {apiKeys.length === 0 && <div className="text-sm text-muted-foreground">登録済みのAPIキーはありません</div>}
            {apiKeys.map(k => (
              <div key={k.id} className="border rounded p-3 flex flex-col md:flex-row md:items-center md:justify-between gap-2">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <div className="font-medium text-sm">
                      {k.provider}{k.model ? ` / ${k.model}` : ''}
                    </div>
                    <Badge variant={k.is_active ? 'default' : 'secondary'} className="text-xs">
                      {k.is_active ? '有効' : '無効'}
                    </Badge>
                  </div>
                  <div className="text-sm text-muted-foreground mb-1 break-all whitespace-pre-wrap font-mono">{k.api_key_masked}</div>
                  <div className="text-xs text-muted-foreground">{new Date(k.created_at).toLocaleString()}</div>
                </div>
                <div className="flex items-center gap-3 md:ml-4 self-start md:self-auto">
                  <div className="flex items-center gap-2">
                    <Switch
                      checked={k.is_active}
                      onCheckedChange={() => handleToggleActive(k.id, k.is_active)}
                      disabled={togglingApiKeyId === k.id || isLoading}
                    />
                    <Label className="text-sm text-muted-foreground">
                      {k.is_active ? '有効' : '無効'}
                    </Label>
                  </div>
                  {/* 登録済みの行ごとの検証ボタンは、登録前の検証UIに集約するため未表示 */}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default TenantApiKeys;


