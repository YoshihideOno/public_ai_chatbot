/**
 * コンテンツ一覧表示コンポーネント
 * 
 * ナレッジベースのコンテンツ一覧を表示し、検索・フィルタリング・
 * ページネーション機能を提供する。管理者権限に応じて編集・削除機能も提供。
 * 
 * 機能:
 * - コンテンツ一覧の表示
 * - 検索・フィルタリング機能
 * - ページネーション
 * - コンテンツの編集・削除（権限に応じて）
 * - 再インデックス機能
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
import { Progress } from '@/components/ui/progress';
import { apiClient, Content } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import { logger } from '@/utils/logger';
import { 
  Plus, 
  Search, 
  MoreHorizontal, 
  Edit, 
  Trash2, 
  FileText,
  Filter,
  Download,
  RefreshCw,
  Eye,
  File,
  FileSpreadsheet,
  FileCode,
  FileType
} from 'lucide-react';
import { format } from 'date-fns';
import { ja } from 'date-fns/locale';

/**
 * コンテンツ一覧表示コンポーネント
 * @returns React.ReactElement コンテンツ一覧のUI
 */
export function ContentsList(): React.ReactElement {
  // コンテンツ一覧の状態管理
  const [contents, setContents] = useState<Content[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  
  // 検索・フィルタリングの状態管理
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [debouncedSearchTerm, setDebouncedSearchTerm] = useState<string>('');
  const [fileTypeFilter, setFileTypeFilter] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  
  // ページネーションの状態管理
  const [currentPage, setCurrentPage] = useState<number>(0);
  const [totalPages, setTotalPages] = useState<number>(0);
  const itemsPerPage: number = 20;

  // 認証コンテキストから現在のユーザー情報を取得
  const { user: currentUser } = useAuth();

  // 検索語のデバウンス処理
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearchTerm(searchTerm);
      setCurrentPage(0); // 検索時にページをリセット
    }, 300);

    return () => clearTimeout(timer);
  }, [searchTerm]);

  /**
   * コンテンツ一覧を取得する関数
   * @param page ページ番号（デフォルト: 0）
   * @returns Promise<void>
   */
  const fetchContents = React.useCallback(async (page: number = 0): Promise<void> => {
    try {
      setIsLoading(true);
      setError(null);
      
      // ページネーション用のスキップ数を計算
      const skip: number = page * itemsPerPage;
      
      // APIからコンテンツ一覧を取得
      const contentsData: Content[] = await apiClient.getContents(
        skip, 
        itemsPerPage, 
        fileTypeFilter || undefined, 
        statusFilter || undefined, 
        debouncedSearchTerm || undefined
      );
      
      // 状態を更新
      setContents(contentsData);
      setTotalPages(Math.ceil(contentsData.length / itemsPerPage));
    } catch (err: unknown) {
      // エラーログを出力
      logger.error('コンテンツ一覧の取得に失敗', err);
      setError('コンテンツ一覧の取得に失敗しました');
    } finally {
      setIsLoading(false);
    }
  }, [fileTypeFilter, statusFilter, debouncedSearchTerm]);

  // コンテンツ一覧の取得を実行
  useEffect(() => {
    fetchContents(currentPage);
  }, [currentPage, fetchContents]);

  // PROCESSING/UPLOADED が存在する間のみ短期ポーリングで自動更新
  useEffect(() => {
    const hasPending = contents.some(
      (c) => c.status === 'PROCESSING' || c.status === 'UPLOADED'
    );
    if (!hasPending) return; 
    const interval = setInterval(() => {
      void fetchContents(currentPage);
    }, 3000);
    return () => clearInterval(interval);
  }, [contents, currentPage, fetchContents]);

  /**
   * コンテンツをダウンロードする関数
   * @param contentId 対象コンテンツのID
   */
  const handleDownloadContent = async (contentId: string, suggestedFileName?: string): Promise<void> => {
    try {
      const { blob, filename } = await apiClient.downloadContent(contentId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename || suggestedFileName || 'content';
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err: unknown) {
      logger.error('コンテンツのダウンロードに失敗', err);
      setError('コンテンツのダウンロードに失敗しました');
    }
  };

  /**
   * コンテンツ一覧をエクスポートする関数
   * @param format 'csv' | 'json'
   */
  const handleExport = async (format: 'csv' | 'json'): Promise<void> => {
    try {
      const { blob, filename } = await apiClient.exportContents({
        fileType: fileTypeFilter || undefined,
        status: statusFilter || undefined,
        search: debouncedSearchTerm || undefined,
        format,
      });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename || `contents_export.${format}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err: unknown) {
      logger.error('エクスポートに失敗', err);
      setError('エクスポートに失敗しました');
    }
  };

  /**
   * コンテンツを削除する関数
   * @param contentId 削除するコンテンツのID
   * @returns Promise<void>
   */
  const handleDeleteContent = async (contentId: string): Promise<void> => {
    // 削除確認ダイアログを表示
    if (!confirm('このコンテンツを削除しますか？')) {
      return;
    }

    try {
      // APIでコンテンツを削除
      await apiClient.deleteContent(contentId);
      
      // ローカル状態からも削除
      setContents(contents.filter(content => content.id !== contentId));
    } catch (err: unknown) {
      // エラーログを出力
      logger.error('コンテンツの削除に失敗', err);
      setError('コンテンツの削除に失敗しました');
    }
  };

  /**
   * コンテンツの再インデックスを実行する関数
   * @param contentId 再インデックスするコンテンツのID
   * @returns Promise<void>
   */
  const handleReindexContent = async (contentId: string): Promise<void> => {
    try {
      // TODO: 再インデックスAPIを実装
      logger.info('コンテンツの再インデックス開始', { contentId });
      alert('再インデックスが開始されました');
      
      // 一覧を再取得
      await fetchContents(currentPage);
    } catch (err: unknown) {
      // エラーログを出力
      logger.error('再インデックスの開始に失敗', err);
      setError('再インデックスの開始に失敗しました');
    }
  };

  /**
   * ファイルタイプに応じたアイコンを取得する関数
   * @param fileType ファイルタイプ
   * @returns React.ReactElement 対応するアイコン
   */
  const getFileTypeIcon = (fileType: string): React.ReactElement => {
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

  /**
   * ステータスに応じたバッジのバリアントを取得する関数
   * @param status ステータス
   * @returns Badgeのバリアント
   */
  const getStatusBadgeVariant = (status: string): "default" | "secondary" | "outline" | "destructive" => {
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

  /**
   * ステータスに応じた日本語ラベルを取得する関数
   * @param status ステータス
   * @returns 日本語ラベル
   */
  const getStatusLabel = (status: string): string => {
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

  /**
   * バイト数を人間が読みやすい形式に変換する関数
   * @param bytes バイト数
   * @returns フォーマットされたファイルサイズ文字列
   */
  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k: number = 1024;
    const sizes: string[] = ['Bytes', 'KB', 'MB', 'GB'];
    const i: number = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  // 検索条件に基づいてコンテンツをフィルタリング
  const filteredContents: Content[] = contents.filter(content =>
    content.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    content.description?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    content.file_name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // コンテンツ管理権限の確認
  const canManageContents: boolean = currentUser?.role === 'PLATFORM_ADMIN' || 
                           currentUser?.role === 'TENANT_ADMIN' || 
                           currentUser?.role === 'OPERATOR';

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
            <Button 
              variant="outline" 
              size="sm"
              onClick={() => {
                setSearchTerm('');
                setFileTypeFilter('');
                setStatusFilter('');
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
                <DropdownMenuItem onClick={() => void handleExport('csv')}>CSV</DropdownMenuItem>
                <DropdownMenuItem onClick={() => void handleExport('json')}>JSON</DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>

          {isLoading && (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
          )}
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
                          {formatFileSize(content.file_size ?? content.size_bytes ?? 0)}
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
                            <DropdownMenuItem onClick={() => void handleDownloadContent(content.id, content.file_name)}>
                                  <Download className="mr-2 h-4 w-4" />
                                  ダウンロード
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
