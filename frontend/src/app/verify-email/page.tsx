/**
 * メール確認ページ
 * 
 * ユーザーがメール内の確認リンクをクリックした際に表示されるページです。
 * トークンを検証し、アカウントの有効化を行います。
 */

'use client';

import { Suspense, useCallback, useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { CheckCircle, XCircle, Loader2 } from 'lucide-react';
import { ApiClient } from '@/lib/api';

export default function VerifyEmailPage() {
  return (
    <Suspense fallback={<VerifyEmailFallback />}>
      <VerifyEmailContent />
    </Suspense>
  );
}

function VerifyEmailContent() {
  const searchParams = useSearchParams();
  const token = searchParams.get('token');
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [message, setMessage] = useState('');
  const [userEmail, setUserEmail] = useState('');

  interface VerifyEmailError {
    response?: {
      data?: {
        detail?: string;
      };
    };
    message?: string;
  }

  const verifyEmail = useCallback(async (token: string) => {
    try {
      const apiClient = new ApiClient();
      const response = await apiClient.verifyEmail(token);
      
      setStatus('success');
      setMessage(response.message);
      setUserEmail(response.email);
    } catch (error: unknown) {
      console.error('Email verification error:', error);
      setStatus('error');
      const verificationError = error as VerifyEmailError;
      const detail =
        verificationError.response?.data?.detail ??
        verificationError.message ??
        'メール確認処理中にエラーが発生しました。';
      setMessage(detail);
    }
  }, []);

  useEffect(() => {
    if (!token) {
      setStatus('error');
      setMessage('確認トークンが見つかりません。');
      return;
    }

    verifyEmail(token);
  }, [token, verifyEmail]);

  const handleLoginRedirect = () => {
    window.location.href = '/login';
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <Card>
          <CardHeader className="text-center">
            <CardTitle className="text-2xl font-bold">
              {status === 'loading' && 'メール確認中...'}
              {status === 'success' && 'メール確認完了'}
              {status === 'error' && 'メール確認エラー'}
            </CardTitle>
            <CardDescription>
              {status === 'loading' && 'アカウントの有効化を行っています'}
              {status === 'success' && 'アカウントが正常に有効化されました'}
              {status === 'error' && 'メール確認に失敗しました'}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {status === 'loading' && (
              <div className="flex flex-col items-center space-y-4">
                <Loader2 className="h-12 w-12 animate-spin text-blue-600" />
                <p className="text-gray-600">確認トークンを検証しています...</p>
              </div>
            )}

            {status === 'success' && (
              <div className="space-y-4">
                <div className="flex justify-center">
                  <CheckCircle className="h-12 w-12 text-green-600" />
                </div>
                <Alert>
                  <AlertDescription>
                    {message}
                    {userEmail && (
                      <div className="mt-2">
                        <strong>メールアドレス:</strong> {userEmail}
                      </div>
                    )}
                  </AlertDescription>
                </Alert>
                <Button 
                  onClick={handleLoginRedirect}
                  className="w-full"
                >
                  ログインページに移動
                </Button>
              </div>
            )}

            {status === 'error' && (
              <div className="space-y-4">
                <div className="flex justify-center">
                  <XCircle className="h-12 w-12 text-red-600" />
                </div>
                <Alert variant="destructive">
                  <AlertDescription>
                    {message}
                  </AlertDescription>
                </Alert>
                <div className="space-y-2">
                  <Button 
                    onClick={() => window.location.href = '/register'}
                    variant="outline"
                    className="w-full"
                  >
                    新規登録ページに戻る
                  </Button>
                  <Button 
                    onClick={handleLoginRedirect}
                    className="w-full"
                  >
                    ログインページに移動
                  </Button>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function VerifyEmailFallback() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <Card>
          <CardHeader className="text-center">
            <CardTitle className="text-2xl font-bold">メール確認中...</CardTitle>
            <CardDescription>アカウントの有効化を行っています</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="flex flex-col items-center space-y-4">
              <Loader2 className="h-12 w-12 animate-spin text-blue-600" />
              <p className="text-gray-600">確認トークンを検証しています...</p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
