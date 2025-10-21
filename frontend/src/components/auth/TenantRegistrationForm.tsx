/**
 * テナント登録フォームコンポーネント
 * 
 * このファイルはテナント登録用のフォームコンポーネントを定義します。
 * テナント作成とテナント管理者ユーザー作成を同時に行うためのフォームです。
 * 
 * 主な機能:
 * - テナント情報の入力（テナント名、ドメイン）
 * - テナント管理者情報の入力（メール、ユーザー名、パスワード）
 * - 入力値のバリデーション
 * - エラーハンドリング
 * - 登録完了後の処理
 */

'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { apiClient, TenantRegistrationRequest } from '@/lib/api';
import { Loader2, Eye, EyeOff, Building2 } from 'lucide-react';

const tenantRegistrationSchema = z.object({
  tenant_name: z.string()
    .min(2, 'テナント名は2文字以上で入力してください')
    .max(255, 'テナント名は255文字以内で入力してください'),
  tenant_domain: z.string()
    .min(3, 'テナント識別子は3文字以上で入力してください')
    .max(255, 'テナント識別子は255文字以内で入力してください')
    .regex(/^[a-zA-Z0-9_-]+$/, 'テナント識別子は英数字、ハイフン、アンダースコアのみ使用可能です'),
  admin_email: z.string().email('有効なメールアドレスを入力してください'),
  admin_username: z.string()
    .min(3, 'ユーザー名は3文字以上で入力してください')
    .max(100, 'ユーザー名は100文字以内で入力してください')
    .regex(/^[a-zA-Z0-9_]+$/, 'ユーザー名は英数字とアンダースコアのみ使用可能です'),
  admin_password: z.string()
    .min(8, 'パスワードは8文字以上で入力してください')
    .regex(/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/, 'パスワードには大文字、小文字、数字を含める必要があります'),
  confirm_password: z.string().min(8, 'パスワード確認を入力してください'),
}).refine((data) => data.admin_password === data.confirm_password, {
  message: 'パスワードが一致しません',
  path: ['confirm_password'],
});

type TenantRegistrationFormData = z.infer<typeof tenantRegistrationSchema>;

export function TenantRegistrationForm() {
  /**
   * テナント登録フォームコンポーネント
   * 
   * テナント作成とテナント管理者ユーザー作成を同時に行うフォームです。
   * バリデーション、エラーハンドリング、登録処理を統合的に管理します。
   */
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  
  const router = useRouter();

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<TenantRegistrationFormData>({
    resolver: zodResolver(tenantRegistrationSchema),
  });

  const onSubmit = async (data: TenantRegistrationFormData) => {
    /**
     * テナント登録フォーム送信処理
     * 
     * 引数:
     *   data: テナント登録フォームデータ
     * 
     * 戻り値:
     *   Promise<void>: 非同期処理
     */
    setIsLoading(true);
    setError(null);

    try {
      const registrationData: TenantRegistrationRequest = {
        tenant_name: data.tenant_name,
        tenant_domain: data.tenant_domain,
        admin_email: data.admin_email,
        admin_username: data.admin_username,
        admin_password: data.admin_password,
      };
      
      console.log('送信するデータ:', registrationData);
      
      const response = await apiClient.registerTenant(registrationData);
      
      // 登録成功時のダイアログ表示
      const confirmed = window.confirm(
        `テナント登録が完了しました。\n\nテナント名: ${response.tenant_name}\n管理者メール: ${response.admin_email}\n\n確認メールを送付いたしました。\nメール内のリンクをクリックしてアカウントを有効化してください。`
      );
      
      if (confirmed) {
        // フォームをリセット
        reset();
        
        // ログイン画面に遷移
        router.push('/login');
      }
      
    } catch (err: any) {
      console.error('Tenant registration error:', err);
      
      if (err.response?.data?.detail) {
        setError(err.response.data.detail);
      } else if (err.message) {
        setError(err.message);
      } else {
        setError('テナント登録に失敗しました。もう一度お試しください。');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card className="w-full max-w-md mx-auto">
      <CardHeader className="space-y-1">
        <div className="flex items-center justify-center mb-2">
          <Building2 className="h-8 w-8 text-blue-600" />
        </div>
        <CardTitle className="text-2xl text-center">テナント管理者登録</CardTitle>
        <CardDescription className="text-center">
          新しいテナントとテナント管理者アカウントを同時に登録します
        </CardDescription>
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mt-3">
          <p className="text-sm text-blue-800">
            <strong>テナントについて：</strong><br/>
            • <strong>テナント名</strong>：表示用の名前（同じ名前でも複数登録可能）<br/>
            • <strong>テナント識別子</strong>：システム内での一意識別子（英数字、ハイフン、アンダースコアのみ）
          </p>
        </div>
      </CardHeader>
      
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 p-6">
        {error && (
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {/* テナント情報 */}
        <div className="space-y-2">
          <Label htmlFor="tenant_name">テナント名</Label>
          <Input
            id="tenant_name"
            type="text"
            placeholder="例: 株式会社サンプル"
            {...register('tenant_name')}
            className={errors.tenant_name ? 'border-red-500' : ''}
          />
          {errors.tenant_name && (
            <p className="text-sm text-red-500">{errors.tenant_name.message}</p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="tenant_domain">テナント識別子</Label>
          <Input
            id="tenant_domain"
            type="text"
            placeholder="例: company-hr, my-company, project_alpha"
            {...register('tenant_domain')}
            className={errors.tenant_domain ? 'border-red-500' : ''}
          />
          {errors.tenant_domain && (
            <p className="text-sm text-red-500">{errors.tenant_domain.message}</p>
          )}
        </div>

        {/* 管理者情報 */}
        <div className="space-y-2">
          <Label htmlFor="admin_email">管理者メールアドレス</Label>
          <Input
            id="admin_email"
            type="email"
            placeholder="admin@example.com"
            {...register('admin_email')}
            className={errors.admin_email ? 'border-red-500' : ''}
          />
          {errors.admin_email && (
            <p className="text-sm text-red-500">{errors.admin_email.message}</p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="admin_username">管理者ユーザー名</Label>
          <Input
            id="admin_username"
            type="text"
            placeholder="admin_user"
            {...register('admin_username')}
            className={errors.admin_username ? 'border-red-500' : ''}
          />
          {errors.admin_username && (
            <p className="text-sm text-red-500">{errors.admin_username.message}</p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="admin_password">パスワード</Label>
          <div className="relative">
            <Input
              id="admin_password"
              type={showPassword ? 'text' : 'password'}
              placeholder="8文字以上、大文字・小文字・数字を含む"
              {...register('admin_password')}
              className={errors.admin_password ? 'border-red-500' : ''}
            />
            <Button
              type="button"
              variant="ghost"
              size="sm"
              className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
              onClick={() => setShowPassword(!showPassword)}
            >
              {showPassword ? (
                <EyeOff className="h-4 w-4" />
              ) : (
                <Eye className="h-4 w-4" />
              )}
            </Button>
          </div>
          {errors.admin_password && (
            <p className="text-sm text-red-500">{errors.admin_password.message}</p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="confirm_password">パスワード確認</Label>
          <div className="relative">
            <Input
              id="confirm_password"
              type={showConfirmPassword ? 'text' : 'password'}
              placeholder="パスワードを再入力"
              {...register('confirm_password')}
              className={errors.confirm_password ? 'border-red-500' : ''}
            />
            <Button
              type="button"
              variant="ghost"
              size="sm"
              className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
              onClick={() => setShowConfirmPassword(!showConfirmPassword)}
            >
              {showConfirmPassword ? (
                <EyeOff className="h-4 w-4" />
              ) : (
                <Eye className="h-4 w-4" />
              )}
            </Button>
          </div>
          {errors.confirm_password && (
            <p className="text-sm text-red-500">{errors.confirm_password.message}</p>
          )}
        </div>

        <Button type="submit" className="w-full" disabled={isLoading}>
          {isLoading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              登録中...
            </>
          ) : (
            <>
              <Building2 className="mr-2 h-4 w-4" />
              テナント管理者を登録
            </>
          )}
        </Button>
      </form>
    </Card>
  );
}
