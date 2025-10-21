/**
 * RAG AIチャットボットウィジェット
 * 
 * このファイルはRAG AIチャットボットのWebウィジェットを提供します。
 * Shadow DOMを使用してスタイルの分離を行い、他のサイトに埋め込んでも
 * スタイルの競合を防ぎます。アクセシビリティとエラーハンドリングを
 * 考慮した実装となっています。
 * 
 * 主な機能:
 * - チャットボタンの表示
 * - Shadow DOMによるスタイル分離
 * - アクセシビリティ対応
 * - エラーハンドリング
 */

(function (w, d, s, o) {
  'use strict';
  
  // グローバルオブジェクトの初期化
  w['RagChatWidget'] = o;
  w[o] = w[o] || function () { 
    (w[o].q = w[o].q || []).push(arguments); 
  };

  /**
   * コマンド処理関数
   * 
   * @param {string} cmd - 実行するコマンド
   * @param {Array} args - コマンドの引数
   */
  const process = (cmd, args) => {
    try {
      if (cmd === 'init') {
        const config = args[0] || {};
        
        // 既存のウィジェットが存在する場合は削除
        const existingWidget = d.getElementById('rag-chat-widget');
        if (existingWidget) {
          existingWidget.remove();
        }
        
        // Shadow DOMホストの作成
        const host = d.createElement('div');
        host.id = 'rag-chat-widget';
        host.setAttribute('role', 'complementary');
        host.setAttribute('aria-label', 'AIチャットボット');
        
        // DOMに追加
        d.body.appendChild(host);
        
        // Shadow DOMの作成
        const root = host.attachShadow({ mode: 'open' });
        
        // スタイルの定義
        const style = d.createElement('style');
        style.textContent = `
          :host {
            all: initial;
            position: fixed;
            right: 20px;
            bottom: 20px;
            z-index: 999999;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
          }
          
          .toggle {
            width: 48px;
            height: 48px;
            border-radius: 9999px;
            background: #1976d2;
            color: #fff;
            border: none;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            transition: all 0.2s ease;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
          }
          
          .toggle:hover {
            background: #1565c0;
            transform: scale(1.05);
          }
          
          .toggle:focus {
            outline: 2px solid #4fc3f7;
            outline-offset: 2px;
          }
          
          .toggle:active {
            transform: scale(0.95);
          }
        `;
        root.appendChild(style);
        
        // チャットボタンの作成
        const btn = d.createElement('button');
        btn.className = 'toggle';
        btn.setAttribute('aria-label', 'AIチャットボットを開く');
        btn.setAttribute('title', 'AIチャットボットを開く');
        btn.textContent = '💬';
        
        // クリックイベントの追加
        btn.addEventListener('click', () => {
          try {
            // チャットウィンドウの表示処理（今後実装予定）
            console.log('チャットボタンがクリックされました');
          } catch (error) {
            console.error('チャットボタンクリック時のエラー:', error);
          }
        });
        
        // キーボードアクセシビリティの追加
        btn.addEventListener('keydown', (e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            btn.click();
          }
        });
        
        root.appendChild(btn);
        
        console.log('RAGチャットウィジェットが初期化されました');
      }
    } catch (error) {
      console.error('RAGチャットウィジェット初期化エラー:', error);
    }
  };

  // 既存のキューを処理
  try {
    (w[o].q || []).forEach(args => {
      process(args[0], Array.prototype.slice.call(args, 1));
    });
    
    // 新しいコマンド処理関数を設定
    w[o] = function () { 
      process(arguments[0], Array.prototype.slice.call(arguments, 1)); 
    };
  } catch (error) {
    console.error('RAGチャットウィジェット設定エラー:', error);
  }

})(window, document, 'script', 'ragChat');


