/**
 * テナント一覧コンポーネント
 * 
 * このファイルはテナント一覧を表示・管理するためのReactコンポーネントを定義します。
 * テナントの検索、フィルタリング、ページネーション、アクション（編集・削除）などの
 * 機能を提供します。
 * 
 * 主な機能:
 * - テナント一覧の表示
 * - 検索・フィルタリング機能
 * - ページネーション
 * - テナントアクション（編集・削除）
 * - プラン・ステータス表示
 * - 管理者権限チェック
 */

'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
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
import { apiClient, Tenant } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import { 
  Plus, 
  Search, 
  MoreHorizontal, 
  Edit, 
  Trash2, 
  Building2,
  Filter,
  Download
} from 'lucide-react';
import { format } from 'date-fns';
import { ja } from 'date-fns/locale';

export function TenantsList() {
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const itemsPerPage = 20;

  const { user: currentUser } = useAuth();

  const fetchTenants = async (page: number = 0) => {
    try {
      setIsLoading(true);
      setError(null);
      
      const skip = page * itemsPerPage;
      const tenantsData = await apiClient.getTenants(skip, itemsPerPage);
      
      setTenants(tenantsData);
      setTotalPages(Math.ceil(tenantsData.length / itemsPerPage));
    } catch (err: unknown) {
      console.error('Failed to fetch tenants:', err);
      setError('テナント一覧の取得に失敗しました');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchTenants(currentPage);
  }, [currentPage]);

  const handleDeleteTenant = async (tenantId: string) => {
    if (!confirm('このテナントを削除しますか？')) {
      return;
    }

    try {
      await apiClient.deleteTenant(tenantId);
      setTenants(tenants.filter(tenant => tenant.id !== tenantId));
    } catch (err: unknown) {
      console.error('Failed to delete tenant:', err);
      setError('テナントの削除に失敗しました');
    }
  };


  const getPlanBadgeVariant = (plan: string) => {
    switch (plan) {
      case 'ENTERPRISE':
        return 'destructive';
      case 'PRO':
        return 'default';
      case 'BASIC':
        return 'secondary';
      case 'FREE':
        return 'outline';
      default:
        return 'outline';
    }
  };

  const getPlanLabel = (plan: string) => {
    switch (plan) {
      case 'FREE':
        return 'Free';
      case 'BASIC':
        return 'Basic';
      case 'PRO':
        return 'Pro';
      case 'ENTERPRISE':
        return 'Enterprise';
      default:
        return plan;
    }
  };

  const getStatusBadgeVariant = (status: string) => {
    switch (status) {
      case 'ACTIVE':
        return 'default';
      case 'SUSPENDED':
        return 'secondary';
      case 'DELETED':
        return 'destructive';
      default:
        return 'outline';
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'ACTIVE':
        return 'アクティブ';
      case 'SUSPENDED':
        return '停止中';
      case 'DELETED':
        return '削除済み';
      default:
        return status;
    }
  };

  const filteredTenants = tenants.filter(tenant =>
    tenant.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    tenant.domain.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const canManageTenants = currentUser?.role === 'PLATFORM_ADMIN';

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
          <h1 className="text-3xl font-bold">テナント管理</h1>
          <p className="text-muted-foreground">
            システムテナントの一覧と管理
          </p>
        </div>
        {canManageTenants && (
          <Button asChild>
            <Link href="/tenants/new">
              <Plus className="mr-2 h-4 w-4" />
              新規テナント
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
          <CardTitle>テナント一覧</CardTitle>
          <CardDescription>
            登録されているテナントの一覧です
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center space-x-4 mb-6">
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
              <Input
                placeholder="テナント名またはドメインで検索..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            <Button variant="outline" size="sm">
              <Filter className="mr-2 h-4 w-4" />
              フィルタ
            </Button>
            <Button variant="outline" size="sm">
              <Download className="mr-2 h-4 w-4" />
              エクスポート
            </Button>
          </div>

          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>テナント</TableHead>
                  <TableHead>プラン</TableHead>
                  <TableHead>ステータス</TableHead>
                  <TableHead>ドメイン</TableHead>
                  <TableHead>作成日</TableHead>
                  <TableHead className="w-[70px]"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredTenants.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} className="text-center py-8 text-muted-foreground">
                      テナントが見つかりません
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredTenants.map((tenant) => (
                    <TableRow key={tenant.id}>
                      <TableCell>
                        <div className="flex items-center space-x-3">
                          <div className="h-8 w-8 rounded bg-primary flex items-center justify-center">
                            <Building2 className="h-4 w-4 text-primary-foreground" />
                          </div>
                          <div>
                            <div className="font-medium">{tenant.name}</div>
                            <div className="text-sm text-muted-foreground">
                              ID: {tenant.id.slice(0, 8)}...
                            </div>
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant={getPlanBadgeVariant(tenant.plan)}>
                          {getPlanLabel(tenant.plan)}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge variant={getStatusBadgeVariant(tenant.status)}>
                          {getStatusLabel(tenant.status)}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="font-mono text-sm">{tenant.domain}</div>
                      </TableCell>
                      <TableCell>
                        {format(new Date(tenant.created_at), 'yyyy/MM/dd', { locale: ja })}
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
                            {canManageTenants && (
                              <>
                                <DropdownMenuItem asChild>
                                  <Link href={`/tenants/${tenant.id}/edit`}>
                                    <Edit className="mr-2 h-4 w-4" />
                                    編集
                                  </Link>
                                </DropdownMenuItem>
                                <DropdownMenuSeparator />
                                <DropdownMenuItem
                                  onClick={() => handleDeleteTenant(tenant.id)}
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
                {filteredTenants.length} 件中 {currentPage * itemsPerPage + 1} - {Math.min((currentPage + 1) * itemsPerPage, filteredTenants.length)} 件を表示
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
