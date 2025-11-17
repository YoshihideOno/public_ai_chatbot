/**
 * ユーザー一覧コンポーネント
 * 
 * このファイルはユーザー一覧を表示・管理するためのReactコンポーネントを定義します。
 * ユーザーの検索、フィルタリング、ページネーション、アクション（編集・削除）などの
 * 機能を提供します。
 * 
 * 主な機能:
 * - ユーザー一覧の表示
 * - 検索・フィルタリング機能
 * - ページネーション
 * - ユーザーアクション（編集・削除）
 * - ロール別表示制御
 */

'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { apiClient, User } from '@/lib/api';
import { usePermissions } from '@/hooks/usePermissions';
import { 
  Plus, 
  Search, 
  MoreHorizontal, 
  Edit, 
  Trash2, 
  User as UserIcon,
  Filter,
  Download
} from 'lucide-react';
import { format } from 'date-fns';
import { ja } from 'date-fns/locale';

export function UsersList() {
  /**
   * ユーザー一覧コンポーネント
   * 
   * ユーザー一覧を表示し、検索・フィルタリング・ページネーション機能を提供します。
   * 認証されたユーザーのみがアクセス可能で、ロールに応じた表示制御を行います。
   */
  const [users, setUsers] = useState<User[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const itemsPerPage = 20;

  const { canManageUsers, canDeleteUser } = usePermissions();

  const handleExport = async (format: 'csv' | 'json') => {
    /**
     * ユーザー一覧エクスポート
     *
     * 引数:
     *   format: 'csv' | 'json'
     * 戻り値:
     *   Promise<void>
     */
    try {
      const { blob, filename } = await apiClient.exportUsers({
        format,
        search: searchTerm || undefined,
      });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename || `users.${format}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Failed to export users:', err);
      setError('エクスポートに失敗しました');
    }
  };

  const fetchUsers = async (page: number = 0) => {
    /**
     * ユーザー一覧を取得
     * 
     * 引数:
     *   page: ページ番号（0から開始）
     * 
     * 戻り値:
     *   Promise<void>: 非同期処理
     * 
     * 例外:
     *   Error: API呼び出し失敗時のエラー
     */
    try {
      setIsLoading(true);
      setError(null);
      
      const skip = page * itemsPerPage;
      const usersData = await apiClient.getUsers(skip, itemsPerPage);
      
      setUsers(usersData);
      setTotalPages(Math.ceil(usersData.length / itemsPerPage));
    } catch (err: unknown) {
      console.error('Failed to fetch users:', err);
      setError('ユーザー一覧の取得に失敗しました');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers(currentPage);
  }, [currentPage]);

  const handleDeleteUser = async (userId: string | number) => {
    /**
     * ユーザー削除処理
     * 
     * 引数:
     *   userId: 削除するユーザーのID
     * 
     * 戻り値:
     *   Promise<void>: 非同期処理
     * 
     * 例外:
     *   Error: 削除失敗時のエラー
     */
    if (!confirm('このユーザーを削除しますか？')) {
      return;
    }

    try {
      await apiClient.deleteUser(userId);
      setUsers(users.filter(user => String(user.id) !== String(userId)));
    } catch (err: unknown) {
      console.error('Failed to delete user:', err);
      setError('ユーザーの削除に失敗しました');
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

  const filteredUsers = users.filter(user =>
    user.username.toLowerCase().includes(searchTerm.toLowerCase()) ||
    user.email.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // canManageUsers は usePermissions に集約

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">ユーザー管理</h1>
          <p className="text-muted-foreground">
            システムユーザーの一覧と管理
          </p>
        </div>
        {canManageUsers && (
          <Button asChild>
            <Link href="/users/new">
              <Plus className="mr-2 h-4 w-4" />
              新規ユーザー
            </Link>
          </Button>
        )}
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <Card>
        <CardHeader>
          <CardTitle>ユーザー一覧</CardTitle>
          <CardDescription>
            登録されているユーザーの一覧です
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center space-x-4 mb-6">
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
              <Input
                placeholder="ユーザー名またはメールアドレスで検索..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setSearchTerm('');
                setCurrentPage(0);
              }}
            >
              <Filter className="mr-2 h-4 w-4" />
              リセット
            </Button>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" size="sm">
                  <Download className="mr-2 h-4 w-4" />
                  エクスポート
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuLabel>形式を選択</DropdownMenuLabel>
                <DropdownMenuItem onClick={() => handleExport('csv')}>CSVでエクスポート</DropdownMenuItem>
                <DropdownMenuItem onClick={() => handleExport('json')}>JSONでエクスポート</DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>

          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>ユーザー</TableHead>
                  <TableHead>ロール</TableHead>
                  <TableHead>ステータス</TableHead>
                  <TableHead>最終ログイン</TableHead>
                  <TableHead>作成日</TableHead>
                  <TableHead className="w-[70px]"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredUsers.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} className="text-center py-8 text-muted-foreground">
                      ユーザーが見つかりません
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredUsers.map((user) => (
                    <TableRow key={user.id}>
                      <TableCell>
                        <div className="flex items-center space-x-3">
                          <Avatar className="h-8 w-8">
                            <AvatarImage src="" alt={user.username} />
                            <AvatarFallback>
                              <UserIcon className="h-4 w-4" />
                            </AvatarFallback>
                          </Avatar>
                          <div>
                            <div className="font-medium">{user.username}</div>
                            <div className="text-sm text-muted-foreground">
                              {user.email}
                            </div>
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant={getRoleBadgeVariant(user.role)}>
                          {getRoleLabel(user.role)}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge variant={user.is_active ? 'default' : 'secondary'}>
                          {user.is_active ? 'アクティブ' : '非アクティブ'}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {user.last_login_at ? (
                          format(new Date(user.last_login_at), 'yyyy/MM/dd HH:mm', { locale: ja })
                        ) : (
                          <span className="text-muted-foreground">未ログイン</span>
                        )}
                      </TableCell>
                      <TableCell>
                        {format(new Date(user.created_at), 'yyyy/MM/dd', { locale: ja })}
                      </TableCell>
                      <TableCell>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" className="h-8 w-8 p-0">
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuLabel>アクション</DropdownMenuLabel>
                            {canManageUsers && (
                              <>
                                <DropdownMenuItem asChild>
                                  <Link href={`/users/${user.id}/edit`}>
                                    <Edit className="mr-2 h-4 w-4" />
                                    編集
                                  </Link>
                                </DropdownMenuItem>
                                <DropdownMenuSeparator />
                                <DropdownMenuItem
                                  onClick={() => handleDeleteUser(user.id)}
                                  disabled={!canDeleteUser(user.role)}
                                  className="text-red-600"
                                >
                                  <Trash2 className="mr-2 h-4 w-4" />
                                  削除
                                </DropdownMenuItem>
                              </>
                            )}
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>

          {totalPages > 1 && (
            <div className="flex items-center justify-between mt-4">
              <div className="text-sm text-muted-foreground">
                {filteredUsers.length} 件中 {currentPage * itemsPerPage + 1} - {Math.min((currentPage + 1) * itemsPerPage, filteredUsers.length)} 件を表示
              </div>
              <div className="flex items-center space-x-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentPage(Math.max(0, currentPage - 1))}
                  disabled={currentPage === 0}
                >
                  前へ
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentPage(Math.min(totalPages - 1, currentPage + 1))}
                  disabled={currentPage >= totalPages - 1}
                >
                  次へ
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
