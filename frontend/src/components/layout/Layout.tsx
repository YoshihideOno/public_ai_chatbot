'use client';

import React, { useState } from 'react';
import { Header, Sidebar, Footer } from './Header';

interface LayoutProps {
  children: React.ReactNode;
}

export function Layout({ children }: LayoutProps) {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  const toggleSidebar = () => {
    setIsSidebarOpen(!isSidebarOpen);
  };

  const closeSidebar = () => {
    setIsSidebarOpen(false);
  };

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
        
        <main className="flex-1 p-6 md:ml-64">
          <div className="max-w-7xl mx-auto">
            {children}
          </div>
        </main>
      </div>
      
      <Footer />
    </div>
  );
}
