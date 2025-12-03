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

## ローカル開発

ローカルで静的サイトを表示するには、以下のいずれかの方法を使用してください。

### 方法1: PythonのHTTPサーバー（推奨）

Python 3がインストールされている場合：

```bash
cd static-site
python3 -m http.server 8080
```

または：

```bash
cd static-site
python -m http.server 8080
```

ブラウザで `http://localhost:8080` にアクセスします。

### 方法2: Node.jsのserve

Node.jsがインストールされている場合：

```bash
cd static-site
npx serve -p 8080
```

または、グローバルにインストールする場合：

```bash
npm install -g serve
cd static-site
serve -p 8080
```

ブラウザで `http://localhost:8080` にアクセスします。

### 方法3: PHPのビルトインサーバー

PHPがインストールされている場合：

```bash
cd static-site
php -S localhost:8080
```

ブラウザで `http://localhost:8080` にアクセスします。

### 方法4: 直接ファイルを開く（簡易）

HTTPサーバーを使わずに直接ファイルを開くこともできますが、一部の機能（CORS、相対パスなど）が正しく動作しない場合があります：

```bash
cd static-site
# macOSの場合
open index.html
# Linuxの場合
xdg-open index.html
# Windowsの場合
start index.html
```

## 使用方法

1. ローカル開発サーバーを起動します（上記の方法を参照）。

2. ブラウザで `http://localhost:8080` にアクセスします。

3. 右下に表示されるチャットボタンをクリックして、AIチャットボットを開きます。

4. ウィジェットはドラッグ&ドロップで移動できます。

5. ページを遷移しても、ウィジェットは表示され続けます。

## 注意事項

- ウィジェットのCDN URL（`NEXT_PUBLIC_WIDGET_CDN_URL` に設定したURL）を利用してください。デフォルトは `https://cdn.rag-chatbot.com/widget.js` です。
- 開発環境でローカルビルドを使用する場合は、スクリプトURLを `http://localhost:3001/widget.js` に差し替えてください。
- テナントIDとAPIキーは機密情報のため、適切に管理してください。

