import { Suspense } from 'react';
import { PasswordResetForm } from '@/components/auth/PasswordResetForm';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Loader2 } from 'lucide-react';

export default function PasswordResetPage() {
  return (
    <Suspense fallback={<PasswordResetFallback />}>
      <PasswordResetForm />
    </Suspense>
  );
}

function PasswordResetFallback() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <Card>
          <CardHeader className="text-center">
            <CardTitle className="text-2xl font-bold">準備中...</CardTitle>
            <CardDescription>パスワードリセット画面を読み込んでいます</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col items-center space-y-4">
            <Loader2 className="h-12 w-12 animate-spin text-blue-600" />
            <p className="text-gray-600 text-sm">少々お待ちください</p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
