'use client';

import React, { useState } from 'react';
import { usePathname } from 'next/navigation';
import { Header, Sidebar, Footer } from './Header';

interface ConditionalLayoutProps {
  children: React.ReactNode;
}

/**
 * 条件付きレイアウトコンポーネント
 * 
 * パスに応じてレイアウトを切り替えます。
 * ランディングページ（/）では独自のレイアウトを使用し、
 * その他のページでは通常の管理画面レイアウトを使用します。
 * 
 * 属性:
 *   children: 子コンポーネント
 */
export function ConditionalLayout({ children }: ConditionalLayoutProps) {
  const pathname = usePathname();
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  const toggleSidebar = () => {
    setIsSidebarOpen(!isSidebarOpen);
  };

  const closeSidebar = () => {
    setIsSidebarOpen(false);
  };

  // ランディングページ、ログイン画面、パスワードリセット画面の場合は独自のレイアウトを使用
  if (pathname === '/' || pathname === '/login' || pathname === '/password-reset') {
    return <>{children}</>;
  }

  // その他のページでは管理画面レイアウトを使用
  return (
    <div className="min-h-screen flex flex-col">
      <Header 
        onMenuToggle={toggleSidebar} 
        isMenuOpen={isSidebarOpen} 
      />
      
      <div className="flex flex-1">
        <Sidebar 
          isOpen={isSidebarOpen} 
          onClose={closeSidebar} 
        />
        
        <main className="flex-1 p-6">
          <div className="max-w-7xl mx-auto">
            {children}
          </div>
        </main>
      </div>
      
      <Footer />
    </div>
  );
}
