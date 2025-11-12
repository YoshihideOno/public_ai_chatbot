'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Separator } from '@/components/ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { apiClient, Tenant } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import { 
  ArrowLeft, 
  Save, 
  Key,
  Copy,
  Download,
  Settings
} from 'lucide-react';
import { format } from 'date-fns';
import { ja } from 'date-fns/locale';

const tenantSchema = z.object({
  name: z.string().min(2, 'テナント名は2文字以上である必要があります'),
  domain: z.string().min(3, 'ドメインは3文字以上である必要があります'),
  plan: z.enum(['FREE', 'BASIC', 'PRO', 'ENTERPRISE']),
  status: z.enum(['ACTIVE', 'SUSPENDED', 'DELETED']),
  settings: z.object({
    default_model: z.string().optional(),
    chunk_size: z.number().optional(),
    chunk_overlap: z.number().optional(),
    max_queries_per_day: z.number().optional(),
    max_storage_mb: z.number().optional(),
    enable_api_access: z.boolean().optional(),
    enable_webhook: z.boolean().optional(),
    webhook_url: z.string().optional(),
  }).optional(),
});

type TenantFormData = z.infer<typeof tenantSchema>;

interface TenantFormProps {
  tenantId?: string;
  mode: 'create' | 'edit' | 'view';
}

export function TenantForm({ tenantId, mode }: TenantFormProps) {
  const [tenant, setTenant] = useState<Tenant | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [apiKey, setApiKey] = useState<string>('');
  
  const { user: currentUser } = useAuth();
  const router = useRouter();

  const isViewMode = mode === 'view';
  const isCreateMode = mode === 'create';

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<TenantFormData>({
    resolver: zodResolver(tenantSchema),
    defaultValues: {
      plan: 'FREE',
      status: 'ACTIVE',
      settings: {
        default_model: 'gpt-4',
        chunk_size: 1024,
        chunk_overlap: 200,
        max_queries_per_day: 1000,
        max_storage_mb: 100,
        enable_api_access: true,
        enable_webhook: false,
      },
    },
  });

  const watchedPlan = watch('plan');
  const watchedStatus = watch('status');
  const watchedSettings = watch('settings');

  const fetchTenant = useCallback(async () => {
    if (!tenantId) return;

    try {
      setIsLoading(true);
      const tenantData = await apiClient.getTenant(tenantId);
      setTenant(tenantData);
      setApiKey(tenantData.api_key || '');
      
      // フォームに値を設定
      setValue('name', tenantData.name);
      setValue('domain', tenantData.domain);
      setValue('plan', tenantData.plan);
      setValue('status', tenantData.status);
      setValue('settings', tenantData.settings);
    } catch (err: unknown) {
      console.error('Failed to fetch tenant:', err);
      setError('テナント情報の取得に失敗しました');
    } finally {
      setIsLoading(false);
    }
  }, [tenantId, setValue]);

  useEffect(() => {
    if (tenantId && !isCreateMode) {
      fetchTenant();
    }
  }, [tenantId, isCreateMode, fetchTenant]);

  const onSubmit = async (data: TenantFormData) => {
    setIsLoading(true);
    setError(null);

    try {
      if (isCreateMode) {
        await apiClient.createTenant(data);
      } else if (tenantId) {
        await apiClient.updateTenant(tenantId, data);
      }
      
      router.push('/tenants');
    } catch (err: unknown) {
      console.error('Failed to save tenant:', err);
      
      if (err && typeof err === 'object' && 'response' in err) {
        const errorResponse = err as { response?: { data?: { error?: { message?: string } } } };
        if (errorResponse.response?.data?.error?.message) {
          setError(errorResponse.response.data.error.message);
        } else {
          setError('テナントの保存に失敗しました');
        }
      } else {
        setError('テナントの保存に失敗しました');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleRegenerateApiKey = async () => {
    if (!tenantId) return;

    if (!confirm('APIキーを再発行しますか？既存のキーは無効になります。')) {
      return;
    }

    try {
      const response = await apiClient.regenerateApiKey(tenantId);
      setApiKey(response.api_key);
      alert('APIキーが再発行されました');
    } catch (err: unknown) {
      console.error('Failed to regenerate API key:', err);
      setError('APIキーの再発行に失敗しました');
    }
  };

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      alert('クリップボードにコピーしました');
    } catch (err) {
      console.error('Failed to copy to clipboard:', err);
    }
  };


  const canEdit = currentUser?.role === 'PLATFORM_ADMIN';

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center space-x-4">
        <Button variant="ghost" size="sm" onClick={() => router.back()}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          戻る
        </Button>
        <div>
          <h1 className="text-3xl font-bold">
            {isCreateMode ? '新規テナント作成' : 
             isViewMode ? 'テナント詳細' : 'テナント編集'}
          </h1>
          <p className="text-muted-foreground">
            {isCreateMode ? '新しいテナントを作成します' : 
             isViewMode ? 'テナント情報を表示します' : 'テナント情報を編集します'}
          </p>
        </div>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <Tabs defaultValue="basic" className="space-y-6">
        <TabsList>
          <TabsTrigger value="basic">基本情報</TabsTrigger>
          <TabsTrigger value="settings">設定</TabsTrigger>
          <TabsTrigger value="api">API情報</TabsTrigger>
          <TabsTrigger value="embed">埋め込み</TabsTrigger>
        </TabsList>

        <TabsContent value="basic">
          <Card>
            <CardHeader>
              <CardTitle>基本情報</CardTitle>
              <CardDescription>
                テナントの基本情報を設定します
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="name">テナント名</Label>
                    <Input
                      id="name"
                      {...register('name')}
                      disabled={isViewMode || !canEdit}
                    />
                    {errors.name && (
                      <p className="text-sm text-red-600">{errors.name.message}</p>
                    )}
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="domain">ドメイン</Label>
                    <Input
                      id="domain"
                      {...register('domain')}
                      disabled={isViewMode || !canEdit}
                    />
                    {errors.domain && (
                      <p className="text-sm text-red-600">{errors.domain.message}</p>
                    )}
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="plan">プラン</Label>
                    <Select
                      value={watchedPlan}
                      onValueChange={(value) => setValue('plan', value as 'FREE' | 'BASIC' | 'PRO' | 'ENTERPRISE')}
                      disabled={isViewMode || !canEdit}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="プランを選択" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="FREE">Free</SelectItem>
                        <SelectItem value="BASIC">Basic</SelectItem>
                        <SelectItem value="PRO">Pro</SelectItem>
                        <SelectItem value="ENTERPRISE">Enterprise</SelectItem>
                      </SelectContent>
                    </Select>
                    {errors.plan && (
                      <p className="text-sm text-red-600">{errors.plan.message}</p>
                    )}
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="status">ステータス</Label>
                    <Select
                      value={watchedStatus}
                      onValueChange={(value) => setValue('status', value as 'ACTIVE' | 'SUSPENDED' | 'DELETED')}
                      disabled={isViewMode || !canEdit}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="ステータスを選択" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="ACTIVE">アクティブ</SelectItem>
                        <SelectItem value="SUSPENDED">停止中</SelectItem>
                        <SelectItem value="DELETED">削除済み</SelectItem>
                      </SelectContent>
                    </Select>
                    {errors.status && (
                      <p className="text-sm text-red-600">{errors.status.message}</p>
                    )}
                  </div>
                </div>

                {tenant && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2 border-t">
                    <div className="space-y-1">
                      <Label className="text-sm text-muted-foreground">作成日</Label>
                      <div className="text-sm">
                        {format(new Date(tenant.created_at), 'yyyy/MM/dd', { locale: ja })}
                      </div>
                    </div>
                  </div>
                )}

                {!isViewMode && canEdit && (
                  <div className="flex justify-end space-x-2">
                    <Button type="button" variant="outline" onClick={() => router.back()}>
                      キャンセル
                    </Button>
                    <Button type="submit" disabled={isSubmitting}>
                      <Save className="mr-2 h-4 w-4" />
                      {isSubmitting ? '保存中...' : '保存'}
                    </Button>
                  </div>
                )}
              </form>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="settings">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Settings className="mr-2 h-5 w-5" />
                テナント設定
              </CardTitle>
              <CardDescription>
                RAGシステムの動作設定を行います
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="default_model">デフォルトモデル</Label>
                  <Select
                    value={watchedSettings?.default_model || 'gpt-4'}
                    onValueChange={(value) => setValue('settings.default_model', value)}
                    disabled={isViewMode || !canEdit}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="モデルを選択" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="gpt-4">GPT-4</SelectItem>
                      <SelectItem value="gpt-3.5-turbo">GPT-3.5 Turbo</SelectItem>
                      <SelectItem value="claude-3">Claude 3</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="max_queries_per_day">1日の最大質問数</Label>
                  <Input
                    id="max_queries_per_day"
                    type="number"
                    value={watchedSettings?.max_queries_per_day || 1000}
                    onChange={(e) => setValue('settings.max_queries_per_day', parseInt(e.target.value))}
                    disabled={isViewMode || !canEdit}
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="chunk_size">チャンクサイズ</Label>
                  <Input
                    id="chunk_size"
                    type="number"
                    value={watchedSettings?.chunk_size || 1024}
                    onChange={(e) => setValue('settings.chunk_size', parseInt(e.target.value))}
                    disabled={isViewMode || !canEdit}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="chunk_overlap">チャンクオーバーラップ</Label>
                  <Input
                    id="chunk_overlap"
                    type="number"
                    value={watchedSettings?.chunk_overlap || 200}
                    onChange={(e) => setValue('settings.chunk_overlap', parseInt(e.target.value))}
                    disabled={isViewMode || !canEdit}
                  />
                </div>
              </div>

              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <Label htmlFor="enable_api_access">APIアクセス</Label>
                    <p className="text-sm text-muted-foreground">
                      API経由でのアクセスを許可します
                    </p>
                  </div>
                  <Switch
                    id="enable_api_access"
                    checked={watchedSettings?.enable_api_access || false}
                    onCheckedChange={(checked) => setValue('settings.enable_api_access', checked)}
                    disabled={isViewMode || !canEdit}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <Label htmlFor="enable_webhook">Webhook</Label>
                    <p className="text-sm text-muted-foreground">
                      Webhook通知を有効にします
                    </p>
                  </div>
                  <Switch
                    id="enable_webhook"
                    checked={watchedSettings?.enable_webhook || false}
                    onCheckedChange={(checked) => setValue('settings.enable_webhook', checked)}
                    disabled={isViewMode || !canEdit}
                  />
                </div>
              </div>

              {watchedSettings?.enable_webhook && (
                <div className="space-y-2">
                  <Label htmlFor="webhook_url">Webhook URL</Label>
                  <Input
                    id="webhook_url"
                    type="url"
                    placeholder="https://example.com/webhook"
                    value={watchedSettings?.webhook_url || ''}
                    onChange={(e) => setValue('settings.webhook_url', e.target.value)}
                    disabled={isViewMode || !canEdit}
                  />
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="api">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Key className="mr-2 h-5 w-5" />
                API情報
              </CardTitle>
              <CardDescription>
                APIキーとアクセス情報
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>APIキー</Label>
                <div className="flex items-center space-x-2">
                  <Input
                    value={apiKey}
                    readOnly
                    className="font-mono text-sm"
                  />
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => copyToClipboard(apiKey || '')}
                    disabled={!apiKey}
                  >
                    <Copy className="h-4 w-4" />
                  </Button>
                  {canEdit && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleRegenerateApiKey}
                    >
                      <Key className="h-4 w-4" />
                    </Button>
                  )}
                </div>
                <p className="text-sm text-muted-foreground">
                  このAPIキーを外部システムで使用してRAG機能にアクセスできます
                </p>
              </div>

              <Separator />

              <div className="space-y-2">
                <Label>APIエンドポイント</Label>
                <div className="p-3 bg-muted rounded-md">
                  <code className="text-sm">
                    POST https://api.rag-chatbot.com/api/v1/chats
                  </code>
                </div>
              </div>

              <div className="space-y-2">
                <Label>認証ヘッダー</Label>
                <div className="p-3 bg-muted rounded-md">
                  <code className="text-sm">
                    Authorization: Bearer {apiKey ? `${apiKey.slice(0, 20)}...` : 'APIキーが設定されていません'}
                  </code>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="embed">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Download className="mr-2 h-5 w-5" />
                埋め込みコード
              </CardTitle>
              <CardDescription>
                ウェブサイトにチャットウィジェットを埋め込むためのコード
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>埋め込みスニペット</Label>
                <Textarea
                  value={`<!-- チャットウィジェット埋め込みコード -->
<script>
  (function(w,d,s,o,f,js,fjs){
    w['RAGChatWidget']=o;w[o]=w[o]||function(){(w[o].q=w[o].q||[]).push(arguments)};
    js=d.createElement(s),fjs=d.getElementsByTagName(s)[0];
    js.id=o;js.src=f;js.async=1;fjs.parentNode.insertBefore(js,fjs);
  }(window,document,'script','ragChat','https://cdn.rag-chatbot.com/widget.js'));
  
  ragChat('init', {
    tenantId: '${tenantId || 'YOUR_TENANT_ID'}',
    apiKey: '${apiKey ? `${apiKey.slice(0, 20)}...` : 'YOUR_API_KEY'}',
    theme: 'light',
    position: 'bottom-right'
  });
</script>`}
                  readOnly
                  className="font-mono text-sm min-h-[200px]"
                />
                <div className="flex justify-end">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => copyToClipboard(`<!-- チャットウィジェット埋め込みコード -->
<script>
  (function(w,d,s,o,f,js,fjs){
    w['RAGChatWidget']=o;w[o]=w[o]||function(){(w[o].q=w[o].q||[]).push(arguments)};
    js=d.createElement(s),fjs=d.getElementsByTagName(s)[0];
    js.id=o;js.src=f;js.async=1;fjs.parentNode.insertBefore(js,fjs);
  }(window,document,'script','ragChat','https://cdn.rag-chatbot.com/widget.js'));
  
  ragChat('init', {
    tenantId: '${tenantId || 'YOUR_TENANT_ID'}',
    apiKey: '${apiKey || 'YOUR_API_KEY'}',
    theme: 'light',
    position: 'bottom-right'
  });
</script>`)}
                  >
                    <Copy className="mr-2 h-4 w-4" />
                    コピー
                  </Button>
                </div>
              </div>

              <Alert>
                <AlertDescription>
                  このコードをウェブサイトのHTMLに貼り付けると、チャットウィジェットが表示されます。
                </AlertDescription>
              </Alert>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
