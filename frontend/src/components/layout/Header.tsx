/**
 * ヘッダーコンポーネント
 * 
 * このファイルはアプリケーションのヘッダー部分を定義します。
 * ナビゲーション、ユーザーメニュー、ログアウト機能、レスポンシブ対応などの
 * 機能を提供します。
 * 
 * 主な機能:
 * - ナビゲーションメニュー
 * - ユーザー情報表示
 * - ロール別メニュー表示
 * - ログアウト機能
 * - レスポンシブ対応
 * - アクセシビリティ対応
 */

'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Badge } from '@/components/ui/badge';
import { useAuth } from '@/contexts/AuthContext';
import { 
  Users, 
  Building2, 
  FileText, 
  BarChart3, 
  Settings, 
  LogOut,
  Menu,
  X
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface HeaderProps {
  onMenuToggle?: () => void;
  isMenuOpen?: boolean;
}

export function Header({ onMenuToggle, isMenuOpen }: HeaderProps) {
  /**
   * ヘッダーコンポーネント
   * 
   * アプリケーションのヘッダー部分を表示し、ナビゲーションとユーザー操作を提供します。
   * 認証状態に応じた表示制御とロール別メニュー表示を行います。
   * 
   * 属性:
   *   onMenuToggle: メニュー開閉のコールバック関数
   *   isMenuOpen: メニューの開閉状態
   */
  const { user, logout } = useAuth();
  const pathname = usePathname();

  const handleLogout = async () => {
    /**
     * ログアウト処理
     * 
     * ユーザーのログアウト処理を実行します。
     * 認証状態をクリアし、ログインページにリダイレクトします。
     * 
     * 戻り値:
     *   Promise<void>: 非同期処理
     * 
     * 例外:
     *   Error: ログアウト失敗時のエラー
     */
    try {
      await logout();
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  const getRoleBadgeVariant = (role: string) => {
    /**
     * ロールに応じたバッジのバリアントを取得
     * 
     * 引数:
     *   role: ユーザーロール
     * 
     * 戻り値:
     *   string: バッジのバリアント名
     */
    switch (role) {
      case 'PLATFORM_ADMIN':
        return 'destructive';
      case 'TENANT_ADMIN':
        return 'default';
      case 'OPERATOR':
        return 'secondary';
      case 'AUDITOR':
        return 'outline';
      default:
        return 'outline';
    }
  };

  const getRoleLabel = (role: string) => {
    switch (role) {
      case 'PLATFORM_ADMIN':
        return 'プラットフォーム管理者';
      case 'TENANT_ADMIN':
        return 'テナント管理者';
      case 'OPERATOR':
        return '運用者';
      case 'AUDITOR':
        return '監査者';
      default:
        return role;
    }
  };

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-16 items-center justify-between">
        <div className="flex items-center space-x-4">
          <Button
            variant="ghost"
            size="icon"
            className="md:hidden"
            onClick={onMenuToggle}
          >
            {isMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </Button>
          
          <Link href="/" className="flex items-center space-x-2">
            <div className="h-8 w-8 rounded-lg bg-primary flex items-center justify-center">
              <span className="text-primary-foreground font-bold text-sm">RAG</span>
            </div>
            <span className="font-bold text-lg">AI Platform</span>
          </Link>
        </div>

        <nav className="hidden md:flex items-center space-x-6">
          <Link
            href="/users"
            className={cn(
              "text-sm font-medium transition-colors hover:text-primary",
              pathname.startsWith('/users') ? "text-primary" : "text-muted-foreground"
            )}
          >
            ユーザー管理
          </Link>
          <Link
            href="/tenants"
            className={cn(
              "text-sm font-medium transition-colors hover:text-primary",
              pathname.startsWith('/tenants') ? "text-primary" : "text-muted-foreground"
            )}
          >
            テナント管理
          </Link>
          <Link
            href="/contents"
            className={cn(
              "text-sm font-medium transition-colors hover:text-primary",
              pathname.startsWith('/contents') ? "text-primary" : "text-muted-foreground"
            )}
          >
            コンテンツ管理
          </Link>
          <Link
            href="/stats"
            className={cn(
              "text-sm font-medium transition-colors hover:text-primary",
              pathname.startsWith('/stats') ? "text-primary" : "text-muted-foreground"
            )}
          >
            統計・分析
          </Link>
        </nav>

        <div className="flex items-center space-x-4">
          {user && (
            <div className="flex items-center space-x-2">
              <Badge variant={getRoleBadgeVariant(user.role)}>
                {getRoleLabel(user.role)}
              </Badge>
              
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" className="relative h-8 w-8 rounded-full">
                    <Avatar className="h-8 w-8">
                      <AvatarImage src="" alt={user.username} />
                      <AvatarFallback>
                        {user.username.charAt(0).toUpperCase()}
                      </AvatarFallback>
                    </Avatar>
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent className="w-56" align="end" forceMount>
                  <DropdownMenuLabel className="font-normal">
                    <div className="flex flex-col space-y-1">
                      <p className="text-sm font-medium leading-none">
                        {user.username}
                      </p>
                      <p className="text-xs leading-none text-muted-foreground">
                        {user.email}
                      </p>
                    </div>
                  </DropdownMenuLabel>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem asChild>
                    <Link href="/settings" className="flex items-center">
                      <Settings className="mr-2 h-4 w-4" />
                      <span>設定</span>
                    </Link>
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={handleLogout} className="text-red-600">
                    <LogOut className="mr-2 h-4 w-4" />
                    <span>ログアウト</span>
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

export function Sidebar({ isOpen, onClose }: SidebarProps) {
  const pathname = usePathname();

  const navigation = [
    {
      name: 'ダッシュボード',
      href: '/',
      icon: BarChart3,
    },
    {
      name: 'ユーザー管理',
      href: '/users',
      icon: Users,
    },
    {
      name: 'テナント管理',
      href: '/tenants',
      icon: Building2,
    },
    {
      name: 'コンテンツ管理',
      href: '/contents',
      icon: FileText,
    },
    {
      name: '統計・分析',
      href: '/stats',
      icon: BarChart3,
    },
  ];

  return (
    <>
      {/* オーバーレイ */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 md:hidden"
          onClick={onClose}
        />
      )}
      
      {/* サイドバー */}
      <div
        className={cn(
          "fixed left-0 top-0 z-50 h-full w-64 bg-background border-r transform transition-transform duration-200 ease-in-out",
          isOpen ? "translate-x-0" : "-translate-x-full",
          "md:translate-x-0 md:static md:inset-0"
        )}
      >
        <div className="flex h-16 items-center justify-between px-6 border-b">
          <Link href="/" className="flex items-center space-x-2">
            <div className="h-8 w-8 rounded-lg bg-primary flex items-center justify-center">
              <span className="text-primary-foreground font-bold text-sm">RAG</span>
            </div>
            <span className="font-bold text-lg">AI Platform</span>
          </Link>
          <Button
            variant="ghost"
            size="icon"
            className="md:hidden"
            onClick={onClose}
          >
            <X className="h-5 w-5" />
          </Button>
        </div>
        
        <nav className="flex-1 px-4 py-6 space-y-2">
          {navigation.map((item) => {
            const Icon = item.icon;
            return (
              <Link
                key={item.name}
                href={item.href}
                className={cn(
                  "flex items-center space-x-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                  pathname === item.href
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:text-primary hover:bg-muted"
                )}
                onClick={onClose}
              >
                <Icon className="h-5 w-5" />
                <span>{item.name}</span>
              </Link>
            );
          })}
        </nav>
      </div>
    </>
  );
}

interface FooterProps {}

export function Footer({}: FooterProps) {
  return (
    <footer className="border-t bg-background">
      <div className="container py-6">
        <div className="flex flex-col items-center justify-between space-y-4 md:flex-row md:space-y-0">
          <div className="flex items-center space-x-2">
            <div className="h-6 w-6 rounded bg-primary flex items-center justify-center">
              <span className="text-primary-foreground font-bold text-xs">RAG</span>
            </div>
            <span className="text-sm font-medium">RAG AI Platform</span>
          </div>
          <div className="text-sm text-muted-foreground">
            © 2025 RAG AI Platform. All rights reserved.
          </div>
        </div>
      </div>
    </footer>
  );
}
