/**
 * ウィジェット設定ファイル
 * 
 * このファイルでテナントIDとAPIキーを設定します。
 * 各HTMLページからこのファイルを読み込んで使用します。
 * 
 * 使用方法:
 * 1. YOUR_TENANT_ID と YOUR_API_KEY を実際の値に置き換えてください
 * 2. 各HTMLページの <head> に <script src="config.js"></script> を追加してください
 */

// テナントID（ダッシュボードから取得）
const WIDGET_TENANT_ID = 'YOUR_TENANT_ID';

// APIキー（ダッシュボードから取得）
const WIDGET_API_KEY = 'YOUR_API_KEY';

// ウィジェットの設定
const WIDGET_CONFIG = {
  tenantId: WIDGET_TENANT_ID,
  apiKey: WIDGET_API_KEY,
  theme: 'light',
  position: 'bottom-right'
};

