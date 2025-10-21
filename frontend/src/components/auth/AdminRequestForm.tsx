/**
 * 管理者権限申請フォームコンポーネント
 * 
 * このファイルはテナント管理者権限の申請用フォームコンポーネントを定義します。
 * 既存の運用者・監査者がテナント管理者権限を申請する機能を提供します。
 * 
 * 主な機能:
 * - 管理者権限申請フォーム
 * - 申請理由の入力
 * - 申請状況の確認
 * - エラーハンドリング
 */

'use client';

import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { apiClient, AdminRequest, ApiError } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import { Loader2, Shield, Clock, CheckCircle, XCircle } from 'lucide-react';

const adminRequestSchema = z.object({
  reason: z.string().min(10, '申請理由は10文字以上で入力してください').max(500, '申請理由は500文字以内で入力してください'),
});

type AdminRequestFormData = z.infer<typeof adminRequestSchema>;


export function AdminRequestForm() {
  /**
   * 管理者権限申請フォームコンポーネント
   * 
   * テナント管理者権限の申請と申請状況の確認を行うコンポーネントです。
   * ダイアログ形式で表示され、申請理由の入力と申請履歴の確認ができます。
   */
  const [isOpen, setIsOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [requests, setRequests] = useState<AdminRequest[]>([]);
  const [isLoadingRequests, setIsLoadingRequests] = useState(false);

  const { user } = useAuth();

  const form = useForm<AdminRequestFormData>({
    resolver: zodResolver(adminRequestSchema),
  });

  const onSubmit = async (data: AdminRequestFormData) => {
    /**
     * 管理者権限申請送信処理
     * 
     * 引数:
     *   data: 申請フォームデータ（申請理由）
     * 
     * 戻り値:
     *   Promise<void>: 非同期処理
     * 
     * 例外:
     *   Error: 申請送信失敗時のエラー
     */
    setIsLoading(true);
    setError(null);
    setSuccess(null);

    try {
      await apiClient.requestAdminRole(data.reason);
      setSuccess('管理者権限の申請を送信しました。承認までお待ちください。');
      form.reset();
      fetchRequests(); // 申請履歴を更新
    } catch (err: unknown) {
      console.error('Admin request error:', err);
      
      if (err && typeof err === 'object' && 'response' in err) {
        const axiosError = err as { response?: { data?: ApiError } };
        if (axiosError.response?.data?.error?.message) {
          setError(axiosError.response.data.error.message);
        } else {
          setError('申請の送信に失敗しました。');
        }
      } else if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('申請の送信に失敗しました。');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const fetchRequests = async () => {
    /**
     * 申請履歴取得処理
     * 
     * 戻り値:
     *   Promise<void>: 非同期処理
     */
    setIsLoadingRequests(true);
    try {
      const response = await apiClient.getAdminRequests();
      setRequests(response);
    } catch (err: unknown) {
      console.error('Failed to fetch admin requests:', err);
    } finally {
      setIsLoadingRequests(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'PENDING':
        return <Badge variant="secondary" className="flex items-center gap-1"><Clock className="h-3 w-3" />審査中</Badge>;
      case 'APPROVED':
        return <Badge variant="default" className="flex items-center gap-1"><CheckCircle className="h-3 w-3" />承認済み</Badge>;
      case 'REJECTED':
        return <Badge variant="destructive" className="flex items-center gap-1"><XCircle className="h-3 w-3" />却下</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('ja-JP', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // 管理者権限を持っている場合は表示しない
  if (user?.role === 'TENANT_ADMIN' || user?.role === 'PLATFORM_ADMIN') {
    return null;
  }

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" size="sm" className="flex items-center gap-2">
          <Shield className="h-4 w-4" />
          管理者権限を申請
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5" />
            テナント管理者権限申請
          </DialogTitle>
          <DialogDescription>
            テナント管理者権限が必要な場合は、申請理由を記入して申請してください。
            既存のテナント管理者が審査・承認を行います。
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* 申請フォーム */}
          <Card>
            <CardHeader>
              <CardTitle>新規申請</CardTitle>
              <CardDescription>
                管理者権限が必要な理由を詳しく記入してください
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
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
                  <Label htmlFor="reason">申請理由</Label>
                  <Textarea
                    id="reason"
                    placeholder="管理者権限が必要な理由を詳しく記入してください（例：チーム管理、設定変更、ユーザー管理など）"
                    {...form.register('reason')}
                    disabled={isLoading}
                    rows={4}
                  />
                  {form.formState.errors.reason && (
                    <p className="text-sm text-red-600">{form.formState.errors.reason.message}</p>
                  )}
                  <p className="text-xs text-gray-500">
                    {form.watch('reason')?.length || 0}/500文字
                  </p>
                </div>

                <Button
                  type="submit"
                  className="w-full"
                  disabled={isLoading}
                >
                  {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  {isLoading ? '申請中...' : '申請を送信'}
                </Button>
              </form>
            </CardContent>
          </Card>

          {/* 申請履歴 */}
          <Card>
            <CardHeader>
              <CardTitle>申請履歴</CardTitle>
              <CardDescription>
                過去の申請状況を確認できます
              </CardDescription>
            </CardHeader>
            <CardContent>
              {isLoadingRequests ? (
                <div className="flex items-center justify-center py-4">
                  <Loader2 className="h-6 w-6 animate-spin" />
                </div>
              ) : requests.length === 0 ? (
                <p className="text-gray-500 text-center py-4">申請履歴がありません</p>
              ) : (
                <div className="space-y-3">
                  {requests.map((request) => (
                    <div key={request.id} className="border rounded-lg p-4 space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium">申請 #{request.id}</span>
                        {getStatusBadge(request.status)}
                      </div>
                      <p className="text-sm text-gray-600">{request.reason}</p>
                      <div className="flex items-center justify-between text-xs text-gray-500">
                        <span>申請日: {formatDate(request.created_at)}</span>
                        {request.reviewed_at && (
                          <span>審査日: {formatDate(request.reviewed_at)}</span>
                        )}
                      </div>
                      {request.review_comment && (
                        <div className="mt-2 p-2 bg-gray-50 rounded text-sm">
                          <strong>審査コメント:</strong> {request.review_comment}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </DialogContent>
    </Dialog>
  );
}
