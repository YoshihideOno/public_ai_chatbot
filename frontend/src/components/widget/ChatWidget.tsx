/**
 * チャットウィジェットコンポーネント
 * 
 * RAG AIチャットボットウィジェットをNext.jsアプリケーションに埋め込むためのコンポーネントです。
 * 環境変数からテナントIDとAPIキーを取得し、ウィジェットを初期化します。
 * 
 * 主な機能:
 * - ウィジェットスクリプトの読み込み
 * - 環境変数からの設定読み込み
 * - 開発環境と本番環境でのURL切り替え
 */

'use client';

import { useEffect } from 'react';
import Script from 'next/script';

interface ChatWidgetProps {
  tenantId?: string;
  apiKey?: string;
  theme?: 'light' | 'dark';
  position?: 'bottom-right' | 'bottom-left' | 'top-right' | 'top-left';
  initialMessage?: string;
}

type RagChatInitOptions = {
  tenantId: string;
  apiKey: string;
  apiBaseUrl: string;
  theme: ChatWidgetProps['theme'];
  position: ChatWidgetProps['position'];
  initialMessage?: string;
};

declare global {
  interface Window {
    ragChat?: (action: 'init', options: RagChatInitOptions) => void;
  }
}

/**
 * チャットウィジェットコンポーネント
 * 
 * @param tenantId - テナントID（環境変数から取得する場合は省略可能）
 * @param apiKey - APIキー（環境変数から取得する場合は省略可能）
 * @param theme - テーマ（light/dark）
 * @param position - 初期位置
 * @param initialMessage - 初期メッセージ（省略時はデフォルトメッセージを表示）
 */
export function ChatWidget({
  tenantId,
  apiKey,
  theme = 'light',
  position = 'bottom-right',
  initialMessage,
}: ChatWidgetProps) {
  // 環境変数からテナントIDとAPIキーを取得
  const widgetTenantId = tenantId || process.env.NEXT_PUBLIC_WIDGET_TENANT_ID;
  const widgetApiKey = apiKey || process.env.NEXT_PUBLIC_WIDGET_API_KEY;

  // APIベースURLを決定（開発環境と本番環境で切り替え）
  const getApiBaseUrl = () => {
    // 環境変数から取得
    if (process.env.NEXT_PUBLIC_API_URL) {
      return process.env.NEXT_PUBLIC_API_URL;
    }
    // 開発環境ではローカルのAPIサーバーを参照
    if (process.env.NODE_ENV === 'development') {
      return 'http://localhost:8000/api/v1';
    }
    // 本番環境では相対パス（同じドメイン）を使用
    return '/api/v1';
  };

  const apiBaseUrl = getApiBaseUrl();

  // ウィジェットのURLを決定（開発環境と本番環境で切り替え）
  const getWidgetUrl = () => {
    // 開発環境ではローカルのウィジェットを参照
    if (process.env.NODE_ENV === 'development') {
      // 開発サーバーが別ポートで動いている場合
      return process.env.NEXT_PUBLIC_WIDGET_URL || 'http://localhost:3001/widget.js';
    }
    // 本番環境ではCDNを参照
    return 'https://cdn.rag-chatbot.com/widget.js';
  };

  const widgetUrl = getWidgetUrl();

  useEffect(() => {
    if (typeof window === 'undefined' || !window.ragChat) {
      return;
    }
    if (widgetTenantId && widgetApiKey) {
      window.ragChat('init', {
        tenantId: widgetTenantId,
        apiKey: widgetApiKey,
        apiBaseUrl,
        theme,
        position,
        initialMessage,
      });
    } else {
      console.warn('チャットウィジェット: テナントIDまたはAPIキーが設定されていません');
    }
  }, [widgetTenantId, widgetApiKey, apiBaseUrl, theme, position, initialMessage]);

  // テナントIDとAPIキーが設定されていない場合は何も表示しない
  if (!widgetTenantId || !widgetApiKey) {
    if (process.env.NODE_ENV === 'development') {
      console.warn('チャットウィジェット: 環境変数 NEXT_PUBLIC_WIDGET_TENANT_ID または NEXT_PUBLIC_WIDGET_API_KEY が設定されていません');
    }
    return null;
  }

  return (
    <>
      <Script
        id="rag-chat-widget-script"
        strategy="afterInteractive"
        src={widgetUrl}
        onLoad={() => {
          if (typeof window !== 'undefined' && window.ragChat && widgetTenantId && widgetApiKey) {
            window.ragChat('init', {
              tenantId: widgetTenantId,
              apiKey: widgetApiKey,
              apiBaseUrl,
              theme,
              position,
              initialMessage,
            });
          }
        }}
        onError={(e) => {
          console.error('チャットウィジェットの読み込みに失敗しました:', e);
        }}
      />
    </>
  );
}

