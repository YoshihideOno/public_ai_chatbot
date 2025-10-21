/**
 * パスワードリセットフォームコンポーネント
 * 
 * このファイルはパスワードリセット用のフォームコンポーネントを定義します。
 * React Hook FormとZodを使用したバリデーション、エラーハンドリング、
 * メール送信とパスワード更新の機能を提供します。
 * 
 * 主な機能:
 * - パスワードリセット要求フォーム
 * - パスワードリセット確認フォーム
 * - 入力値のバリデーション
 * - エラーメッセージの表示
 * - 成功メッセージの表示
 */

'use client';

import React, { useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { apiClient } from '@/lib/api';
import { Loader2, Eye, EyeOff, CheckCircle, ArrowLeft } from 'lucide-react';
import Link from 'next/link';

/**
 * APIエラーレスポンスの型定義
 * 
 * APIからのエラーレスポンスの構造を定義します。
 * エラーハンドリング時に型安全性を確保するために使用されます。
 */
interface ApiErrorResponse {
  response?: {
    data?: {
      error?: {
        message?: string;
      };
    };
  };
  message?: string;
}

const requestResetSchema = z.object({
  email: z.string().email('有効なメールアドレスを入力してください'),
});

const confirmResetSchema = z.object({
  password: z.string().min(8, 'パスワードは8文字以上で入力してください'),
  confirmPassword: z.string().min(8, 'パスワード確認を入力してください'),
}).refine((data) => data.password === data.confirmPassword, {
  message: 'パスワードが一致しません',
  path: ['confirmPassword'],
});

type RequestResetFormData = z.infer<typeof requestResetSchema>;
type ConfirmResetFormData = z.infer<typeof confirmResetSchema>;

export function PasswordResetForm() {
  /**
   * パスワードリセットフォームコンポーネント
   * 
   * パスワードリセットの要求と確認を行うフォームコンポーネントです。
   * URLパラメータにトークンがある場合は確認フォームを表示し、
   * ない場合は要求フォームを表示します。
   */
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get('token');
  
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const requestForm = useForm<RequestResetFormData>({
    resolver: zodResolver(requestResetSchema),
  });

  const confirmForm = useForm<ConfirmResetFormData>({
    resolver: zodResolver(confirmResetSchema),
  });

  const onRequestSubmit = async (data: RequestResetFormData) => {
    /**
     * パスワードリセット要求送信処理
     * 
     * 引数:
     *   data: パスワードリセット要求フォームデータ（メール）
     * 
     * 戻り値:
     *   Promise<void>: 非同期処理
     * 
     * 例外:
     *   Error: パスワードリセット要求失敗時のエラー
     */
    setIsLoading(true);
    setError(null);
    setSuccess(null);

    try {
      await apiClient.requestPasswordReset(data.email);
      setSuccess('パスワードリセットのメールを送信しました。メールボックスをご確認ください。');
    } catch (err: unknown) {
      console.error('Password reset request error:', err);
      
      const apiError = err as ApiErrorResponse;
      if (apiError.response?.data?.error?.message) {
        setError(apiError.response.data.error.message);
      } else if (apiError.message) {
        setError(apiError.message);
      } else {
        setError('パスワードリセット要求に失敗しました。');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const onConfirmSubmit = async (data: ConfirmResetFormData) => {
    /**
     * パスワードリセット確認送信処理
     * 
     * 引数:
     *   data: パスワードリセット確認フォームデータ（パスワード、パスワード確認）
     * 
     * 戻り値:
     *   Promise<void>: 非同期処理
     * 
     * 例外:
     *   Error: パスワードリセット確認失敗時のエラー
     */
    if (!token) {
      setError('無効なリセットトークンです。');
      return;
    }

    setIsLoading(true);
    setError(null);
    setSuccess(null);

    try {
      await apiClient.confirmPasswordReset(token, data.password);
      setSuccess('パスワードが正常に更新されました。ログイン画面に戻ってログインしてください。');
      
      // 3秒後にログイン画面にリダイレクト
      setTimeout(() => {
        router.push('/login');
      }, 3000);
    } catch (err: unknown) {
      console.error('Password reset confirm error:', err);
      
      const apiError = err as ApiErrorResponse;
      if (apiError.response?.data?.error?.message) {
        setError(apiError.response.data.error.message);
      } else if (apiError.message) {
        setError(apiError.message);
      } else {
        setError('パスワードの更新に失敗しました。');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <div className="mx-auto h-12 w-12 rounded-lg bg-primary flex items-center justify-center">
            <span className="text-primary-foreground font-bold text-xl">RAG</span>
          </div>
          <h2 className="mt-6 text-3xl font-bold text-gray-900">
            {token ? 'パスワードリセット' : 'パスワードを忘れた場合'}
          </h2>
          <p className="mt-2 text-sm text-gray-600">
            {token 
              ? '新しいパスワードを設定してください'
              : 'メールアドレスを入力してパスワードリセットのメールを送信します'
            }
          </p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>
              {token ? '新しいパスワードを設定' : 'パスワードリセット要求'}
            </CardTitle>
            <CardDescription>
              {token 
                ? '新しいパスワードを入力してください'
                : '登録済みのメールアドレスを入力してください'
              }
            </CardDescription>
          </CardHeader>
          <CardContent>
            {token ? (
              // パスワードリセット確認フォーム
              <form onSubmit={confirmForm.handleSubmit(onConfirmSubmit)} className="space-y-4">
                {error && (
                  <Alert variant="destructive">
                    <AlertDescription>{error}</AlertDescription>
                  </Alert>
                )}

                {success && (
                  <Alert className="border-green-200 bg-green-50">
                    <CheckCircle className="h-4 w-4 text-green-600" />
                    <AlertDescription className="text-green-800">{success}</AlertDescription>
                  </Alert>
                )}

                <div className="space-y-2">
                  <Label htmlFor="password">新しいパスワード</Label>
                  <div className="relative">
                    <Input
                      id="password"
                      type={showPassword ? 'text' : 'password'}
                      placeholder="新しいパスワードを入力（8文字以上）"
                      {...confirmForm.register('password')}
                      disabled={isLoading}
                    />
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                      onClick={() => setShowPassword(!showPassword)}
                      disabled={isLoading}
                    >
                      {showPassword ? (
                        <EyeOff className="h-4 w-4" />
                      ) : (
                        <Eye className="h-4 w-4" />
                      )}
                    </Button>
                  </div>
                  {confirmForm.formState.errors.password && (
                    <p className="text-sm text-red-600">{confirmForm.formState.errors.password.message}</p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="confirmPassword">パスワード確認</Label>
                  <div className="relative">
                    <Input
                      id="confirmPassword"
                      type={showConfirmPassword ? 'text' : 'password'}
                      placeholder="パスワードを再入力"
                      {...confirmForm.register('confirmPassword')}
                      disabled={isLoading}
                    />
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                      onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                      disabled={isLoading}
                    >
                      {showConfirmPassword ? (
                        <EyeOff className="h-4 w-4" />
                      ) : (
                        <Eye className="h-4 w-4" />
                      )}
                    </Button>
                  </div>
                  {confirmForm.formState.errors.confirmPassword && (
                    <p className="text-sm text-red-600">{confirmForm.formState.errors.confirmPassword.message}</p>
                  )}
                </div>

                <Button
                  type="submit"
                  className="w-full"
                  disabled={isLoading}
                >
                  {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  {isLoading ? '更新中...' : 'パスワードを更新'}
                </Button>
              </form>
            ) : (
              // パスワードリセット要求フォーム
              <form onSubmit={requestForm.handleSubmit(onRequestSubmit)} className="space-y-4">
                {error && (
                  <Alert variant="destructive">
                    <AlertDescription>{error}</AlertDescription>
                  </Alert>
                )}

                {success && (
                  <Alert className="border-green-200 bg-green-50">
                    <CheckCircle className="h-4 w-4 text-green-600" />
                    <AlertDescription className="text-green-800">{success}</AlertDescription>
                  </Alert>
                )}

                <div className="space-y-2">
                  <Label htmlFor="email">メールアドレス</Label>
                  <Input
                    id="email"
                    type="email"
                    placeholder="user@example.com"
                    {...requestForm.register('email')}
                    disabled={isLoading}
                  />
                  {requestForm.formState.errors.email && (
                    <p className="text-sm text-red-600">{requestForm.formState.errors.email.message}</p>
                  )}
                </div>

                <Button
                  type="submit"
                  className="w-full"
                  disabled={isLoading}
                >
                  {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  {isLoading ? '送信中...' : 'リセットメールを送信'}
                </Button>
              </form>
            )}
          </CardContent>
        </Card>

        <div className="text-center">
          <Link href="/login">
            <Button variant="link" className="p-0 h-auto text-sm">
              <ArrowLeft className="mr-1 h-3 w-3" />
              ログイン画面に戻る
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
}
