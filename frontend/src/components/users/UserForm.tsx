/**
 * ユーザーフォームコンポーネント
 * 
 * このファイルはユーザー情報の表示・編集・作成を行うフォームコンポーネントを定義します。
 * React Hook FormとZodを使用したバリデーション、エラーハンドリング、
 * ロール管理などの機能を提供します。
 * 
 * 主な機能:
 * - ユーザー情報の表示・編集
 * - 新規ユーザー作成
 * - 入力値のバリデーション
 * - ロール管理
 * - テナント関連付け
 * - アクティブ状態管理
 */

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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { apiClient, User, ApiError } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import { 
  ArrowLeft, 
  Save, 
  Eye,
  EyeOff
} from 'lucide-react';
import { format } from 'date-fns';
import { ja } from 'date-fns/locale';

const userSchema = z.object({
  email: z.string().email('有効なメールアドレスを入力してください'),
  username: z.string().min(2, 'ユーザー名は2文字以上である必要があります'),
  password: z.string().min(8, 'パスワードは8文字以上である必要があります').optional(),
  role: z.enum(['PLATFORM_ADMIN', 'TENANT_ADMIN', 'OPERATOR', 'AUDITOR']),
  is_active: z.boolean(),
});

type UserFormData = z.infer<typeof userSchema>;

interface UserFormProps {
  userId?: string | number;
  mode: 'create' | 'edit' | 'view';
}

export function UserForm({ userId, mode }: UserFormProps) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showPassword, setShowPassword] = useState(false);
  
  const { user: currentUser } = useAuth();
  const router = useRouter();

  const isViewMode = mode === 'view';
  const isCreateMode = mode === 'create';

  const {
    register,
    handleSubmit,
    setValue,
    reset,
    watch,
    trigger,
    setError: setFormError,
    formState: { errors, isSubmitting },
  } = useForm<UserFormData>({
    resolver: zodResolver(userSchema),
    mode: 'onBlur', // フォーカスを外した時点でバリデーションを実行
    reValidateMode: 'onBlur', // 再バリデーションもフォーカスを外した時点で実行
    defaultValues: {
      email: '',
      username: '',
      role: 'OPERATOR',
      is_active: true,
    },
  });

  const watchedRole = watch('role');
  const watchedIsActive = watch('is_active');

  const fetchUser = useCallback(async () => {
    if (!userId) return;

    try {
      setIsLoading(true);
      const userData = await apiClient.getUser(userId);
      setUser(userData);
      
      // フォームに値を設定（resetメソッドを使用して確実に初期値を設定）
      reset({
        email: userData.email,
        username: userData.username,
        role: userData.role,
        is_active: userData.is_active,
        password: undefined, // 編集時はパスワードは未設定
      });
    } catch (err: unknown) {
      console.error('Failed to fetch user:', err);
      setError('ユーザー情報の取得に失敗しました');
    } finally {
      setIsLoading(false);
    }
  }, [userId, reset]);

  useEffect(() => {
    if (userId && !isCreateMode) {
      fetchUser();
    }
  }, [userId, isCreateMode, fetchUser]);

  const onSubmit = async (data: UserFormData) => {
    setIsLoading(true);
    setError(null);

    try {
      if (isCreateMode) {
        await apiClient.createUser(data);
      } else if (userId) {
        // 自分自身かつ管理者以外は /users/me に送る（ロールは送らない）
        const isAdmin = currentUser?.role === 'PLATFORM_ADMIN' || currentUser?.role === 'TENANT_ADMIN';
        const payload: Partial<User> = { ...data } as unknown as Partial<User>;
        if (!canChangeRole) {
          // 型安全にroleを取り除く
          const tmp = payload as Partial<User> & { role?: User['role'] };
          if ('role' in tmp) {
            delete (tmp as { role?: unknown }).role;
          }
        }
        if (!isAdmin && isSelf) {
          await apiClient.updateCurrentUser(payload);
        } else {
          await apiClient.updateUser(userId, payload);
        }
      }
      
      router.push('/users');
    } catch (err: unknown) {
      console.error('Failed to save user:', err);
      
      if (err && typeof err === 'object' && 'response' in err) {
        const axiosError = err as { response?: { status?: number; data?: any } };
        const message: string | undefined = axiosError.response?.data?.detail || axiosError.response?.data?.error?.message;
        // 重複メールの明示エラー
        if (axiosError.response?.status === 400 && message && message.toLowerCase().includes('email')) {
          setFormError('email', { type: 'manual', message: 'このメールアドレスは既に登録されています' });
          setError('入力内容を確認してください');
        } else {
          setError(message || 'ユーザーの保存に失敗しました');
        }
      } else if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('ユーザーの保存に失敗しました');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const isSelf = user && currentUser && String(user.id) === String(currentUser.id);
  const canEdit = (currentUser?.role === 'PLATFORM_ADMIN') || 
                  (currentUser?.role === 'TENANT_ADMIN' && user?.role !== 'PLATFORM_ADMIN') ||
                  Boolean(isSelf);
  // ロール変更可否: プラットフォーム管理者は可。テナント管理者は対象が管理者でない場合に限り可。
  const canChangeRole = (currentUser?.role === 'PLATFORM_ADMIN') ||
    (currentUser?.role === 'TENANT_ADMIN' && (user?.role !== 'PLATFORM_ADMIN' && user?.role !== 'TENANT_ADMIN'));

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
            {isCreateMode ? '新規ユーザー作成' : 
             isViewMode ? 'ユーザー詳細' : 'ユーザー編集'}
          </h1>
          <p className="text-muted-foreground">
            {isCreateMode ? '新しいユーザーを作成します' : 
             isViewMode ? 'ユーザー情報を表示します' : 'ユーザー情報を編集します'}
          </p>
        </div>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <div className="grid grid-cols-1 gap-6">
        {/* メイン情報 */}
        <Card>
          <CardHeader>
            <CardTitle>基本情報</CardTitle>
            <CardDescription>
              ユーザーの基本情報を設定します
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-6" autoComplete="off">
                {/* ブラウザの自動入力抑止用ダミーフィールド */}
                <input type="text" name="prevent_autofill_username" autoComplete="username" style={{ display: 'none' }} tabIndex={-1} />
                <input type="password" name="prevent_autofill_password" autoComplete="new-password" style={{ display: 'none' }} tabIndex={-1} />
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="username">ユーザー名</Label>
                    <Input
                      id="username"
                      {...register('username')}
                      disabled={isViewMode || !canEdit}
                      autoComplete="off"
                      placeholder="例: yamada_taro"
                    />
                    {!errors.username && (
                      <p className="text-xs text-muted-foreground">英数字とアンダースコアのみ。3〜100文字推奨</p>
                    )}
                    {errors.username && (
                      <p className="text-sm text-red-600">{errors.username.message}</p>
                    )}
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="email">メールアドレス</Label>
                    <Input
                      id="email"
                      type="email"
                      {...register('email', {
                        onBlur: () => trigger('email'), // フォーカスを外した時点でバリデーションを実行
                      })}
                      disabled={isViewMode || !canEdit}
                      autoComplete="off"
                      placeholder="例: user@example.com"
                      aria-invalid={errors.email ? 'true' : 'false'}
                    />
                    {errors.email && (
                      <p className="text-sm text-red-600" role="alert">{errors.email.message}</p>
                    )}
                  </div>
                </div>

                {/* ロール説明はロールセレクトの直下に表示へ移設 */}

                {isCreateMode && (
                  <div className="space-y-2">
                    <Label htmlFor="password">パスワード</Label>
                    <div className="relative">
                      <Input
                        id="password"
                        type={showPassword ? 'text' : 'password'}
                        {...register('password')}
                        disabled={isViewMode || !canEdit}
                        autoComplete="new-password"
                        placeholder="8文字以上（大文字・小文字・数字を含む推奨）"
                      />
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                        onClick={() => setShowPassword(!showPassword)}
                        disabled={isViewMode || !canEdit}
                      >
                        {showPassword ? (
                          <EyeOff className="h-4 w-4" />
                        ) : (
                          <Eye className="h-4 w-4" />
                        )}
                      </Button>
                    </div>
                    {errors.password ? (
                      <p className="text-sm text-red-600">{errors.password.message}</p>
                    ) : (
                      <p className="text-xs text-muted-foreground">例: Abcdef12</p>
                    )}
                  </div>
                )}

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="role">ロール</Label>
                    <Select
                      value={watchedRole}
                      onValueChange={(value) => setValue('role', value as UserFormData['role'])}
                      disabled={isViewMode || !canChangeRole}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="ロールを選択" />
                      </SelectTrigger>
                      <SelectContent>
                        {/* 常に基本ロールは表示 */}
                        <SelectItem value="OPERATOR">運用者</SelectItem>
                        <SelectItem value="AUDITOR">監査者</SelectItem>

                        {/* プラットフォーム管理者は上位ロールも編集可 */}
                        {currentUser?.role === 'PLATFORM_ADMIN' && (
                          <>
                            <SelectItem value="TENANT_ADMIN">テナント管理者</SelectItem>
                            <SelectItem value="PLATFORM_ADMIN">プラットフォーム管理者</SelectItem>
                          </>
                        )}

                        {/* 編集不可のケースでも、現在のロールがリストに無い場合は表示（disabled） */}
                        {currentUser?.role !== 'PLATFORM_ADMIN' && watchedRole === 'TENANT_ADMIN' && (
                          <SelectItem value="TENANT_ADMIN" disabled>
                            テナント管理者
                          </SelectItem>
                        )}
                        {currentUser?.role !== 'PLATFORM_ADMIN' && watchedRole === 'PLATFORM_ADMIN' && (
                          <SelectItem value="PLATFORM_ADMIN" disabled>
                            プラットフォーム管理者
                          </SelectItem>
                        )}
                      </SelectContent>
                    </Select>
                    {/* ロール説明（ロールセレクト直下） */}
                    <div className="text-xs text-muted-foreground">
                      {watchedRole === 'PLATFORM_ADMIN' && '全システムの管理権限を持ちます'}
                      {watchedRole === 'TENANT_ADMIN' && '自テナントの管理権限を持ちます'}
                      {watchedRole === 'OPERATOR' && 'コンテンツ管理と統計確認ができます'}
                      {watchedRole === 'AUDITOR' && 'ログ閲覧と監査データエクスポートができます'}
                    </div>
                    {errors.role && (
                      <p className="text-sm text-red-600">{errors.role.message}</p>
                    )}
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="is_active">ステータス</Label>
                    <div className="flex items-center space-x-2">
                      <Switch
                        id="is_active"
                        checked={watchedIsActive}
                        onCheckedChange={(checked) => setValue('is_active', checked)}
                        disabled={isViewMode || !canEdit}
                      />
                      <Label htmlFor="is_active">
                        {watchedIsActive ? 'アクティブ' : '非アクティブ'}
                      </Label>
                    </div>
                  </div>
                </div>

                {/* 作成日・最終ログイン（基本情報内に移動） */}
                {user && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2 border-t">
                    <div className="space-y-1">
                      <Label className="text-sm text-muted-foreground">作成日</Label>
                      <div className="text-sm">
                        {format(new Date(user.created_at), 'yyyy/MM/dd', { locale: ja })}
                      </div>
                    </div>
                    <div className="space-y-1">
                      <Label className="text-sm text-muted-foreground">最終ログイン</Label>
                      <div className="text-sm">
                        {user.last_login_at ? (
                          format(new Date(user.last_login_at), 'yyyy/MM/dd HH:mm', { locale: ja })
                        ) : (
                          <span className="text-muted-foreground">未ログイン</span>
                        )}
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
      </div>
    </div>
  );
}
