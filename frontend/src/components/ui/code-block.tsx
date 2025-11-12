/**
 * コードブロック表示コンポーネント
 * 
 * シンタックスハイライト付きのコードブロックを表示し、
 * コピーボタン機能を提供します。
 * 
 * 主な機能:
 * - コードの表示（シンタックスハイライト対応）
 * - クリップボードへのコピー機能
 * - 複数言語のタブ切り替え対応
 */

'use client';

import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Copy, Check } from 'lucide-react';
import { cn } from '@/lib/utils';

interface CodeBlockProps {
  /**
   * 表示するコード文字列
   */
  code: string;
  
  /**
   * 言語（html, javascript, typescript等）
   */
  language?: string;
  
  /**
   * 追加のクラス名
   */
  className?: string;
  
  /**
   * ファイル名（オプション）
   */
  filename?: string;
}

interface CodeBlockWithTabsProps {
  /**
   * タブのデータ配列
   */
  tabs: Array<{
    label: string;
    code: string;
    language?: string;
  }>;
  
  /**
   * 追加のクラス名
   */
  className?: string;
}

/**
 * 単一のコードブロックコンポーネント
 * 
 * @param code - 表示するコード文字列
 * @param language - 言語（html, javascript等）
 * @param className - 追加のクラス名
 * @param filename - ファイル名（オプション）
 */
export function CodeBlock({ 
  code, 
  language = 'text', 
  className,
  filename 
}: CodeBlockProps) {
  const [copied, setCopied] = useState(false);

  /**
   * クリップボードにコピーする関数
   */
  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('コピーに失敗しました:', err);
    }
  };

  return (
    <div className={cn('relative rounded-lg border bg-gray-900', className)}>
      {filename && (
        <div className="px-4 py-2 border-b border-gray-800 text-sm text-gray-400">
          {filename}
        </div>
      )}
      <div className="relative">
        <pre className="overflow-x-auto p-4 text-sm">
          <code className={cn('text-gray-100', `language-${language}`)}>
            {code}
          </code>
        </pre>
        <Button
          variant="ghost"
          size="sm"
          className="absolute top-2 right-2 h-8 w-8 p-0 text-gray-400 hover:text-gray-100"
          onClick={handleCopy}
          aria-label="コードをコピー"
        >
          {copied ? (
            <Check className="h-4 w-4 text-green-400" />
          ) : (
            <Copy className="h-4 w-4" />
          )}
        </Button>
      </div>
    </div>
  );
}

/**
 * タブ切り替え可能なコードブロックコンポーネント
 * 
 * @param tabs - タブのデータ配列
 * @param className - 追加のクラス名
 */
export function CodeBlockWithTabs({ tabs, className }: CodeBlockWithTabsProps) {
  const [activeTab, setActiveTab] = useState(tabs[0]?.label || '');

  return (
    <div className={cn('w-full', className)}>
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-auto mb-4">
          {tabs.map((tab) => (
            <TabsTrigger key={tab.label} value={tab.label}>
              {tab.label}
            </TabsTrigger>
          ))}
        </TabsList>
        {tabs.map((tab) => (
          <TabsContent key={tab.label} value={tab.label} className="mt-0">
            <CodeBlock 
              code={tab.code} 
              language={tab.language || 'text'}
            />
          </TabsContent>
        ))}
      </Tabs>
    </div>
  );
}

