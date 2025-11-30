/**
 * ウィジェット設定ファイル
 * 
 * このファイルでテナントID、APIキー、API URL、ウィジェットCDN URLを設定します。
 * 各HTMLページからこのファイルを読み込んで使用します。
 * 
 * 使用方法:
 * 1. YOUR_TENANT_ID と YOUR_API_KEY を実際の値に置き換えてください
 * 2. API_BASE_URL と WIDGET_CDN_URL を本番環境のURLに置き換えてください
 * 3. 各HTMLページの <head> に <script src="config.js"></script> を追加してください
 */

// テナントID（ダッシュボードから取得）
const WIDGET_TENANT_ID = 'YOUR_TENANT_ID';

// APIキー（ダッシュボードから取得）
const WIDGET_API_KEY = 'YOUR_API_KEY';

// APIベースURL（本番環境のAPI URLに置き換えてください）
// 例: 'https://api.example.com/api/v1' または '/api/v1'（同一オリジンの場合）
const API_BASE_URL = 'http://localhost:8000/api/v1';

// ウィジェットCDN URL（本番環境のウィジェットCDN URLに置き換えてください）
// 例: 'https://cdn.example.com/widget.js'
const WIDGET_CDN_URL = 'https://cdn.rag-chatbot.com/widget.js';

// ウィジェットの設定
const WIDGET_CONFIG = {
  tenantId: WIDGET_TENANT_ID,
  apiKey: WIDGET_API_KEY,
  apiBaseUrl: API_BASE_URL,
  theme: 'light',
  position: 'bottom-right'
};

