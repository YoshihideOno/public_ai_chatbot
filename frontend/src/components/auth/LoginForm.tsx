/**
 * 認証フォームコンポーネント（ログイン・アカウント登録）
 * 
 * このファイルはユーザーのログインとアカウント登録用のフォームコンポーネントを定義します。
 * React Hook FormとZodを使用したバリデーション、エラーハンドリング、
 * パスワード表示切り替え、タブ切り替えなどの機能を提供します。
 * 
 * 主な機能:
 * - ログイン・アカウント登録フォームの表示・操作
 * - 入力値のバリデーション
 * - パスワード表示切り替え
 * - エラーメッセージの表示
 * - 認証状態の管理
 * - 認証後の画面遷移
 */

'use client';

import React, { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useAuth } from '@/contexts/AuthContext';
import { apiClient } from '@/lib/api';
import { TenantRegistrationForm } from './TenantRegistrationForm';
import { Loader2, Eye, EyeOff, LogIn, Building2 } from 'lucide-react';

const loginSchema = z.object({
  email: z.string().email('有効なメールアドレスを入力してください'),
  password: z.string().min(1, 'パスワードを入力してください'),
});

type LoginFormData = z.infer<typeof loginSchema>;

export function LoginForm() {
  /**
   * 認証フォームコンポーネント
   * 
   * ユーザーのログインとアカウント登録処理を行うフォームコンポーネントです。
   * タブ切り替えでログインとアカウント登録を切り替え、それぞれのバリデーション、
   * エラーハンドリング、認証状態管理を統合的に処理します。
   */
  const [activeTab, setActiveTab] = useState('login');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  
  const { login } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();

  // URLクエリパラメータからタブの初期状態を設定
  useEffect(() => {
    const tab = searchParams.get('tab');
    if (tab === 'register') {
      setActiveTab('register');
    }
  }, [searchParams]);

  const loginForm = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  });


  const onLoginSubmit = async (data: LoginFormData) => {
    /**
     * ログインフォーム送信処理
     * 
     * 引数:
     *   data: ログインフォームデータ（メール、パスワード）
     * 
     * 戻り値:
     *   Promise<void>: 非同期処理
     * 
     * 例外:
     *   Error: ログイン失敗時のエラー
     */
    setIsLoading(true);
    setError(null);

    try {
      await login(data);
      router.push('/dashboard');
    } catch (err: unknown) {
      console.error('Login error:', err);
      
      if (err && typeof err === 'object' && 'response' in err) {
        const errorResponse = err as { response?: { data?: { error?: { message?: string } } }; message?: string };
        if (errorResponse.response?.data?.error?.message) {
          setError(errorResponse.response.data.error.message);
        } else if (errorResponse.message) {
          setError(errorResponse.message);
        } else {
          setError('ログインに失敗しました。メールアドレスとパスワードを確認してください。');
        }
      } else if (err && typeof err === 'object' && 'message' in err) {
        setError((err as Error).message);
      } else {
        setError('ログインに失敗しました。メールアドレスとパスワードを確認してください。');
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
            RAG AI Chatbot Platform
          </h2>
          <p className="mt-2 text-sm text-gray-600">
            アカウントにログインまたは新規登録してください
          </p>
        </div>

        <Card>
          <CardHeader>
            <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="login" className="flex items-center gap-2">
                  <LogIn className="h-4 w-4" />
                  ログイン
                </TabsTrigger>
                <TabsTrigger value="register" className="flex items-center gap-2">
                  <Building2 className="h-4 w-4" />
                  アカウント登録
                </TabsTrigger>
              </TabsList>

              <TabsContent value="login" className="space-y-4">
                <div>
                  <CardTitle>ログイン</CardTitle>
                  <CardDescription>
                    メールアドレスとパスワードを入力してください
                  </CardDescription>
                </div>
                <form onSubmit={loginForm.handleSubmit(onLoginSubmit)} className="space-y-4">
                  {error && (
                    <Alert variant="destructive">
                      <AlertDescription>{error}</AlertDescription>
                    </Alert>
                  )}

                  <div className="space-y-2">
                    <Label htmlFor="login-email">メールアドレス</Label>
                    <Input
                      id="login-email"
                      type="email"
                      placeholder="user@example.com"
                      {...loginForm.register('email')}
                      disabled={isLoading}
                    />
                    {loginForm.formState.errors.email && (
                      <p className="text-sm text-red-600">{loginForm.formState.errors.email.message}</p>
                    )}
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="login-password">パスワード</Label>
                    <div className="relative">
                      <Input
                        id="login-password"
                        type={showPassword ? 'text' : 'password'}
                        placeholder="パスワードを入力"
                        {...loginForm.register('password')}
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
                    {loginForm.formState.errors.password && (
                      <p className="text-sm text-red-600">{loginForm.formState.errors.password.message}</p>
                    )}
                  </div>

                  <Button
                    type="submit"
                    className="w-full"
                    disabled={isLoading}
                  >
                    {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                    {isLoading ? 'ログイン中...' : 'ログイン'}
                  </Button>
                </form>
              </TabsContent>

              <TabsContent value="register">
                <TenantRegistrationForm />
              </TabsContent>
            </Tabs>
          </CardHeader>
        </Card>

        {activeTab === 'login' && (
          <div className="text-center">
            <p className="text-sm text-gray-600">
              パスワードを忘れた場合は、
              <Link href="/password-reset">
                <Button variant="link" className="p-0 h-auto text-sm">
                  こちらをクリック
                </Button>
              </Link>
            </p>
          </div>
        )}
      </div>
    </div>
  );
}