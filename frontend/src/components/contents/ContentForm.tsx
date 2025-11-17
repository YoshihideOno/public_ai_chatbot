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
import { isAxiosError } from 'axios';
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
import { apiClient, Content } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import { logger } from '@/utils/logger';
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
  file_type: z.enum(['PDF', 'HTML', 'MD', 'CSV', 'TXT']).optional(),
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
 * ファイル拡張子からファイルタイプを判定する関数
 * @param filename - ファイル名
 * @returns ファイルタイプ（PDF, HTML, MD, CSV, TXT）
 */
function getFileTypeFromFilename(filename: string): 'PDF' | 'HTML' | 'MD' | 'CSV' | 'TXT' {
  const extension = filename.toLowerCase().split('.').pop() || '';
  switch (extension) {
    case 'pdf':
      return 'PDF';
    case 'html':
    case 'htm':
      return 'HTML';
    case 'md':
    case 'markdown':
      return 'MD';
    case 'csv':
      return 'CSV';
    case 'txt':
      return 'TXT';
    default:
      return 'TXT';
  }
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
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [inputType, setInputType] = useState<'file' | 'url'>('file');
  const [urlInput, setUrlInput] = useState<string>('');
  const [urlFileType, setUrlFileType] = useState<'PDF' | 'HTML' | 'MD' | 'CSV' | 'TXT' | null>(null);
  // ドラッグ中の見た目制御
  const [isDragging, setIsDragging] = useState(false);
  
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
    trigger,
    formState: { errors, isSubmitting },
  } = useForm<ContentFormData>({
    resolver: zodResolver(contentSchema),
    mode: 'onBlur', // フォーカスを外した時点でバリデーションを実行
    reValidateMode: 'onBlur', // 再バリデーションもフォーカスを外した時点で実行
    defaultValues: {
      tags: [],
    },
  });

  // フォームの監視対象フィールド
  const watchedFileType = watch('file_type');
  const watchedTitle = watch('title');

  /**
   * コンテンツ情報を取得してフォームに設定する関数
   * APIからコンテンツデータを取得し、フォームフィールドに値を設定します
   */
  const fetchContent = useCallback(async () => {
    if (!contentId) return;
    
    // 新規作成モードの場合は取得しない
    if (contentId === 'upload' || isCreateMode) return;

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
      logger.error('コンテンツ情報の取得に失敗', err);
      setError('コンテンツ情報の取得に失敗しました');
    } finally {
      setIsLoading(false);
    }
  }, [contentId, isCreateMode, setValue]);

  useEffect(() => {
    if (contentId && !isCreateMode) {
      fetchContent();
    }
  }, [contentId, isCreateMode, fetchContent]);

  /**
   * フォーム送信処理
   * コンテンツの作成または更新を行い、成功時はコンテンツ一覧ページに遷移します
   * 新規作成時はファイルまたはURLが必須です
   * 
   * @param data - フォームから送信されたデータ
   */
  const onSubmit = async (data: ContentFormData) => {
    setIsLoading(true);
    setError(null);

    try {
      if (isCreateMode) {
        // 新規作成時はファイルまたはURLが必須
        if (inputType === 'file' && !selectedFile) {
          setError('ファイルを選択してください');
          setIsLoading(false);
          return;
        }
        
        if (inputType === 'url' && !urlInput.trim()) {
          setError('URLを入力してください');
          setIsLoading(false);
          return;
        }

        // URL形式のバリデーション
        if (inputType === 'url') {
          try {
            new URL(urlInput);
          } catch {
            setError('有効なURLを入力してください');
            setIsLoading(false);
            return;
          }
        }

        // 重処理はサーバ側で非同期化するため、フォーム側は即時遷移のみ
        setIsUploading(true);

        if (inputType === 'file' && selectedFile) {
          // ファイルアップロード
          await apiClient.uploadFile(
            selectedFile,
            data.title,
            data.description,
            data.tags || []
          );
        } else if (inputType === 'url' && urlInput.trim()) {
          // URLからコンテンツ作成
          const res = await apiClient.createContent({
            title: data.title,
            description: data.description,
            tags: data.tags || [],
            content_type: urlFileType || 'HTML',
            file_url: urlInput.trim(),
          });
          // 202 Accepted（BG開始）の場合はモーダル風アラートで案内
          const maybeAccepted = res as any;
          if (maybeAccepted && typeof maybeAccepted === 'object' && maybeAccepted.status === 'PROCESSING') {
            alert(maybeAccepted.message || '処理を開始しました。後で一覧で完了をご確認ください。');
          }
        }

        router.push('/contents');
      } else if (contentId) {
        await apiClient.updateContent(contentId, data);
        router.push('/contents');
      }
    } catch (err: unknown) {
      // 保存失敗時の詳細はUIで表示するため、コンソールは冗長なエラー出力を避ける
      logger.debug('コンテンツの保存に失敗', err);
      
      if (isAxiosError(err) && err.code === 'ECONNABORTED') {
        setError('リクエストがタイムアウトしました。数秒後にコンテンツ一覧を確認してください。');
        return;
      }
      
      if (err && typeof err === 'object' && 'response' in err) {
        const errorResponse = err as { response?: { status?: number; data?: { detail?: string; error?: { message?: string } } } };
        
        // 409 Conflict エラー（ファイル名重複）の処理
        if (errorResponse.response?.status === 409) {
          const message = errorResponse.response.data?.detail || '同一ファイル名のファイルが既に存在します';
          setError(message);
        } else if (errorResponse.response?.data?.error?.message) {
          setError(errorResponse.response.data.error.message);
        } else if (errorResponse.response?.data?.detail) {
          setError(errorResponse.response.data.detail);
        } else {
          setError('コンテンツの保存に失敗しました');
        }
      } else {
        setError('コンテンツの保存に失敗しました');
      }
    } finally {
      setIsLoading(false);
      setIsUploading(false);
    }
  };

  /**
   * ファイル選択処理
   * 選択されたファイルを状態に保持し、ファイルタイプを自動設定します
   * 自動アップロードは行わず、保存ボタンでアップロードします
   * 
   * @param event - ファイル入力の変更イベント
   */
  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) {
      setSelectedFile(null);
      return;
    }

    setSelectedFile(file);
    
    // ファイルタイプを自動設定
    const fileType = getFileTypeFromFilename(file.name);
    setValue('file_type', fileType);

    // タイトルが空の場合はファイル名（拡張子除く）を設定
    if (!watchedTitle) {
      const fileNameWithoutExtension = file.name.replace(/\.[^/.]+$/, '');
      setValue('title', fileNameWithoutExtension);
    }
  };

  /**
   * URLからファイルタイプを判定する関数
   * URLからファイルを取得して拡張子からファイルタイプを判定します
   * 
   * @param url - 判定するURL
   * @returns ファイルタイプ（PDF, HTML, MD, CSV, TXT）
   */
  const detectFileTypeFromUrl = async (url: string): Promise<'PDF' | 'HTML' | 'MD' | 'CSV' | 'TXT'> => {
    try {
      // URLからファイルを取得してヘッダーを確認
      const response = await fetch(url, { method: 'HEAD', mode: 'no-cors' }).catch(() => null);
      
      // CORS制限がある場合は、URLパスから拡張子を判定
      const urlPath = new URL(url).pathname;
      const extension = urlPath.toLowerCase().split('.').pop() || '';
      
      // Content-Typeヘッダーから判定を試みる（CORS許可時）
      if (response && response.headers) {
        const contentType = response.headers.get('content-type');
        if (contentType) {
          if (contentType.includes('pdf')) return 'PDF';
          if (contentType.includes('html')) return 'HTML';
          if (contentType.includes('markdown') || contentType.includes('text/markdown')) return 'MD';
          if (contentType.includes('csv') || contentType.includes('text/csv')) return 'CSV';
          if (contentType.includes('text/plain')) return 'TXT';
          }
      }
      
      // 拡張子から判定
      return getFileTypeFromFilename(urlPath || extension);
    } catch (error) {
      logger.error('URLからのファイルタイプ判定エラー', error);
      // エラー時はデフォルトでHTMLを返す
      return 'HTML';
    }
  };

  /**
   * URL入力変更処理
   * URLを状態に保持し、ファイルタイプを自動判定します
   * 
   * @param event - 入力フィールドの変更イベント
   */
  const handleUrlChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const url = event.target.value;
    setUrlInput(url);
    
    if (!url.trim()) {
      setUrlFileType(null);
      return;
    }

    // URLの形式をバリデーション
    try {
      new URL(url);
      
      // ファイルタイプを判定
      const fileType = await detectFileTypeFromUrl(url);
      setUrlFileType(fileType);
      setValue('file_type', fileType);
      
      // タイトルが空の場合はURLパスからファイル名を設定
      if (!watchedTitle) {
        try {
          const urlObj = new URL(url);
          const pathName = urlObj.pathname;
          const fileName = pathName.split('/').pop() || urlObj.hostname;
          const fileNameWithoutExtension = fileName.replace(/\.[^/.]+$/, '') || 'untitled';
          setValue('title', fileNameWithoutExtension);
        } catch {
          setValue('title', 'untitled');
        }
      }
    } catch {
      // 無効なURLの場合はエラーを表示しない（入力中の場合があるため）
      setUrlFileType(null);
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
      logger.error('コンテンツの削除に失敗', err);
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
      logger.error('再インデックスの開始に失敗', err);
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
          <TabsTrigger value="preview">プレビュー</TabsTrigger>
          <TabsTrigger value="chunks">チャンク</TabsTrigger>
          <TabsTrigger value="analytics">分析</TabsTrigger>
        </TabsList>

        <TabsContent value="basic">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2">
              <Card>
                <CardHeader>
                  <CardTitle>基本情報</CardTitle>
                </CardHeader>
                <CardContent>
                  <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
                    <div className="space-y-2">
                      <Label htmlFor="title">タイトル</Label>
                      <Input
                        id="title"
                        {...register('title', {
                          onBlur: () => trigger('title'), // フォーカスを外した時点でバリデーションを実行
                        })}
                        disabled={isViewMode || !canManageContents}
                        aria-invalid={errors.title ? 'true' : 'false'}
                      />
                      {errors.title && (
                        <p className="text-sm text-red-600" role="alert">{errors.title.message}</p>
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

                    {isCreateMode && (
                      <div className="space-y-4">
                        <div className="space-y-2">
                          <Label>入力方法 <span className="text-red-500">*</span></Label>
                          <div className="flex items-center space-x-6">
                            <div className="flex items-center space-x-2">
                              <input
                                type="radio"
                                id="input_type_file"
                                name="input_type"
                                value="file"
                                checked={inputType === 'file'}
                                onChange={() => {
                                  setInputType('file');
                                  setUrlInput('');
                                  setUrlFileType(null);
                                }}
                                disabled={isViewMode || !canManageContents}
                                className="h-4 w-4 text-primary focus:ring-primary"
                              />
                              <Label htmlFor="input_type_file" className="cursor-pointer">
                                ファイルをアップロード
                              </Label>
                            </div>
                            <div className="flex items-center space-x-2">
                              <input
                                type="radio"
                                id="input_type_url"
                                name="input_type"
                                value="url"
                                checked={inputType === 'url'}
                                onChange={() => {
                                  setInputType('url');
                                  setSelectedFile(null);
                                }}
                                disabled={isViewMode || !canManageContents}
                                className="h-4 w-4 text-primary focus:ring-primary"
                              />
                              <Label htmlFor="input_type_url" className="cursor-pointer">
                                URLを入力
                              </Label>
                            </div>
                          </div>
                        </div>

                        {inputType === 'file' && (
                      <div className="space-y-2">
                            <Label htmlFor="file_upload">ファイルアップロード <span className="text-red-500">*</span></Label>
                            <div
                              className={`border-2 border-dashed rounded-lg p-6 text-center ${isDragging ? 'border-primary bg-primary/5' : 'border-gray-300'}`}
                              onDragEnter={(e) => { e.preventDefault(); e.stopPropagation(); setIsDragging(true); }}
                              onDragOver={(e) => { e.preventDefault(); e.stopPropagation(); }}
                              onDragLeave={(e) => { e.preventDefault(); e.stopPropagation(); setIsDragging(false); }}
                              onDrop={(e) => {
                                e.preventDefault();
                                e.stopPropagation();
                                setIsDragging(false);
                                const file = e.dataTransfer?.files?.[0];
                                if (!file) return;
                                const dt = new DataTransfer();
                                dt.items.add(file);
                                const input = document.getElementById('file_upload') as HTMLInputElement | null;
                                if (input) {
                                  input.files = dt.files;
                                  input.dispatchEvent(new Event('change', { bubbles: true }));
                                }
                              }}
                            >
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
                                  disabled={isViewMode || !canManageContents}
                            />
                          </div>
                              {selectedFile && (
                                <div className="mt-2">
                                  <p className="text-sm text-green-600">選択済み: {selectedFile.name}</p>
                                  <p className="text-xs text-gray-500">
                                    ファイルタイプ: {getFileTypeFromFilename(selectedFile.name)}
                                  </p>
                                </div>
                              )}
                          <p className="mt-1 text-xs text-gray-500">
                            PDF, HTML, Markdown, CSV, TXT ファイルをサポート
                          </p>
                        </div>
                            {error && inputType === 'file' && !selectedFile && (
                              <p className="text-sm text-red-600">{error}</p>
                            )}
                          </div>
                        )}

                        {inputType === 'url' && (
                          <div className="space-y-2">
                            <Label htmlFor="url_input">URL <span className="text-red-500">*</span></Label>
                            <Input
                              id="url_input"
                              type="url"
                              placeholder="https://example.com/document.pdf"
                              value={urlInput}
                              onChange={handleUrlChange}
                              disabled={isViewMode || !canManageContents || isUploading}
                              className="font-mono text-sm"
                            />
                            {urlFileType && (
                              <div className="mt-2">
                                <p className="text-sm text-green-600">
                                  検出されたファイルタイプ: {urlFileType}
                                </p>
                              </div>
                            )}
                            {error && inputType === 'url' && !urlInput.trim() && (
                              <p className="text-sm text-red-600">{error}</p>
                            )}
                            <p className="text-xs text-gray-500">
                              URLからファイルを取得してコンテンツを作成します
                            </p>
                          </div>
                        )}

                        {isUploading && (
                          <div className="space-y-2">
                            <div className="flex justify-between text-sm">
                              <span>処理中...</span>
                              <span>{uploadProgress}%</span>
                            </div>
                            <Progress value={uploadProgress} />
                          </div>
                        )}
                      </div>
                    )}

                    {!isViewMode && canManageContents && (
                      <div className="flex justify-end space-x-2">
                        <Button type="button" variant="outline" onClick={() => router.back()}>
                          キャンセル
                        </Button>
                        <Button 
                          type="submit" 
                          disabled={
                            isSubmitting || 
                            isUploading || 
                            (isCreateMode && inputType === 'file' && !selectedFile) ||
                            (isCreateMode && inputType === 'url' && !urlInput.trim())
                          }
                        >
                          <Save className="mr-2 h-4 w-4" />
                          {isSubmitting || isUploading ? '保存中...' : '保存'}
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
                    {getFileTypeIcon(content?.file_type || watchedFileType || 'TXT')}
                    <span className="ml-2">ファイル情報</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center space-x-3">
                    <div className="h-12 w-12 rounded bg-muted flex items-center justify-center">
                      {getFileTypeIcon(content?.file_type || watchedFileType || 'TXT')}
                    </div>
                    <div>
                      <div className="font-medium">{content?.title || watchedTitle || '新規コンテンツ'}</div>
                      <div className="text-sm text-muted-foreground">
                        {content?.file_name || (selectedFile ? selectedFile.name : `${watchedTitle || 'untitled'}.${(watchedFileType || 'TXT').toLowerCase()}`)}
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
                            {formatFileSize(content.file_size ?? content.size_bytes ?? 0)}
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

              {null}
            </div>
          </div>
        </TabsContent>

        <TabsContent value="preview">
          <Card>
            <CardHeader>
              <CardTitle>プレビュー</CardTitle>
            </CardHeader>
            <CardContent>
              {content ? (
                <div className="space-y-4">
                  {(() => {
                    type PreviewChunk = { id?: string; chunk_index?: number; content?: string; created_at?: string };
                    const ft = content.file_type as string | undefined;
                    const chunksArr = (content as unknown as { chunks?: PreviewChunk[] })?.chunks;
                    const previewText = chunksArr && chunksArr.length > 0
                      ? chunksArr.slice(0, 3).map(c => c.content).join('\n\n')
                      : (content.description || 'プレビュー可能なテキストがありません');
                    if (ft === 'MD' || ft === 'TXT') {
                      return (
                        <div>
                          <div className="text-sm text-muted-foreground mb-2">先頭数チャンクの抜粋</div>
                          <pre className="whitespace-pre-wrap break-words p-3 bg-muted rounded-md text-sm">{previewText}</pre>
                        </div>
                      );
                    }
                    if (ft === 'PDF' || ft === 'HTML') {
                      return (
                        <div className="space-y-2">
                          <div className="text-sm text-muted-foreground">このファイルタイプは外部ビューアでの表示を推奨します。</div>
                          <div>
                            <Button asChild variant="outline" size="sm">
                              <a href="#" target="_blank" rel="noopener noreferrer">別タブで開く（リンク未設定）</a>
                            </Button>
                          </div>
                          {chunksArr && chunksArr.length > 0 && (
                            <div>
                              <div className="text-sm text-muted-foreground mb-2">テキスト抜粋</div>
                              <pre className="whitespace-pre-wrap break-words p-3 bg-muted rounded-md text-sm">{previewText}</pre>
                            </div>
                          )}
                        </div>
                      );
                    }
                    return (
                      <pre className="whitespace-pre-wrap break-words p-3 bg-muted rounded-md text-sm">{previewText}</pre>
                    );
                  })()}

                  {content.tags && content.tags.length > 0 && (
                    <div className="space-y-2">
                      <h4 className="font-medium">タグ</h4>
                      <div className="flex flex-wrap gap-2">
                        {content.tags.map((tag: string, index: number) => (
                          <Badge key={index} variant="secondary">
                            {tag}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">コンテンツが読み込まれていません</div>
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
              {(() => {
                type PreviewChunk = { id?: string; chunk_index?: number; content?: string; created_at?: string };
                const chunksArr = (content as unknown as { chunks?: PreviewChunk[] })?.chunks;
                return content && chunksArr && chunksArr.length > 0 ? (
                <div className="space-y-4">
                  <div className="text-sm text-muted-foreground">
                    {chunksArr.length} 個のチャンクが生成されています
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="text-left text-muted-foreground">
                          <th className="py-2 pr-3">#</th>
                          <th className="py-2 pr-3">文字数</th>
                          <th className="py-2 pr-3">抜粋</th>
                          <th className="py-2 pr-3">作成日時</th>
                        </tr>
                      </thead>
                      <tbody>
                        {chunksArr.map((ck, idx) => (
                          <tr key={ck.id || idx} className="border-t">
                            <td className="py-2 pr-3 align-top">{ck.chunk_index ?? idx}</td>
                            <td className="py-2 pr-3 align-top">{(ck.content?.length ?? 0).toLocaleString()}</td>
                            <td className="py-2 pr-3 align-top max-w-[640px]">
                              <div className="line-clamp-3 whitespace-pre-wrap break-words">{ck.content?.slice(0, 500) ?? ''}</div>
                            </td>
                            <td className="py-2 pr-3 align-top">{ck.created_at ? format(new Date(ck.created_at), 'yyyy/MM/dd HH:mm', { locale: ja }) : '-'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  チャンクが生成されていません
                </div>
              );})()}
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
              {content ? (
                (() => {
                  type PreviewChunk = { content?: string };
                  const chunksArr = (content as unknown as { chunks?: PreviewChunk[] })?.chunks;
                  const counts = chunksArr?.map(c => c.content?.length ?? 0) || [];
                  const chunkCount = counts.length;
                  const totalChars = counts.reduce((a, b) => a + b, 0);
                  const avgChars = chunkCount ? Math.round(totalChars / chunkCount) : 0;
                  const maxChars = counts.length ? Math.max(...counts) : 0;
                  const minChars = counts.length ? Math.min(...counts) : 0;
                  return (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <Card>
                        <CardHeader>
                          <CardTitle className="text-base">基本統計</CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-2 text-sm">
                          <div className="flex justify-between"><span className="text-muted-foreground">チャンク数</span><span>{chunkCount}</span></div>
                          <div className="flex justify-between"><span className="text-muted-foreground">総文字数</span><span>{totalChars.toLocaleString()}</span></div>
                          <div className="flex justify-between"><span className="text-muted-foreground">ステータス</span><span>{getStatusLabel(content.status)}</span></div>
                          <div className="flex justify-between"><span className="text-muted-foreground">アップロード日</span><span>{content.uploaded_at ? format(new Date(content.uploaded_at), 'yyyy/MM/dd HH:mm', { locale: ja }) : '-'}</span></div>
                          <div className="flex justify-between"><span className="text-muted-foreground">インデックス日</span><span>{content.indexed_at ? format(new Date(content.indexed_at), 'yyyy/MM/dd HH:mm', { locale: ja }) : '-'}</span></div>
                        </CardContent>
                      </Card>
                      <Card>
                        <CardHeader>
                          <CardTitle className="text-base">チャンク文字数統計</CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-2 text-sm">
                          <div className="flex justify-between"><span className="text-muted-foreground">平均</span><span>{avgChars.toLocaleString()}</span></div>
                          <div className="flex justify-between"><span className="text-muted-foreground">最大</span><span>{maxChars.toLocaleString()}</span></div>
                          <div className="flex justify-between"><span className="text-muted-foreground">最小</span><span>{minChars.toLocaleString()}</span></div>
                        </CardContent>
                      </Card>
                    </div>
                  );
                })()
              ) : (
                <div className="text-center py-8 text-muted-foreground">コンテンツが読み込まれていません</div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
