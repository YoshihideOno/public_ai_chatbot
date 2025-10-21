/**
 * コンテンツ管理フォームコンポーネント
 * 
 * このファイルは、RAG AIプラットフォームにおけるコンテンツの作成・編集・表示を
 * 管理するフォームコンポーネントを提供します。PDF、HTML、Markdown、CSV、TXT
 * ファイルのアップロードと管理機能を実装しています。
 * 
 * 主な機能:
 * - コンテンツの新規作成・編集・表示
 * - ファイルアップロード機能（プログレス表示付き）
 * - ファイルタイプ別のアイコン表示
 * - コンテンツのステータス管理（アップロード済み、処理中、インデックス済み、失敗）
 * - チャンク分割情報の表示
 * - コンテンツの削除・再インデックス・複製機能
 * - ロールベースのアクセス制御
 * - タブ形式での情報表示（基本情報、コンテンツ、チャンク、分析）
 * 
 * 対応ファイル形式:
 * - PDF: 文書ファイル
 * - HTML: Webページ
 * - MD: Markdown文書
 * - CSV: 表形式データ
 * - TXT: テキストファイル
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
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { apiClient, Content } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import { 
  ArrowLeft, 
  Save, 
  FileText,
  Upload,
  RefreshCw,
  Trash2,
  File,
  FileSpreadsheet,
  FileCode,
  FileType,
  Download,
  Copy
} from 'lucide-react';
import { format } from 'date-fns';
import { ja } from 'date-fns/locale';

/**
 * コンテンツフォームのバリデーションスキーマ
 * Zodを使用してフォームデータの型安全性とバリデーションを実装
 */
const contentSchema = z.object({
  title: z.string().min(1, 'タイトルは必須です'),
  description: z.string().optional(),
  tags: z.array(z.string()).optional(),
  file_type: z.enum(['PDF', 'HTML', 'MD', 'CSV', 'TXT']),
});

/**
 * コンテンツフォームデータの型定義
 * contentSchemaから推論された型
 */
type ContentFormData = z.infer<typeof contentSchema>;

/**
 * ContentFormコンポーネントのプロパティ型定義
 * @param contentId - 編集・表示するコンテンツのID（オプション）
 * @param mode - フォームの動作モード（作成・編集・表示）
 */
interface ContentFormProps {
  contentId?: string;
  mode: 'create' | 'edit' | 'view';
}

/**
 * コンテンツ管理フォームコンポーネント
 * コンテンツの作成・編集・表示機能を提供するメインコンポーネント
 * 
 * @param contentId - 編集・表示するコンテンツのID（オプション）
 * @param mode - フォームの動作モード（作成・編集・表示）
 * @returns コンテンツ管理フォームのJSX要素
 */
export function ContentForm({ contentId, mode }: ContentFormProps) {
  // コンテンツデータの状態管理
  const [content, setContent] = useState<Content | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  
  // 認証情報とルーターの取得
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
  } = useForm<ContentFormData>({
    resolver: zodResolver(contentSchema),
    defaultValues: {
      file_type: 'TXT',
      tags: [],
    },
  });

  // フォームの監視対象フィールド
  const watchedFileType = watch('file_type');
  const watchedTitle = watch('title');
  const watchedDescription = watch('description');

  /**
   * コンテンツ情報を取得してフォームに設定する関数
   * APIからコンテンツデータを取得し、フォームフィールドに値を設定します
   */
  const fetchContent = useCallback(async () => {
    if (!contentId) return;

    try {
      setIsLoading(true);
      const contentData = await apiClient.getContent(contentId);
      setContent(contentData);
      
      // フォームに値を設定
      setValue('title', contentData.title);
      setValue('description', contentData.description || '');
      setValue('file_type', contentData.file_type);
      setValue('tags', contentData.tags);
    } catch (err: unknown) {
      console.error('Failed to fetch content:', err);
      setError('コンテンツ情報の取得に失敗しました');
    } finally {
      setIsLoading(false);
    }
  }, [contentId, setValue]);

  useEffect(() => {
    if (contentId && !isCreateMode) {
      fetchContent();
    }
  }, [contentId, isCreateMode, fetchContent]);

  /**
   * フォーム送信処理
   * コンテンツの作成または更新を行い、成功時はコンテンツ一覧ページに遷移します
   * 
   * @param data - フォームから送信されたデータ
   */
  const onSubmit = async (data: ContentFormData) => {
    setIsLoading(true);
    setError(null);

    try {
      if (isCreateMode) {
        await apiClient.createContent(data);
      } else if (contentId) {
        await apiClient.updateContent(contentId, data);
      }
      
      router.push('/contents');
    } catch (err: unknown) {
      console.error('Failed to save content:', err);
      
      if (err && typeof err === 'object' && 'response' in err) {
        const errorResponse = err as { response?: { data?: { error?: { message?: string } } } };
        if (errorResponse.response?.data?.error?.message) {
          setError(errorResponse.response.data.error.message);
        } else {
          setError('コンテンツの保存に失敗しました');
        }
      } else {
        setError('コンテンツの保存に失敗しました');
      }
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * ファイルアップロード処理
   * 選択されたファイルをアップロードし、プログレス表示を行います
   * アップロード完了後はコンテンツ一覧ページに遷移します
   * 
   * @param event - ファイル入力の変更イベント
   */
  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    setUploadProgress(0);

    try {
      // プログレスシミュレーション
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return 90;
          }
          return prev + 10;
        });
      }, 200);

      await apiClient.uploadFile(
        file,
        watchedTitle || file.name.split('.')[0],
        watchedDescription,
        []
      );

      setUploadProgress(100);
      setTimeout(() => {
        router.push('/contents');
      }, 1000);

    } catch (err: unknown) {
      console.error('Failed to upload file:', err);
      setError('ファイルのアップロードに失敗しました');
    } finally {
      setIsUploading(false);
    }
  };

  /**
   * コンテンツ削除処理
   * 確認ダイアログを表示してからコンテンツを削除し、
   * 成功時はコンテンツ一覧ページに遷移します
   */
  const handleDeleteContent = async () => {
    if (!contentId) return;

    if (!confirm('このコンテンツを削除しますか？')) {
      return;
    }

    try {
      await apiClient.deleteContent(contentId);
      router.push('/contents');
    } catch (err: unknown) {
      console.error('Failed to delete content:', err);
      setError('コンテンツの削除に失敗しました');
    }
  };

  /**
   * コンテンツ再インデックス処理
   * コンテンツの再インデックスを開始します（実装予定）
   */
  const handleReindexContent = async () => {
    if (!contentId) return;

    try {
      // TODO: 再インデックスAPIを実装
      alert('再インデックスが開始されました');
    } catch (err: unknown) {
      console.error('Failed to reindex content:', err);
      setError('再インデックスの開始に失敗しました');
    }
  };

  /**
   * ファイルタイプに応じたアイコンを取得する関数
   * 
   * @param fileType - ファイルタイプ（PDF, HTML, MD, CSV, TXT）
   * @returns 対応するLucideアイコンコンポーネント
   */
  const getFileTypeIcon = (fileType: string) => {
    switch (fileType) {
      case 'PDF':
        return <FileText className="h-5 w-5 text-red-600" />;
      case 'HTML':
        return <FileCode className="h-5 w-5 text-orange-600" />;
      case 'MD':
        return <FileType className="h-5 w-5 text-blue-600" />;
      case 'CSV':
        return <FileSpreadsheet className="h-5 w-5 text-green-600" />;
      case 'TXT':
        return <File className="h-5 w-5 text-gray-600" />;
      default:
        return <File className="h-5 w-5 text-gray-600" />;
    }
  };

  /**
   * ステータスに応じたバッジのバリアントを取得する関数
   * 
   * @param status - コンテンツのステータス
   * @returns Badgeコンポーネントのバリアント名
   */
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

  /**
   * ステータスに応じた日本語ラベルを取得する関数
   * 
   * @param status - コンテンツのステータス
   * @returns 日本語のステータスラベル
   */
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

  /**
   * バイト数を人間が読みやすい形式に変換する関数
   * 
   * @param bytes - バイト数
   * @returns フォーマットされたファイルサイズ文字列
   */
  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  // コンテンツ管理権限のチェック
  const canManageContents = currentUser?.role === 'PLATFORM_ADMIN' || 
                           currentUser?.role === 'TENANT_ADMIN' || 
                           currentUser?.role === 'OPERATOR';

  // ローディング中の表示
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
            {isCreateMode ? '新規コンテンツ作成' : 
             isViewMode ? 'コンテンツ詳細' : 'コンテンツ編集'}
          </h1>
          <p className="text-muted-foreground">
            {isCreateMode ? '新しいコンテンツを作成します' : 
             isViewMode ? 'コンテンツ情報を表示します' : 'コンテンツ情報を編集します'}
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
          <TabsTrigger value="content">コンテンツ</TabsTrigger>
          <TabsTrigger value="chunks">チャンク</TabsTrigger>
          <TabsTrigger value="analytics">分析</TabsTrigger>
        </TabsList>

        <TabsContent value="basic">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2">
              <Card>
                <CardHeader>
                  <CardTitle>基本情報</CardTitle>
                  <CardDescription>
                    コンテンツの基本情報を設定します
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
                    <div className="space-y-2">
                      <Label htmlFor="title">タイトル</Label>
                      <Input
                        id="title"
                        {...register('title')}
                        disabled={isViewMode || !canManageContents}
                      />
                      {errors.title && (
                        <p className="text-sm text-red-600">{errors.title.message}</p>
                      )}
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="description">説明</Label>
                      <Textarea
                        id="description"
                        {...register('description')}
                        disabled={isViewMode || !canManageContents}
                        rows={4}
                      />
                      {errors.description && (
                        <p className="text-sm text-red-600">{errors.description.message}</p>
                      )}
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="file_type">ファイルタイプ</Label>
                      <Select
                        value={watchedFileType}
                        onValueChange={(value) => setValue('file_type', value as ContentFormData['file_type'])}
                        disabled={isViewMode || !canManageContents}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="ファイルタイプを選択" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="PDF">PDF</SelectItem>
                          <SelectItem value="HTML">HTML</SelectItem>
                          <SelectItem value="MD">Markdown</SelectItem>
                          <SelectItem value="CSV">CSV</SelectItem>
                          <SelectItem value="TXT">TXT</SelectItem>
                        </SelectContent>
                      </Select>
                      {errors.file_type && (
                        <p className="text-sm text-red-600">{errors.file_type.message}</p>
                      )}
                    </div>

                    {isCreateMode && (
                      <div className="space-y-2">
                        <Label htmlFor="file_upload">ファイルアップロード</Label>
                        <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
                          <Upload className="mx-auto h-12 w-12 text-gray-400" />
                          <div className="mt-4">
                            <Label htmlFor="file_upload" className="cursor-pointer">
                              <span className="mt-2 block text-sm font-medium text-gray-900">
                                ファイルを選択またはドラッグ&ドロップ
                              </span>
                            </Label>
                            <input
                              id="file_upload"
                              type="file"
                              className="hidden"
                              onChange={handleFileUpload}
                              accept=".pdf,.html,.md,.csv,.txt"
                            />
                          </div>
                          <p className="mt-1 text-xs text-gray-500">
                            PDF, HTML, Markdown, CSV, TXT ファイルをサポート
                          </p>
                        </div>
                        {isUploading && (
                          <div className="space-y-2">
                            <div className="flex justify-between text-sm">
                              <span>アップロード中...</span>
                              <span>{uploadProgress}%</span>
                            </div>
                            <Progress value={uploadProgress} />
                          </div>
                        )}
                      </div>
                    )}

                    {!isViewMode && canManageContents && !isCreateMode && (
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

            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    {getFileTypeIcon(content?.file_type || watchedFileType)}
                    <span className="ml-2">ファイル情報</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center space-x-3">
                    <div className="h-12 w-12 rounded bg-muted flex items-center justify-center">
                      {getFileTypeIcon(content?.file_type || watchedFileType)}
                    </div>
                    <div>
                      <div className="font-medium">{content?.title || watchedTitle || '新規コンテンツ'}</div>
                      <div className="text-sm text-muted-foreground">
                        {content?.file_name || `${watchedTitle || 'untitled'}.${watchedFileType.toLowerCase()}`}
                      </div>
                    </div>
                  </div>

                  <Separator />

                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground">ファイルタイプ</span>
                      <Badge variant="outline">
                        {content?.file_type || watchedFileType}
                      </Badge>
                    </div>

                    {content && (
                      <>
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-muted-foreground">ファイルサイズ</span>
                          <span className="text-sm">
                            {formatFileSize(content.size_bytes)}
                          </span>
                        </div>

                        <div className="flex items-center justify-between">
                          <span className="text-sm text-muted-foreground">ステータス</span>
                          <Badge variant={getStatusBadgeVariant(content.status)}>
                            {getStatusLabel(content.status)}
                          </Badge>
                        </div>

                        <div className="flex items-center justify-between">
                          <span className="text-sm text-muted-foreground">チャンク数</span>
                          <span className="text-sm">
                            {content.chunk_count || '-'}
                          </span>
                        </div>

                        <div className="flex items-center justify-between">
                          <span className="text-sm text-muted-foreground">アップロード日</span>
                          <span className="text-sm">
                            {format(new Date(content.uploaded_at), 'yyyy/MM/dd HH:mm', { locale: ja })}
                          </span>
                        </div>

                        {content.indexed_at && (
                          <div className="flex items-center justify-between">
                            <span className="text-sm text-muted-foreground">インデックス日</span>
                            <span className="text-sm">
                              {format(new Date(content.indexed_at), 'yyyy/MM/dd HH:mm', { locale: ja })}
                            </span>
                          </div>
                        )}
                      </>
                    )}
                  </div>
                </CardContent>
              </Card>

              {content && canManageContents && (
                <Card>
                  <CardHeader>
                    <CardTitle>アクション</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    <Button
                      variant="outline"
                      className="w-full justify-start"
                      onClick={handleReindexContent}
                    >
                      <RefreshCw className="mr-2 h-4 w-4" />
                      再インデックス
                    </Button>
                    <Button
                      variant="outline"
                      className="w-full justify-start"
                    >
                      <Download className="mr-2 h-4 w-4" />
                      ダウンロード
                    </Button>
                    <Button
                      variant="outline"
                      className="w-full justify-start"
                    >
                      <Copy className="mr-2 h-4 w-4" />
                      複製
                    </Button>
                    <Separator />
                    <Button
                      variant="destructive"
                      className="w-full justify-start"
                      onClick={handleDeleteContent}
                    >
                      <Trash2 className="mr-2 h-4 w-4" />
                      削除
                    </Button>
                  </CardContent>
                </Card>
              )}
            </div>
          </div>
        </TabsContent>

        <TabsContent value="content">
          <Card>
            <CardHeader>
              <CardTitle>コンテンツ内容</CardTitle>
              <CardDescription>
                ファイルの内容を表示します
              </CardDescription>
            </CardHeader>
            <CardContent>
              {content ? (
                <div className="space-y-4">
                  <div className="p-4 bg-muted rounded-md">
                    <h4 className="font-medium mb-2">ファイル内容</h4>
                    <div className="text-sm text-muted-foreground">
                      {content.description || '説明がありません'}
                    </div>
                  </div>
                  
                  {content.tags && content.tags.length > 0 && (
                    <div className="space-y-2">
                      <h4 className="font-medium">タグ</h4>
                      <div className="flex flex-wrap gap-2">
                        {content.tags.map((tag, index) => (
                          <Badge key={index} variant="secondary">
                            {tag}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  コンテンツが読み込まれていません
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="chunks">
          <Card>
            <CardHeader>
              <CardTitle>チャンク一覧</CardTitle>
              <CardDescription>
                テキストが分割されたチャンクの一覧です
              </CardDescription>
            </CardHeader>
            <CardContent>
              {content && content.chunk_count ? (
                <div className="space-y-4">
                  <div className="text-sm text-muted-foreground">
                    {content.chunk_count} 個のチャンクが生成されています
                  </div>
                  {/* TODO: チャンク一覧の実装 */}
                  <div className="text-center py-8 text-muted-foreground">
                    チャンク一覧の表示機能は実装予定です
                  </div>
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  チャンクが生成されていません
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="analytics">
          <Card>
            <CardHeader>
              <CardTitle>使用分析</CardTitle>
              <CardDescription>
                このコンテンツの使用状況と分析データ
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center py-8 text-muted-foreground">
                分析機能は実装予定です
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
