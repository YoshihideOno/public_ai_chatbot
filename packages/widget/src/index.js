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
 * - SPA/MPA自動検出
 * - ページ遷移をまたいだ永続化
 * - ドラッグ&ドロップによる位置移動
 * - チャットダイアログ
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

  // 状態管理用のキー
  const STATE_KEY = 'rag-chat-widget-state';
  const WEBSITE_TYPE_KEY = 'rag-chat-widget-website-type';

  /**
   * 状態管理ユーティリティ
   * sessionStorageを使用してウィジェットの状態を保存・復元
   */
  const StateManager = {
    /**
     * 状態を保存
     * @param {Object} state - 保存する状態オブジェクト
     */
    save: function(state) {
      try {
        if (w.sessionStorage) {
          w.sessionStorage.setItem(STATE_KEY, JSON.stringify(state));
        }
      } catch (error) {
        console.warn('状態の保存に失敗しました:', error);
      }
    },

    /**
     * 状態を読み込み
     * @returns {Object|null} 保存された状態、またはnull
     */
    load: function() {
      try {
        if (w.sessionStorage) {
          const saved = w.sessionStorage.getItem(STATE_KEY);
          return saved ? JSON.parse(saved) : null;
        }
      } catch (error) {
        console.warn('状態の読み込みに失敗しました:', error);
      }
      return null;
    },

    /**
     * 状態をクリア
     */
    clear: function() {
      try {
        if (w.sessionStorage) {
          w.sessionStorage.removeItem(STATE_KEY);
        }
      } catch (error) {
        console.warn('状態のクリアに失敗しました:', error);
      }
    }
  };

  /**
   * Webサイトタイプ検出ユーティリティ
   * SPAとMPAを自動検出
   */
  const WebsiteTypeDetector = {
    /**
     * Webサイトタイプを検出
     * @returns {string} 'spa' または 'mpa'
     */
    detect: function() {
      // 既に検出済みの場合は保存された値を返す
      try {
        if (w.sessionStorage) {
          const saved = w.sessionStorage.getItem(WEBSITE_TYPE_KEY);
          if (saved) {
            return saved;
          }
        }
      } catch (error) {
        // エラー時は続行
      }

      // SPA検出のヒント
      const spaHints = [
        // React
        w.__REACT_DEVTOOLS_GLOBAL_HOOK__,
        // Vue
        w.__VUE__,
        // Angular
        w.ng,
        // Next.js
        w.__NEXT_DATA__,
        // History APIの使用（pushState/replaceStateがオーバーライドされている可能性）
        w.history && w.history.pushState && w.history.pushState.toString().includes('[native code]') === false
      ];

      // SPAフレームワークの痕跡があるかチェック
      const hasSPAHint = spaHints.some(hint => hint !== undefined && hint !== null);

      // MutationObserverでDOM変更を監視（SPAの特徴）
      let isSPA = hasSPAHint;
      
      // History APIの監視
      if (w.history && w.history.pushState) {
        const originalPushState = w.history.pushState;
        const originalReplaceState = w.history.replaceState;
        
        w.history.pushState = function() {
          isSPA = true;
          WebsiteTypeDetector._saveType('spa');
          return originalPushState.apply(w.history, arguments);
        };
        
        w.history.replaceState = function() {
          isSPA = true;
          WebsiteTypeDetector._saveType('spa');
          return originalReplaceState.apply(w.history, arguments);
        };
      }

      // popstateイベントの監視
      w.addEventListener('popstate', function() {
        isSPA = true;
        WebsiteTypeDetector._saveType('spa');
      }, { once: true });

      // 初期判定
      const detectedType = isSPA ? 'spa' : 'mpa';
      WebsiteTypeDetector._saveType(detectedType);
      
      return detectedType;
    },

    /**
     * 検出結果を保存
     * @param {string} type - 'spa' または 'mpa'
     */
    _saveType: function(type) {
      try {
        if (w.sessionStorage) {
          w.sessionStorage.setItem(WEBSITE_TYPE_KEY, type);
        }
      } catch (error) {
        // エラー時は無視
      }
    },

    /**
     * 現在のWebサイトタイプを取得
     * @returns {string} 'spa' または 'mpa'
     */
    getType: function() {
      return WebsiteTypeDetector.detect();
    }
  };

  // グローバルなウィジェットインスタンス管理
  let widgetInstance = null;
  let isInitialized = false;

  /**
   * ウィジェットクラス
   * ウィジェットの状態と動作を管理
   */
  class Widget {
    constructor(config) {
      this.config = config || {};
      this.host = null;
      this.root = null;
      this.isOpen = false;
      this.isDragging = false;
      this.dragStartX = 0;
      this.dragStartY = 0;
      this.currentX = 0;
      this.currentY = 0;
      this.websiteType = WebsiteTypeDetector.getType();
      this.messages = []; // メッセージ履歴
      this.dragThreshold = 5; // ドラッグ判定の閾値（ピクセル）
      this.hasMoved = false; // ドラッグ中に移動したかどうか
      this.sessionId = null; // セッションID
      this.isLoading = false; // ローディング状態
      
      // 保存された状態を復元
      this.restoreState();
      
      // セッションIDの初期化
      this.initializeSessionId();
    }
    
    /**
     * セッションIDを初期化
     * sessionStorageから取得、なければ生成
     */
    initializeSessionId() {
      const SESSION_ID_KEY = 'rag-chat-widget-session-id';
      try {
        if (w.sessionStorage) {
          const saved = w.sessionStorage.getItem(SESSION_ID_KEY);
          if (saved) {
            this.sessionId = saved;
            return;
          }
        }
      } catch (error) {
        console.warn('セッションIDの読み込みに失敗しました:', error);
      }
      
      // セッションIDを生成（簡易UUID形式）
      this.sessionId = this.generateSessionId();
      
      try {
        if (w.sessionStorage) {
          w.sessionStorage.setItem(SESSION_ID_KEY, this.sessionId);
        }
      } catch (error) {
        console.warn('セッションIDの保存に失敗しました:', error);
      }
    }
    
    /**
     * セッションIDを生成（簡易UUID形式）
     * @returns {string} セッションID
     */
    generateSessionId() {
      return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        const r = Math.random() * 16 | 0;
        const v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
      });
    }
    
    /**
     * APIベースURLを取得
     * @returns {string} APIベースURL
     */
    getApiBaseUrl() {
      // 設定から取得、なければ相対パス
      if (this.config.apiBaseUrl) {
        return this.config.apiBaseUrl;
      }
      
      // 環境変数から取得（開発環境用）
      if (typeof process !== 'undefined' && process.env && process.env.NEXT_PUBLIC_API_URL) {
        return process.env.NEXT_PUBLIC_API_URL;
      }
      
      // デフォルト: 相対パス
      return '/api/v1';
    }

    /**
     * 保存された状態を復元
     */
    restoreState() {
      const saved = StateManager.load();
      if (saved) {
        this.isOpen = saved.isOpen || false;
        if (saved.position) {
          this.currentX = saved.position.x || 0;
          this.currentY = saved.position.y || 0;
        }
        // メッセージ履歴を復元
        if (saved.messages && Array.isArray(saved.messages)) {
          this.messages = saved.messages;
        }
      }
    }

    /**
     * 状態を保存
     */
    saveState() {
      StateManager.save({
        isOpen: this.isOpen,
        position: {
          x: this.currentX,
          y: this.currentY
        },
        messages: this.messages // メッセージ履歴も保存
      });
    }

    /**
     * ウィジェットを初期化
     */
    init() {
      // 既存のウィジェットが存在する場合は再利用
      const existingWidget = d.getElementById('rag-chat-widget');
      if (existingWidget && widgetInstance) {
        // 設定のみ更新
        widgetInstance.config = { ...widgetInstance.config, ...this.config };
        widgetInstance.saveState();
        return;
      }

      // Shadow DOMホストの作成
      this.host = d.createElement('div');
      this.host.id = 'rag-chat-widget';
      this.host.setAttribute('role', 'complementary');
      this.host.setAttribute('aria-label', 'AIチャットボット');

      // 位置の設定（保存された位置があれば使用、なければ右下）
      const saved = StateManager.load();
      if (saved && saved.position) {
        this.host.style.position = 'fixed';
        this.host.style.right = 'auto';
        this.host.style.bottom = 'auto';
        this.host.style.left = saved.position.x + 'px';
        this.host.style.top = saved.position.y + 'px';
        this.currentX = saved.position.x;
        this.currentY = saved.position.y;
      } else {
        this.host.style.position = 'fixed';
        this.host.style.right = '20px';
        this.host.style.bottom = '20px';
        // 初期位置を計算
        this.currentX = w.innerWidth - 68; // 48px + 20px margin
        this.currentY = w.innerHeight - 68;
      }

      // DOMに追加
      d.body.appendChild(this.host);

      // Shadow DOMの作成
      this.root = this.host.attachShadow({ mode: 'open' });

      // スタイルとUIの作成
      this.createStyles();
      this.createUI();

      // イベントリスナーの設定
      this.setupEventListeners();

      // SPA遷移監視の設定
      if (this.websiteType === 'spa') {
        this.setupSPAMonitoring();
      }

      // メッセージ履歴を復元
      this.restoreMessages();

      widgetInstance = this;
      this.saveState();
    }

    /**
     * スタイルを作成
     */
    createStyles() {
      const style = d.createElement('style');
      style.textContent = `
        :host {
          all: initial;
          position: fixed;
          z-index: 999999;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
        }
        
        .widget-container {
          position: relative;
          display: flex;
          flex-direction: column;
        }
        
        .toggle {
          width: 56px;
          height: 56px;
          border-radius: 50%;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: #fff;
          border: none;
          cursor: move;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 24px;
          transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
          box-shadow: 0 4px 16px rgba(102, 126, 234, 0.4), 0 2px 8px rgba(0, 0, 0, 0.1);
          user-select: none;
          -webkit-user-select: none;
          position: relative;
          overflow: hidden;
        }
        
        .toggle::before {
          content: '';
          position: absolute;
          top: 50%;
          left: 50%;
          width: 0;
          height: 0;
          border-radius: 50%;
          background: rgba(255, 255, 255, 0.3);
          transform: translate(-50%, -50%);
          transition: width 0.6s, height 0.6s;
        }
        
        .toggle:hover::before {
          width: 300px;
          height: 300px;
        }
        
        .toggle:hover {
          transform: scale(1.1) translateY(-2px);
          box-shadow: 0 8px 24px rgba(102, 126, 234, 0.5), 0 4px 12px rgba(0, 0, 0, 0.15);
        }
        
        .toggle:focus {
          outline: 3px solid rgba(102, 126, 234, 0.3);
          outline-offset: 3px;
        }
        
        .toggle:active {
          transform: scale(1.05) translateY(0);
        }
        
        .toggle.dragging {
          opacity: 0.9;
          cursor: grabbing;
          box-shadow: 0 8px 24px rgba(102, 126, 234, 0.6), 0 4px 12px rgba(0, 0, 0, 0.2);
        }
        
        .chat-dialog {
          position: absolute;
          bottom: 70px;
          right: 0;
          width: 400px;
          height: 600px;
          background: #ffffff;
          border-radius: 20px;
          box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3), 0 0 0 1px rgba(0, 0, 0, 0.05);
          display: none;
          flex-direction: column;
          overflow: hidden;
          animation: slideUpFade 0.4s cubic-bezier(0.4, 0, 0.2, 1);
          backdrop-filter: blur(10px);
        }
        
        .chat-dialog.open {
          display: flex;
        }
        
        @keyframes slideUpFade {
          from {
            opacity: 0;
            transform: translateY(30px) scale(0.95);
          }
          to {
            opacity: 1;
            transform: translateY(0) scale(1);
          }
        }
        
        .chat-header {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: #fff;
          padding: 20px 24px;
          display: flex;
          justify-content: space-between;
          align-items: center;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }
        
        .chat-header h3 {
          margin: 0;
          font-size: 18px;
          font-weight: 600;
          letter-spacing: -0.02em;
          display: flex;
          align-items: center;
          gap: 8px;
        }
        
        .chat-header h3::before {
          content: '🤖';
          font-size: 20px;
        }
        
        .chat-close {
          background: rgba(255, 255, 255, 0.15);
          border: none;
          color: #fff;
          font-size: 20px;
          cursor: pointer;
          padding: 0;
          width: 36px;
          height: 36px;
          display: flex;
          align-items: center;
          justify-content: center;
          border-radius: 10px;
          transition: all 0.2s ease;
          font-weight: 300;
        }
        
        .chat-close:hover {
          background: rgba(255, 255, 255, 0.25);
          transform: rotate(90deg);
        }
        
        .chat-close:active {
          transform: rotate(90deg) scale(0.95);
        }
        
        .chat-messages {
          flex: 1;
          overflow-y: auto;
          padding: 24px;
          background: linear-gradient(to bottom, #f8f9fa 0%, #ffffff 100%);
          scroll-behavior: smooth;
        }
        
        .chat-messages::-webkit-scrollbar {
          width: 6px;
        }
        
        .chat-messages::-webkit-scrollbar-track {
          background: transparent;
        }
        
        .chat-messages::-webkit-scrollbar-thumb {
          background: rgba(0, 0, 0, 0.2);
          border-radius: 3px;
          border-radius: 3px;
        }
        
        .chat-messages::-webkit-scrollbar-thumb:hover {
          background: rgba(0, 0, 0, 0.3);
        }
        
        .chat-input-area {
          padding: 20px;
          border-top: 1px solid rgba(0, 0, 0, 0.08);
          display: flex;
          gap: 12px;
          background: #ffffff;
          box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.05);
        }
        
        .chat-input {
          flex: 1;
          padding: 14px 18px;
          border: 2px solid #e8ecf0;
          border-radius: 12px;
          font-size: 14px;
          font-family: inherit;
          background: #f8f9fa;
          transition: all 0.2s ease;
          line-height: 1.5;
        }
        
        .chat-input:focus {
          outline: none;
          border-color: #667eea;
          background: #ffffff;
          box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        .chat-input::placeholder {
          color: #9ca3af;
        }
        
        .chat-send {
          padding: 14px 28px;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: #fff;
          border: none;
          border-radius: 12px;
          cursor: pointer;
          font-size: 14px;
          font-weight: 600;
          transition: all 0.2s ease;
          box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
          white-space: nowrap;
        }
        
        .chat-send:hover {
          transform: translateY(-1px);
          box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        }
        
        .chat-send:active {
          transform: translateY(0);
        }
        
        .chat-send:disabled {
          background: #d1d5db;
          cursor: not-allowed;
          transform: none;
          box-shadow: none;
        }
        
        .message {
          margin-bottom: 16px;
          padding: 14px 18px;
          border-radius: 18px;
          max-width: 85%;
          word-wrap: break-word;
          line-height: 1.5;
          font-size: 14px;
          animation: messageSlideIn 0.3s ease;
          position: relative;
        }
        
        @keyframes messageSlideIn {
          from {
            opacity: 0;
            transform: translateY(10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        
        .message.user {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: #fff;
          margin-left: auto;
          text-align: left;
          border-bottom-right-radius: 4px;
          box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
        }
        
        .message.bot {
          background: #ffffff;
          color: #1f2937;
          border: 1px solid #e5e7eb;
          border-bottom-left-radius: 4px;
          box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }
        
        .message a {
          color: #667eea;
          text-decoration: none;
          word-break: break-all;
          border-bottom: 1px solid rgba(102, 126, 234, 0.3);
          transition: all 0.2s ease;
          font-weight: 500;
        }
        
        .message a:hover {
          color: #764ba2;
          border-bottom-color: #764ba2;
        }
        
        .message.user a {
          color: #fff;
          border-bottom-color: rgba(255, 255, 255, 0.5);
        }
        
        .message.user a:hover {
          color: #f3f4f6;
          border-bottom-color: rgba(255, 255, 255, 0.8);
        }
        
        .message.loading {
          opacity: 0.7;
        }
        
        .loading-dots {
          display: inline-block;
          position: relative;
        }
        
        .loading-dots::after {
          content: '...';
          animation: loadingDots 1.5s steps(4, end) infinite;
        }
        
        @keyframes loadingDots {
          0%, 20% {
            content: '.';
          }
          40% {
            content: '..';
          }
          60%, 100% {
            content: '...';
          }
        }
        
        .message.error {
          background: #fee2e2;
          color: #991b1b;
          border: 1px solid #fca5a5;
        }
        
        .chat-send:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }
        
        .chat-input:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }
      `;
      this.root.appendChild(style);
    }

    /**
     * UIを作成
     */
    createUI() {
      const container = d.createElement('div');
      container.className = 'widget-container';

      // チャットボタン
      const btn = d.createElement('button');
      btn.className = 'toggle';
      btn.setAttribute('aria-label', 'AIチャットボットを開く');
      btn.setAttribute('title', 'AIチャットボットを開く');
      btn.textContent = '💬';
      btn.setAttribute('draggable', 'false');

      // チャットダイアログ
      const dialog = d.createElement('div');
      dialog.className = 'chat-dialog';
      if (this.isOpen) {
        dialog.classList.add('open');
      }

      // ヘッダー
      const header = d.createElement('div');
      header.className = 'chat-header';
      const title = d.createElement('h3');
      title.innerHTML = '<span>AIチャットボット</span>';
      const closeBtn = d.createElement('button');
      closeBtn.className = 'chat-close';
      closeBtn.setAttribute('aria-label', 'チャットを閉じる');
      closeBtn.innerHTML = '×';
      closeBtn.addEventListener('click', () => this.closeDialog());
      header.appendChild(title);
      header.appendChild(closeBtn);

      // メッセージエリア
      const messages = d.createElement('div');
      messages.className = 'chat-messages';
      messages.setAttribute('role', 'log');
      messages.setAttribute('aria-live', 'polite');

      // 入力エリア
      const inputArea = d.createElement('div');
      inputArea.className = 'chat-input-area';
      const input = d.createElement('input');
      input.type = 'text';
      input.className = 'chat-input';
      input.placeholder = 'メッセージを入力...';
      input.setAttribute('aria-label', 'メッセージ入力');
      const sendBtn = d.createElement('button');
      sendBtn.className = 'chat-send';
      sendBtn.textContent = '送信';
      sendBtn.addEventListener('click', () => {
        console.log('[Widget] 送信ボタンクリック');
        this.sendMessage(input);
      });
      input.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
          console.log('[Widget] Enterキー押下');
          this.sendMessage(input);
        }
      });
      inputArea.appendChild(input);
      inputArea.appendChild(sendBtn);

      dialog.appendChild(header);
      dialog.appendChild(messages);
      dialog.appendChild(inputArea);

      container.appendChild(btn);
      container.appendChild(dialog);

      this.root.appendChild(container);

      // 参照を保存
      this.toggleBtn = btn;
      this.dialog = dialog;
      this.messagesArea = messages;
      this.input = input;
      this.sendButton = sendBtn;
    }

    /**
     * イベントリスナーを設定
     */
    setupEventListeners() {
      // ドラッグ&ドロップ（先に設定して、クリックイベントを制御）
      this.setupDragAndDrop();

      // トグルボタンのクリック（ドラッグでない場合のみ）
      this.toggleBtn.addEventListener('click', (e) => {
        // ドラッグ中でない場合のみダイアログを開閉
        if (!this.isDragging && !this.hasMoved) {
          this.toggleDialog();
        }
      });
    }

    /**
     * ドラッグ&ドロップ機能を設定
     */
    setupDragAndDrop() {
      let startX, startY, initialX, initialY;

      const startDrag = (e) => {
        // クリックイベントを一時的に無効化
        this.hasMoved = false;
        this.isDragging = false;

        const clientX = e.touches ? e.touches[0].clientX : e.clientX;
        const clientY = e.touches ? e.touches[0].clientY : e.clientY;

        startX = clientX;
        startY = clientY;

        const rect = this.host.getBoundingClientRect();
        initialX = rect.left;
        initialY = rect.top;

        const onMove = (e) => {
          const currentX = e.touches ? e.touches[0].clientX : e.clientX;
          const currentY = e.touches ? e.touches[0].clientY : e.clientY;

          const deltaX = currentX - startX;
          const deltaY = currentY - startY;
          const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY);

          // 一定距離以上移動した場合のみドラッグと判定
          if (distance > this.dragThreshold) {
            if (!this.isDragging) {
              this.isDragging = true;
              this.toggleBtn.classList.add('dragging');
              e.preventDefault(); // ドラッグ開始時にクリックイベントを防止
            }

            this.hasMoved = true;

            let newX = initialX + deltaX;
            let newY = initialY + deltaY;

            // 境界チェック
            const widgetWidth = 48;
            const widgetHeight = 48;
            const maxX = w.innerWidth - widgetWidth;
            const maxY = w.innerHeight - widgetHeight;

            newX = Math.max(0, Math.min(newX, maxX));
            newY = Math.max(0, Math.min(newY, maxY));

            this.host.style.left = newX + 'px';
            this.host.style.top = newY + 'px';
            this.host.style.right = 'auto';
            this.host.style.bottom = 'auto';

            this.currentX = newX;
            this.currentY = newY;
          }
        };

        const onEnd = () => {
          if (this.isDragging) {
            // ドラッグが発生していた場合
            this.saveState();
          }
          
          this.isDragging = false;
          this.toggleBtn.classList.remove('dragging');
          
          // 少し遅延させてクリック判定をリセット（クリックイベントが発火する前に）
          setTimeout(() => {
            this.hasMoved = false;
          }, 100);

          d.removeEventListener('mousemove', onMove);
          d.removeEventListener('mouseup', onEnd);
          d.removeEventListener('touchmove', onMove);
          d.removeEventListener('touchend', onEnd);
        };

        d.addEventListener('mousemove', onMove);
        d.addEventListener('mouseup', onEnd);
        d.addEventListener('touchmove', onMove, { passive: false });
        d.addEventListener('touchend', onEnd);
      };

      this.toggleBtn.addEventListener('mousedown', startDrag);
      this.toggleBtn.addEventListener('touchstart', startDrag, { passive: false });
    }

    /**
     * SPA遷移監視を設定
     */
    setupSPAMonitoring() {
      // History APIの監視は既にWebsiteTypeDetectorで設定済み
      // ここでは追加の監視が必要な場合に実装
      
      // MutationObserverでDOM変更を監視（オプション）
      if (w.MutationObserver) {
        const observer = new MutationObserver((mutations) => {
          // ウィジェットがDOMから削除された場合の検知
          if (!d.body.contains(this.host) && this.host) {
            // ウィジェットが削除された場合は再追加
            d.body.appendChild(this.host);
          }
        });

        observer.observe(d.body, {
          childList: true,
          subtree: true
        });
      }
    }

    /**
     * ダイアログを開閉
     */
    toggleDialog() {
      this.isOpen = !this.isOpen;
      if (this.isOpen) {
        this.dialog.classList.add('open');
        this.input.focus();
      } else {
        this.dialog.classList.remove('open');
      }
      this.saveState();
    }

    /**
     * ダイアログを閉じる
     */
    closeDialog() {
      this.isOpen = false;
      this.dialog.classList.remove('open');
      this.saveState();
    }

    /**
     * メッセージを送信
     * APIを呼び出してRAG応答を取得
     */
    async sendMessage(input) {
      console.log('[Widget] sendMessage呼び出し:', {
        inputValue: input ? input.value : 'input is null',
        isLoading: this.isLoading,
        hasConfig: !!this.config,
        tenantId: this.config?.tenantId ? this.config.tenantId.substring(0, 8) + '...' : '未設定',
        apiKey: this.config?.apiKey ? this.config.apiKey.substring(0, 8) + '...' : '未設定'
      });
      
      const message = input.value.trim();
      if (!message) {
        console.log('[Widget] メッセージが空のため送信をスキップ');
        return;
      }
      
      // ローディング中は送信を無効化
      if (this.isLoading) {
        console.log('[Widget] ローディング中のため送信をスキップ');
        return;
      }

      console.log('[Widget] メッセージ送信開始:', message.substring(0, 50));

      // ユーザーメッセージを表示
      this.addMessage(message, 'user');
      input.value = '';

      // ローディング状態に設定
      this.setLoading(true);
      
      // ローディングメッセージを表示
      const loadingMessageId = 'loading-' + Date.now();
      this.addLoadingMessage(loadingMessageId);

      try {
        console.log('[Widget] callChatAPI呼び出し前');
        // API呼び出し
        const response = await this.callChatAPI(message);
        console.log('[Widget] callChatAPI完了');
        
        // ローディングメッセージを削除
        this.removeLoadingMessage(loadingMessageId);
        
        // ボットの応答を表示
        if (response && response.answer) {
          this.addMessage(response.answer, 'bot');
        } else {
          console.warn('[Widget] レスポンスにanswerが含まれていません:', response);
          this.addMessage('応答を取得できませんでした。', 'bot');
        }
      } catch (error) {
        // ローディングメッセージを削除
        this.removeLoadingMessage(loadingMessageId);
        
        // エラーメッセージを表示
        console.error('[Widget] チャットAPI呼び出しエラー:', error);
        let errorMessage = 'エラーが発生しました。しばらくしてから再度お試しください。';
        
        if (error.response) {
          // HTTPエラーレスポンス
          const status = error.response.status;
          if (status === 401) {
            errorMessage = '認証に失敗しました。APIキーを確認してください。';
          } else if (status === 403) {
            errorMessage = 'アクセスが拒否されました。';
          } else if (status === 429) {
            errorMessage = 'リクエストが多すぎます。しばらくしてから再度お試しください。';
          } else if (status >= 500) {
            errorMessage = 'サーバーエラーが発生しました。しばらくしてから再度お試しください。';
          }
        } else if (error.message) {
          // ネットワークエラーなど
          if (error.message.includes('fetch')) {
            errorMessage = 'ネットワークエラーが発生しました。接続を確認してください。';
          }
        }
        
        this.addMessage(errorMessage, 'bot');
      } finally {
        // ローディング状態を解除
        this.setLoading(false);
        console.log('[Widget] sendMessage完了');
      }
    }
    
    /**
     * チャットAPIを呼び出し
     * @param {string} message - ユーザーメッセージ
     * @returns {Promise<Object>} APIレスポンス
     */
    async callChatAPI(message) {
      const apiBaseUrl = this.getApiBaseUrl();
      const apiUrl = `${apiBaseUrl}/chats/widget/chat`;
      
      // デバッグログ
      console.log('[Widget] API呼び出し開始:', {
        apiUrl: apiUrl,
        tenantId: this.config.tenantId ? this.config.tenantId.substring(0, 8) + '...' : '未設定',
        apiKey: this.config.apiKey ? this.config.apiKey.substring(0, 8) + '...' : '未設定',
        sessionId: this.sessionId
      });
      
      // テナントIDとAPIキーの確認
      if (!this.config.tenantId || !this.config.apiKey) {
        console.error('[Widget] エラー: テナントIDまたはAPIキーが設定されていません', {
          tenantId: !!this.config.tenantId,
          apiKey: !!this.config.apiKey
        });
        throw new Error('テナントIDまたはAPIキーが設定されていません');
      }
      
      // リクエストボディ
      const requestBody = {
        query: message,
        session_id: this.sessionId,
        model: this.config.model || null,
        max_tokens: this.config.maxTokens || null,
        temperature: this.config.temperature || null
      };
      
      try {
        // fetchでAPI呼び出し
        const response = await fetch(apiUrl, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-Tenant-ID': this.config.tenantId,
            'X-API-Key': this.config.apiKey
          },
          body: JSON.stringify(requestBody)
        });
        
        console.log('[Widget] APIレスポンス受信:', {
          status: response.status,
          statusText: response.statusText,
          ok: response.ok
        });
        
        // レスポンスのチェック
        if (!response.ok) {
          const errorData = await response.json().catch(() => ({ detail: response.statusText }));
          console.error('[Widget] APIエラー:', {
            status: response.status,
            errorData: errorData
          });
          const error = new Error(errorData.detail || `HTTP error! status: ${response.status}`);
          error.response = { status: response.status, data: errorData };
          throw error;
        }
        
        // JSONレスポンスを取得
        const data = await response.json();
        console.log('[Widget] API成功:', {
          answer: data.answer ? data.answer.substring(0, 50) + '...' : 'なし',
          sources: data.sources ? data.sources.length : 0
        });
        return data;
      } catch (error) {
        console.error('[Widget] API呼び出し例外:', {
          message: error.message,
          stack: error.stack
        });
        throw error;
      }
    }
    
    /**
     * ローディング状態を設定
     * @param {boolean} loading - ローディング状態
     */
    setLoading(loading) {
      this.isLoading = loading;
      if (this.sendButton) {
        this.sendButton.disabled = loading;
        if (loading) {
          this.sendButton.textContent = '送信中...';
        } else {
          this.sendButton.textContent = '送信';
        }
      }
      if (this.input) {
        this.input.disabled = loading;
      }
    }
    
    /**
     * ローディングメッセージを追加
     * @param {string} messageId - メッセージID
     */
    addLoadingMessage(messageId) {
      const message = d.createElement('div');
      message.className = 'message bot loading';
      message.id = messageId;
      message.innerHTML = '<span class="loading-dots">考え中</span>';
      
      this.messagesArea.appendChild(message);
      this.messagesArea.scrollTop = this.messagesArea.scrollHeight;
    }
    
    /**
     * ローディングメッセージを削除
     * @param {string} messageId - メッセージID
     */
    removeLoadingMessage(messageId) {
      const loadingMessage = this.messagesArea.querySelector('#' + messageId);
      if (loadingMessage) {
        loadingMessage.remove();
      }
    }

    /**
     * URLを検出してリンクに変換
     * セキュリティ対策（XSS防止）を実装
     * 
     * @param {string} text - 変換するテキスト
     * @returns {DocumentFragment} リンク化されたDOMフラグメント
     */
    convertUrlsToLinks(text) {
      const fragment = d.createDocumentFragment();
      
      // URL検出の正規表現（http://またはhttps://で始まるもののみ）
      const urlRegex = /(https?:\/\/[^\s<>"']+)/gi;
      let lastIndex = 0;
      let match;
      
      while ((match = urlRegex.exec(text)) !== null) {
        // URLの前のテキストを追加
        if (match.index > lastIndex) {
          const textNode = d.createTextNode(text.substring(lastIndex, match.index));
          fragment.appendChild(textNode);
        }
        
        // URLを検証
        const url = match[0];
        // セキュリティ: 危険なプロトコルを除外
        if (url.startsWith('http://') || url.startsWith('https://')) {
          // リンク要素を作成
          const link = d.createElement('a');
          link.href = url;
          link.textContent = url;
          link.target = '_blank';
          link.rel = 'noopener noreferrer';
          link.setAttribute('aria-label', `外部リンク: ${url}`);
          fragment.appendChild(link);
        } else {
          // 安全でないURLはテキストとして表示
          const textNode = d.createTextNode(url);
          fragment.appendChild(textNode);
        }
        
        lastIndex = match.index + match[0].length;
      }
      
      // 残りのテキストを追加
      if (lastIndex < text.length) {
        const textNode = d.createTextNode(text.substring(lastIndex));
        fragment.appendChild(textNode);
      }
      
      // URLが見つからない場合はテキストノードのみを返す
      if (fragment.childNodes.length === 0) {
        const textNode = d.createTextNode(text);
        fragment.appendChild(textNode);
      }
      
      return fragment;
    }

    /**
     * メッセージ履歴を復元
     */
    restoreMessages() {
      if (this.messages && this.messages.length > 0) {
        this.messages.forEach(msg => {
          const message = d.createElement('div');
          message.className = `message ${msg.type}`;
          
          // URLをリンクに変換して追加
          const content = this.convertUrlsToLinks(msg.text);
          message.appendChild(content);
          
          this.messagesArea.appendChild(message);
        });
        this.messagesArea.scrollTop = this.messagesArea.scrollHeight;
      }
    }

    /**
     * メッセージを追加
     */
    addMessage(text, type) {
      // メッセージ履歴に追加
      this.messages.push({ text, type, timestamp: Date.now() });
      
      // DOMに追加
      const message = d.createElement('div');
      message.className = `message ${type}`;
      
      // URLをリンクに変換して追加
      const content = this.convertUrlsToLinks(text);
      message.appendChild(content);
      
      this.messagesArea.appendChild(message);
      this.messagesArea.scrollTop = this.messagesArea.scrollHeight;
      
      // 状態を保存
      this.saveState();
    }
  }

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
        
        console.log('[Widget] 初期化コマンド受信:', {
          tenantId: config.tenantId ? config.tenantId.substring(0, 8) + '...' : '未設定',
          apiKey: config.apiKey ? config.apiKey.substring(0, 8) + '...' : '未設定',
          apiBaseUrl: config.apiBaseUrl || '未設定（デフォルト使用）',
          theme: config.theme,
          position: config.position
        });
        
        // 重複初期化の防止
        if (isInitialized && widgetInstance) {
          // 既存のウィジェットがある場合は設定のみ更新
          console.log('[Widget] 既存のウィジェットを更新');
          widgetInstance.config = { ...widgetInstance.config, ...config };
          return;
        }

        // ウィジェットの作成と初期化
        const widget = new Widget(config);
        widget.init();
        isInitialized = true;
        
        console.log('[Widget] RAGチャットウィジェットが初期化されました（' + widget.websiteType.toUpperCase() + 'モード）');
      }
    } catch (error) {
      console.error('[Widget] RAGチャットウィジェット初期化エラー:', error);
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
