/**
 * ウィジェット配信サーバー
 * 
 * ウィジェットファイル（widget.js）とマスコット画像を配信するための
 * シンプルなHTTPサーバーです。
 * CORSヘッダーを設定してクロスオリジンリクエストを許可します。
 */

import http from 'http';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const PORT = process.env.PORT || 3001;

/**
 * MIMEタイプを取得
 * @param {string} filePath - ファイルパス
 * @returns {string} MIMEタイプ
 */
function getMimeType(filePath) {
  const ext = path.extname(filePath).toLowerCase();
  const mimeTypes = {
    '.js': 'application/javascript',
    '.json': 'application/json',
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.gif': 'image/gif',
    '.svg': 'image/svg+xml',
    '.webp': 'image/webp',
    '.glb': 'model/gltf-binary',
    '.gltf': 'model/gltf+json',
    '.html': 'text/html',
    '.css': 'text/css',
  };
  return mimeTypes[ext] || 'application/octet-stream';
}

/**
 * HTTPサーバーを作成
 */
const server = http.createServer((req, res) => {
  // CORSヘッダーを設定
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  res.setHeader('Access-Control-Max-Age', '86400'); // 24時間

  // OPTIONSリクエストの処理
  if (req.method === 'OPTIONS') {
    res.writeHead(200);
    res.end();
    return;
  }

  // パスの正規化
  let filePath = req.url === '/' ? '/widget.js' : req.url;
  
  // クエリパラメータを除去
  filePath = filePath.split('?')[0];

  // セキュリティ: パストラバーサル攻撃を防ぐ
  if (filePath.includes('..')) {
    res.writeHead(400, { 'Content-Type': 'text/plain' });
    res.end('Bad Request');
    return;
  }

  // ファイルパスを解決
  let resolvedPath;
  
  // widget.jsの配信
  if (filePath === '/widget.js' || filePath === '/dist/widget.js') {
    resolvedPath = path.join(__dirname, 'dist', 'widget.js');
  }
  // マスコット画像の配信（assets/mascot/配下）
  else if (filePath.startsWith('/assets/mascot/')) {
    const fileName = path.basename(filePath);
    resolvedPath = path.join(__dirname, 'assets', 'mascot', fileName);
  }
  // その他の静的ファイル
  else {
    resolvedPath = path.join(__dirname, filePath);
  }

  // ファイルの存在確認
  fs.access(resolvedPath, fs.constants.F_OK, (err) => {
    if (err) {
      res.writeHead(404, { 'Content-Type': 'text/plain' });
      res.end('Not Found');
      return;
    }

    // ファイルを読み込んで配信
    fs.readFile(resolvedPath, (err, data) => {
      if (err) {
        res.writeHead(500, { 'Content-Type': 'text/plain' });
        res.end('Internal Server Error');
        return;
      }

      const mimeType = getMimeType(resolvedPath);
      
      // キャッシュヘッダーを設定（開発環境では無効化）
      if (process.env.NODE_ENV === 'production') {
        res.setHeader('Cache-Control', 'public, max-age=31536000'); // 1年
      } else {
        res.setHeader('Cache-Control', 'no-cache');
      }

      res.writeHead(200, { 'Content-Type': mimeType });
      res.end(data);
    });
  });
});

// サーバーを起動
server.listen(PORT, '0.0.0.0', () => {
  console.log(`ウィジェット配信サーバーが起動しました: http://localhost:${PORT}`);
  console.log(`配信ファイル:`);
  console.log(`  - widget.js: http://localhost:${PORT}/widget.js`);
  console.log(`  - マスコット画像: http://localhost:${PORT}/assets/mascot/[ファイル名]`);
});

// エラーハンドリング
server.on('error', (err) => {
  console.error('サーバーエラー:', err);
  process.exit(1);
});

