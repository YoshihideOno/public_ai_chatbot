"use client";
import { UsersList } from '@/components/users/UsersList';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { useAuth } from '@/contexts/AuthContext';
import React from 'react';

export default function UsersPage() {
  const { user } = useAuth();
  return (
    <ProtectedRoute>
      {(user?.role === 'PLATFORM_ADMIN' || user?.role === 'TENANT_ADMIN' || user?.role === 'AUDITOR') ? (
        <UsersList />
      ) : (
        <div className="flex items-center justify-center min-h-[50vh]">
          <div className="text-center">
            <h1 className="text-2xl font-bold text-red-600 mb-4">アクセス拒否</h1>
            <p className="text-muted-foreground">このページにアクセスする権限がありません。</p>
          </div>
        </div>
      )}
    </ProtectedRoute>
  );
}
