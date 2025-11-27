# 静的サイトサンプル

このディレクトリには、RAG AIチャットボットウィジェットを埋め込んだ静的Webサイトのサンプルが含まれています。

## ファイル構成

- `index.html` - トップページ
- `about.html` - 概要ページ
- `contact.html` - お問い合わせページ
- `config.js` - ウィジェット設定ファイル（オプション）
- `README.md` - このファイル

## セットアップ

1. 各HTMLファイルの埋め込みコード内の `YOUR_TENANT_ID` と `YOUR_API_KEY` を実際の値に置き換えてください。

2. または、`config.js` を使用する場合:
   - `config.js` の `WIDGET_TENANT_ID` と `WIDGET_API_KEY` を設定
   - 各HTMLページの `<head>` に `<script src="config.js"></script>` を追加
   - 埋め込みコード内の `tenantId` と `apiKey` を `WIDGET_CONFIG.tenantId` と `WIDGET_CONFIG.apiKey` に変更

## 使用方法

1. このディレクトリをWebサーバーに配置します。

2. ブラウザで `index.html` を開きます。

3. 右下に表示されるチャットボタンをクリックして、AIチャットボットを開きます。

4. ウィジェットはドラッグ&ドロップで移動できます。

5. ページを遷移しても、ウィジェットは表示され続けます。

## 注意事項

- ウィジェットのCDN URL（`NEXT_PUBLIC_WIDGET_CDN_URL` に設定したURL）を利用してください。デフォルトは `https://cdn.rag-chatbot.com/widget.js` です。
- 開発環境でローカルビルドを使用する場合は、スクリプトURLを `http://localhost:3001/widget.js` に差し替えてください。
- テナントIDとAPIキーは機密情報のため、適切に管理してください。

