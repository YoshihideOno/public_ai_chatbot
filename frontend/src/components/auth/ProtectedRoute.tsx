'use client';

import React from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredRole?: 'PLATFORM_ADMIN' | 'TENANT_ADMIN' | 'OPERATOR' | 'AUDITOR';
  fallback?: React.ReactNode;
}

export function ProtectedRoute({ 
  children, 
  requiredRole, 
  fallback 
}: ProtectedRouteProps) {
  const { user, isLoading, isAuthenticated } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [isLoading, isAuthenticated, router]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return fallback || null;
  }

  if (requiredRole && user?.role !== requiredRole) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-red-600 mb-4">アクセス拒否</h1>
          <p className="text-muted-foreground">
            このページにアクセスする権限がありません。
          </p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}

export function AdminRoute({ children }: { children: React.ReactNode }) {
  return (
    <ProtectedRoute requiredRole="PLATFORM_ADMIN">
      {children}
    </ProtectedRoute>
  );
}

export function TenantAdminRoute({ children }: { children: React.ReactNode }) {
  return (
    <ProtectedRoute requiredRole="TENANT_ADMIN">
      {children}
    </ProtectedRoute>
  );
}

export function OperatorRoute({ children }: { children: React.ReactNode }) {
  return (
    <ProtectedRoute requiredRole="OPERATOR">
      {children}
    </ProtectedRoute>
  );
}
