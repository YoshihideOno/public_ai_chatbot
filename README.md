# AIチャットボットプロジェクト

Next.js 15とPostgreSQLを使用したAIチャットボットアプリケーションです。

## 🚀 技術スタック

- **フロントエンド**: Next.js 15.5.4, React 19.1.0, TypeScript
- **スタイリング**: Tailwind CSS, Material-UI
- **バックエンド**: Node.js 20, PostgreSQL 13
- **コンテナ**: Docker, Docker Compose
- **開発環境**: Turbopack

## 📋 機能

- ✅ レスポンシブなWebインターフェース
- ✅ アプリケーション情報ページ
- ✅ お問い合わせフォーム
- 🔄 AIチャットボット機能（開発中）
- 🔄 データベース連携（開発中）

## 🛠️ セットアップ

### 前提条件

- Docker & Docker Compose
- Node.js 20+ (ローカル開発時)

### インストール

1. リポジトリをクローン
```bash
git clone https://github.com/YOUR_USERNAME/ai_chatbot_project.git
cd ai_chatbot_project
```

2. 環境変数を設定
```bash
# .env.local ファイルを作成
cp .env.example .env.local
# 必要に応じて値を編集
```

3. Docker Composeで起動
```bash
docker-compose up -d
```

4. アプリケーションにアクセス
```
http://localhost:3000
```

## 📁 プロジェクト構造

```
ai_chatbot_project/
├── ai_chatbot_app/          # Next.jsアプリケーション
│   ├── app/                # App Router
│   │   ├── about/          # アプリについてページ
│   │   ├── contact/        # お問い合わせページ
│   │   ├── layout.tsx      # ルートレイアウト
│   │   └── page.tsx        # ホームページ
│   ├── components/         # Reactコンポーネント
│   ├── public/            # 静的ファイル
│   └── package.json       # 依存関係
├── docker-compose.yml      # Docker設定
└── README.md              # このファイル
```

## 🔧 開発

### ローカル開発

```bash
cd ai_chatbot_app
npm install
npm run dev
```

### Docker開発

```bash
# 開発環境で起動
docker-compose up

# バックグラウンドで起動
docker-compose up -d

# ログを確認
docker-compose logs -f nextjs-app
```

## 🌐 環境変数

| 変数名 | 説明 | デフォルト |
|--------|------|------------|
| `DATABASE_URL` | PostgreSQL接続URL | `postgresql://user:password@db:5432/ai_chatbot_db` |
| `NODE_ENV` | 実行環境 | `development` |
| `NEXT_PUBLIC_APP_NAME` | アプリケーション名 | `AI Chatbot` |

## 📝 ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## 🤝 コントリビューション

1. このリポジトリをフォーク
2. フィーチャーブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add some amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを作成

## 📞 サポート

質問や問題がある場合は、[Issues](https://github.com/YOUR_USERNAME/ai_chatbot_project/issues)でお知らせください。
