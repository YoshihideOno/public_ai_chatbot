/**
 * 認証コンテキスト
 * 
 * このファイルはユーザー認証状態を管理するためのReact Contextを定義します。
 * ログイン、ログアウト、ユーザー情報の取得・更新などの認証関連の機能を
 * アプリケーション全体で共有できるようにします。
 * 
 * 主な機能:
 * - ユーザー認証状態の管理
 * - ログイン・ログアウト処理
 * - トークンの自動リフレッシュ
 * - 認証状態の永続化
 */

'use client';

import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { User, LoginRequest, apiClient } from '@/lib/api';

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (credentials: LoginRequest) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  /**
   * 認証プロバイダー
   * 
   * 認証状態を管理し、子コンポーネントに認証関連の機能を提供します。
   * ユーザー情報、ローディング状態、認証フラグを管理します。
   * 
   * 属性:
   *   children: 子コンポーネント
   */
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const isAuthenticated = !!user;

  const login = async (credentials: LoginRequest) => {
    /**
     * ユーザーログイン処理
     * 
     * 引数:
     *   credentials: ログイン認証情報（メール、パスワード）
     * 
     * 戻り値:
     *   Promise<void>: 非同期処理
     * 
     * 例外:
     *   Error: ログイン失敗時のエラー
     */
    try {
      const response = await apiClient.login(credentials);
      
      // トークンをローカルストレージに保存
      localStorage.setItem('access_token', response.access_token);
      localStorage.setItem('refresh_token', response.refresh_token);
      
      setUser(response.user);
      
      // ログイン成功後、ダッシュボードにリダイレクト
      window.location.href = '/dashboard';
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    }
  };

  const logout = async () => {
    /**
     * ユーザーログアウト処理
     * 
     * 戻り値:
     *   Promise<void>: 非同期処理
     * 
     * 例外:
     *   Error: ログアウト失敗時のエラー
     */
    try {
      await apiClient.logout();
    } catch (error) {
      console.error('Logout failed:', error);
    } finally {
      setUser(null);
      // トークンを削除
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      // ログアウト後、ランディングページにリダイレクト
      window.location.href = '/';
    }
  };

  const refreshUser = async () => {
    try {
      const userData = await apiClient.getCurrentUser();
      setUser(userData);
    } catch (error) {
      console.error('Failed to refresh user:', error);
      setUser(null);
    }
  };

  // 初期化時にユーザー情報を取得
  useEffect(() => {
    const initAuth = async () => {
      const token = localStorage.getItem('access_token');
      if (token) {
        try {
          await refreshUser();
        } catch (error) {
          console.error('Failed to initialize auth:', error);
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
        }
      }
      setIsLoading(false);
    };

    initAuth();
  }, []);

  const value: AuthContextType = {
    user,
    isLoading,
    isAuthenticated,
    login,
    logout,
    refreshUser,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
