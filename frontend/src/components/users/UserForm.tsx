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

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Separator } from '@/components/ui/separator';
import { apiClient, User } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import { 
  ArrowLeft, 
  Save, 
  User as UserIcon,
  Mail,
  Calendar,
  Shield,
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
  userId?: number;
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
    watch,
    formState: { errors, isSubmitting },
  } = useForm<UserFormData>({
    resolver: zodResolver(userSchema),
    defaultValues: {
      role: 'OPERATOR',
      is_active: true,
    },
  });

  const watchedRole = watch('role');
  const watchedIsActive = watch('is_active');

  useEffect(() => {
    if (userId && !isCreateMode) {
      fetchUser();
    }
  }, [userId, isCreateMode]);

  const fetchUser = async () => {
    if (!userId) return;

    try {
      setIsLoading(true);
      const userData = await apiClient.getUser(userId);
      setUser(userData);
      
      // フォームに値を設定
      setValue('email', userData.email);
      setValue('username', userData.username);
      setValue('role', userData.role);
      setValue('is_active', userData.is_active);
    } catch (err: any) {
      console.error('Failed to fetch user:', err);
      setError('ユーザー情報の取得に失敗しました');
    } finally {
      setIsLoading(false);
    }
  };

  const onSubmit = async (data: UserFormData) => {
    setIsLoading(true);
    setError(null);

    try {
      if (isCreateMode) {
        await apiClient.createUser(data);
      } else if (userId) {
        await apiClient.updateUser(userId, data);
      }
      
      router.push('/users');
    } catch (err: any) {
      console.error('Failed to save user:', err);
      
      if (err.response?.data?.error?.message) {
        setError(err.response.data.error.message);
      } else {
        setError('ユーザーの保存に失敗しました');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const getRoleBadgeVariant = (role: string) => {
    switch (role) {
      case 'PLATFORM_ADMIN':
        return 'destructive';
      case 'TENANT_ADMIN':
        return 'default';
      case 'OPERATOR':
        return 'secondary';
      case 'AUDITOR':
        return 'outline';
      default:
        return 'outline';
    }
  };

  const getRoleLabel = (role: string) => {
    switch (role) {
      case 'PLATFORM_ADMIN':
        return 'プラットフォーム管理者';
      case 'TENANT_ADMIN':
        return 'テナント管理者';
      case 'OPERATOR':
        return '運用者';
      case 'AUDITOR':
        return '監査者';
      default:
        return role;
    }
  };

  const canEdit = currentUser?.role === 'PLATFORM_ADMIN' || 
                  (currentUser?.role === 'TENANT_ADMIN' && user?.role !== 'PLATFORM_ADMIN');

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

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* メイン情報 */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle>基本情報</CardTitle>
              <CardDescription>
                ユーザーの基本情報を設定します
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="username">ユーザー名</Label>
                    <Input
                      id="username"
                      {...register('username')}
                      disabled={isViewMode || !canEdit}
                    />
                    {errors.username && (
                      <p className="text-sm text-red-600">{errors.username.message}</p>
                    )}
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="email">メールアドレス</Label>
                    <Input
                      id="email"
                      type="email"
                      {...register('email')}
                      disabled={isViewMode || !canEdit}
                    />
                    {errors.email && (
                      <p className="text-sm text-red-600">{errors.email.message}</p>
                    )}
                  </div>
                </div>

                {isCreateMode && (
                  <div className="space-y-2">
                    <Label htmlFor="password">パスワード</Label>
                    <div className="relative">
                      <Input
                        id="password"
                        type={showPassword ? 'text' : 'password'}
                        {...register('password')}
                        disabled={isViewMode || !canEdit}
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
                    {errors.password && (
                      <p className="text-sm text-red-600">{errors.password.message}</p>
                    )}
                  </div>
                )}

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="role">ロール</Label>
                    <Select
                      value={watchedRole}
                      onValueChange={(value) => setValue('role', value as any)}
                      disabled={isViewMode || !canEdit}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="ロールを選択" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="OPERATOR">運用者</SelectItem>
                        <SelectItem value="AUDITOR">監査者</SelectItem>
                        {currentUser?.role === 'PLATFORM_ADMIN' && (
                          <>
                            <SelectItem value="TENANT_ADMIN">テナント管理者</SelectItem>
                            <SelectItem value="PLATFORM_ADMIN">プラットフォーム管理者</SelectItem>
                          </>
                        )}
                      </SelectContent>
                    </Select>
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

        {/* サイドバー情報 */}
        <div className="space-y-6">
          {/* ユーザー情報 */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <UserIcon className="mr-2 h-5 w-5" />
                ユーザー情報
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center space-x-3">
                <Avatar className="h-12 w-12">
                  <AvatarImage src="" alt={user?.username || ''} />
                  <AvatarFallback>
                    <UserIcon className="h-6 w-6" />
                  </AvatarFallback>
                </Avatar>
                <div>
                  <div className="font-medium">{user?.username || '新規ユーザー'}</div>
                  <div className="text-sm text-muted-foreground">
                    {user?.email || 'メールアドレス未設定'}
                  </div>
                </div>
              </div>

              <Separator />

              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">ロール</span>
                  <Badge variant={getRoleBadgeVariant(watchedRole)}>
                    {getRoleLabel(watchedRole)}
                  </Badge>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">ステータス</span>
                  <Badge variant={watchedIsActive ? 'default' : 'secondary'}>
                    {watchedIsActive ? 'アクティブ' : '非アクティブ'}
                  </Badge>
                </div>

                {user && (
                  <>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground">作成日</span>
                      <span className="text-sm">
                        {format(new Date(user.created_at), 'yyyy/MM/dd', { locale: ja })}
                      </span>
                    </div>

                    {user.last_login_at && (
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-muted-foreground">最終ログイン</span>
                        <span className="text-sm">
                          {format(new Date(user.last_login_at), 'yyyy/MM/dd HH:mm', { locale: ja })}
                        </span>
                      </div>
                    )}
                  </>
                )}
              </div>
            </CardContent>
          </Card>

          {/* 権限情報 */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Shield className="mr-2 h-5 w-5" />
                権限情報
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {watchedRole === 'PLATFORM_ADMIN' && (
                  <div className="text-sm">
                    <div className="font-medium">プラットフォーム管理者</div>
                    <div className="text-muted-foreground">
                      全システムの管理権限を持ちます
                    </div>
                  </div>
                )}
                {watchedRole === 'TENANT_ADMIN' && (
                  <div className="text-sm">
                    <div className="font-medium">テナント管理者</div>
                    <div className="text-muted-foreground">
                      自テナントの管理権限を持ちます
                    </div>
                  </div>
                )}
                {watchedRole === 'OPERATOR' && (
                  <div className="text-sm">
                    <div className="font-medium">運用者</div>
                    <div className="text-muted-foreground">
                      コンテンツ管理と統計確認ができます
                    </div>
                  </div>
                )}
                {watchedRole === 'AUDITOR' && (
                  <div className="text-sm">
                    <div className="font-medium">監査者</div>
                    <div className="text-muted-foreground">
                      ログ閲覧と監査データエクスポートができます
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
