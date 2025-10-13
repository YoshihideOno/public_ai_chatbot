# AIチャットボットプロジェクト

Next.js 15とPostgreSQLを使用したAIチャットボットアプリケーションです。

## 🚀 技術スタック

- **フロントエンド**: Next.js 15.5.4, React 19.1.0, TypeScript
- **スタイリング**: Tailwind CSS, Material-UI
- **バックエンド**: Node.js 20, PostgreSQL 17
- **コンテナ**: Docker, Docker Compose
- **開発環境**: Turbopack
- **CI/CD**: GitHub Actions
- **デプロイ**: Vercel
- **データベース**: Neon (PostgreSQL)

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
├── .github/
│   └── workflows/
│       └── ci.yml              # GitHub Actions設定
├── ai_chatbot_app/             # Next.jsアプリケーション
│   ├── app/                    # App Router
│   ├── components/             # Reactコンポーネント
│   ├── public/                 # 静的ファイル
│   ├── .gitignore             # Next.js用gitignore
│   ├── Dockerfile              # Docker設定
│   ├── package.json            # 依存関係
│   └── tsconfig.json           # TypeScript設定
├── .gitignore                  # プロジェクト全体のgitignore
├── docker-compose.yml          # Docker Compose設定
├── env.example                 # 環境変数テンプレート
├── vercel.json                 # Vercel設定
└── README.md                   # プロジェクト説明
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

## ☁️ デプロイメント

### Vercel + Neon構成
- **フロントエンド**: Vercel
- **データベース**: Neon (PostgreSQL)
- **CI/CD**: GitHub Actions

### デプロイ手順
1. GitHubにコードをプッシュ
2. Vercelが自動的にビルド・デプロイ
3. Neonデータベースに接続

### 環境変数設定
- VercelプロジェクトのSettings → Environment Variables
- `DATABASE_URL` にNeonの接続文字列を設定

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
