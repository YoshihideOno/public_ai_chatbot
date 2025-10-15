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
import { Progress } from '@/components/ui/progress';
import { apiClient, Content } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import { 
  Plus, 
  Search, 
  MoreHorizontal, 
  Edit, 
  Trash2, 
  FileText,
  Filter,
  Download,
  Upload,
  RefreshCw,
  Eye,
  File,
  FileImage,
  FileSpreadsheet,
  FileCode,
  FileType
} from 'lucide-react';
import { format } from 'date-fns';
import { ja } from 'date-fns/locale';

export function ContentsList() {
  const [contents, setContents] = useState<Content[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [fileTypeFilter, setFileTypeFilter] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [currentPage, setCurrentPage] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const itemsPerPage = 20;

  const { user: currentUser } = useAuth();

  const fetchContents = async (page: number = 0) => {
    try {
      setIsLoading(true);
      setError(null);
      
      const skip = page * itemsPerPage;
      const contentsData = await apiClient.getContents(
        skip, 
        itemsPerPage, 
        fileTypeFilter || undefined, 
        statusFilter || undefined, 
        searchTerm || undefined
      );
      
      setContents(contentsData);
      setTotalPages(Math.ceil(contentsData.length / itemsPerPage));
    } catch (err: any) {
      console.error('Failed to fetch contents:', err);
      setError('コンテンツ一覧の取得に失敗しました');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchContents(currentPage);
  }, [currentPage, fileTypeFilter, statusFilter]);

  const handleDeleteContent = async (contentId: string) => {
    if (!confirm('このコンテンツを削除しますか？')) {
      return;
    }

    try {
      await apiClient.deleteContent(contentId);
      setContents(contents.filter(content => content.id !== contentId));
    } catch (err: any) {
      console.error('Failed to delete content:', err);
      setError('コンテンツの削除に失敗しました');
    }
  };

  const handleReindexContent = async (contentId: string) => {
    try {
      // TODO: 再インデックスAPIを実装
      alert('再インデックスが開始されました');
      await fetchContents(currentPage);
    } catch (err: any) {
      console.error('Failed to reindex content:', err);
      setError('再インデックスの開始に失敗しました');
    }
  };

  const getFileTypeIcon = (fileType: string) => {
    switch (fileType) {
      case 'PDF':
        return <FileText className="h-4 w-4 text-red-600" />;
      case 'HTML':
        return <FileCode className="h-4 w-4 text-orange-600" />;
      case 'MD':
        return <FileType className="h-4 w-4 text-blue-600" />;
      case 'CSV':
        return <FileSpreadsheet className="h-4 w-4 text-green-600" />;
      case 'TXT':
        return <File className="h-4 w-4 text-gray-600" />;
      default:
        return <File className="h-4 w-4 text-gray-600" />;
    }
  };

  const getStatusBadgeVariant = (status: string) => {
    switch (status) {
      case 'INDEXED':
        return 'default';
      case 'PROCESSING':
        return 'secondary';
      case 'UPLOADED':
        return 'outline';
      case 'FAILED':
        return 'destructive';
      default:
        return 'outline';
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'INDEXED':
        return 'インデックス済み';
      case 'PROCESSING':
        return '処理中';
      case 'UPLOADED':
        return 'アップロード済み';
      case 'FAILED':
        return '失敗';
      default:
        return status;
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const filteredContents = contents.filter(content =>
    content.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    content.description?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    content.file_name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const canManageContents = currentUser?.role === 'PLATFORM_ADMIN' || 
                           currentUser?.role === 'TENANT_ADMIN' || 
                           currentUser?.role === 'OPERATOR';

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
          <h1 className="text-3xl font-bold">コンテンツ管理</h1>
          <p className="text-muted-foreground">
            ナレッジベースのコンテンツ管理
          </p>
        </div>
        {canManageContents && (
          <div className="flex items-center space-x-2">
            <Button variant="outline" asChild>
              <Link href="/contents/upload">
                <Upload className="mr-2 h-4 w-4" />
                ファイルアップロード
              </Link>
            </Button>
            <Button asChild>
              <Link href="/contents/new">
                <Plus className="mr-2 h-4 w-4" />
                新規コンテンツ
              </Link>
            </Button>
          </div>
        )}
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <Card>
        <CardHeader>
          <CardTitle>コンテンツ一覧</CardTitle>
          <CardDescription>
            アップロードされたコンテンツの一覧です
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center space-x-4 mb-6">
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
              <Input
                placeholder="タイトルまたは説明で検索..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            <select
              value={fileTypeFilter}
              onChange={(e) => setFileTypeFilter(e.target.value)}
              className="px-3 py-2 border border-input rounded-md bg-background"
            >
              <option value="">すべてのファイルタイプ</option>
              <option value="PDF">PDF</option>
              <option value="HTML">HTML</option>
              <option value="MD">Markdown</option>
              <option value="CSV">CSV</option>
              <option value="TXT">TXT</option>
            </select>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-3 py-2 border border-input rounded-md bg-background"
            >
              <option value="">すべてのステータス</option>
              <option value="INDEXED">インデックス済み</option>
              <option value="PROCESSING">処理中</option>
              <option value="UPLOADED">アップロード済み</option>
              <option value="FAILED">失敗</option>
            </select>
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
                  <TableHead>ファイル</TableHead>
                  <TableHead>タイプ</TableHead>
                  <TableHead>サイズ</TableHead>
                  <TableHead>ステータス</TableHead>
                  <TableHead>チャンク数</TableHead>
                  <TableHead>アップロード日</TableHead>
                  <TableHead className="w-[70px]"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredContents.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} className="text-center py-8 text-muted-foreground">
                      コンテンツが見つかりません
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredContents.map((content) => (
                    <TableRow key={content.id}>
                      <TableCell>
                        <div className="flex items-center space-x-3">
                          {getFileTypeIcon(content.file_type)}
                          <div>
                            <div className="font-medium">{content.title}</div>
                            <div className="text-sm text-muted-foreground">
                              {content.file_name}
                            </div>
                            {content.description && (
                              <div className="text-sm text-muted-foreground mt-1">
                                {content.description.slice(0, 50)}...
                              </div>
                            )}
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline">
                          {content.file_type}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="text-sm">
                          {formatFileSize(content.size_bytes)}
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center space-x-2">
                          <Badge variant={getStatusBadgeVariant(content.status)}>
                            {getStatusLabel(content.status)}
                          </Badge>
                          {content.status === 'PROCESSING' && (
                            <Progress value={50} className="w-16" />
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="text-sm">
                          {content.chunk_count || '-'}
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="text-sm">
                          {format(new Date(content.uploaded_at), 'yyyy/MM/dd HH:mm', { locale: ja })}
                        </div>
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
                            <DropdownMenuItem asChild>
                              <Link href={`/contents/${content.id}`}>
                                <Eye className="mr-2 h-4 w-4" />
                                詳細表示
                              </Link>
                            </DropdownMenuItem>
                            {canManageContents && (
                              <>
                                <DropdownMenuItem asChild>
                                  <Link href={`/contents/${content.id}/edit`}>
                                    <Edit className="mr-2 h-4 w-4" />
                                    編集
                                  </Link>
                                </DropdownMenuItem>
                                <DropdownMenuItem onClick={() => handleReindexContent(content.id)}>
                                  <RefreshCw className="mr-2 h-4 w-4" />
                                  再インデックス
                                </DropdownMenuItem>
                                <DropdownMenuSeparator />
                                <DropdownMenuItem
                                  onClick={() => handleDeleteContent(content.id)}
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
                {filteredContents.length} 件中 {currentPage * itemsPerPage + 1} - {Math.min((currentPage + 1) * itemsPerPage, filteredContents.length)} 件を表示
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
