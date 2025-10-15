## RAG AI プラットフォーム（マイクロサービス）

本リポジトリは、RAG（Retrieval-Augmented Generation）方式のAIチャットボットプラットフォームです。マイクロサービス指向、マルチテナント、セキュリティファーストを重視し、フロントエンド（Next.js）とバックエンド（FastAPI）で構成されています。

### 🚀 技術スタック

- **フロントエンド**: Next.js 15, React 18+, TypeScript, Tailwind CSS, shadcn/ui, React Hook Form + Zod
- **バックエンド**: Python 3.11+, FastAPI, PostgreSQL + pgvector, Redis
- **インフラ**: Docker, Docker Compose, Vercel, Neon
- **CI/CD**: GitHub Actions

### 📁 ディレクトリ構成（抜粋）

```
ai_chatbot_project/
├── api/                       # FastAPI バックエンド
│   └── app/
│       ├── api/               # APIエンドポイント
│       ├── core/              # 設定・セキュリティ
│       ├── services/          # ドメインサービス
│       └── utils/             # 共通ユーティリティ
├── frontend/                  # Next.js フロントエンド
│   ├── app/
│   ├── components/
│   └── tsconfig.json
├── docker-compose.yml         # ローカル開発用（あれば）
└── README.md
```

---

## 機能概要

- **AIチャット**: RAG による文書検索と生成
- **マルチテナント**: テナント毎にデータを分離
- **認証/認可**: JWT + OAuth2、RBAC（Role-Based Access Control）
- **観測性**: 構造化ログ、メトリクス、トレーシング

---

## 🛠 セットアップ

### 前提条件

- Docker & Docker Compose（推奨）
- Node.js 20+（フロントエンド開発時）
- Python 3.11+（バックエンドローカル実行時）

### リポジトリ取得

```bash
git clone https://github.com/YOUR_ORG/ai_chatbot_project.git
cd ai_chatbot_project
```

### 環境変数

- ルート、`api/`、`frontend/` それぞれにサンプルを用意してください（例: `.env.example` → `.env`/`.env.local`）。
- 代表例（値は環境に合わせて設定）

| 変数名 | 用途 |
|---|---|
| `DATABASE_URL` | PostgreSQL 接続（pgvector 拡張有）|
| `REDIS_URL` | セッション/キャッシュ用 Redis |
| `JWT_SECRET` | 認証用シークレット |
| `NEXT_PUBLIC_APP_NAME` | フロントのアプリ名 |

---

## ▶ ローカル実行

### 1) バックエンド（FastAPI）

```bash
cd api
pip install -r requirements.txt  # または Poetry 等
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- OpenAPI: `http://localhost:8000/docs`

### 2) フロントエンド（Next.js）

```bash
cd frontend
npm install
npm run dev
```

- Web: `http://localhost:3000`

### 3) Docker で一括起動（任意）

```bash
docker compose up -d
```

---

## セキュリティ/品質（抜粋）

- 入力バリデーション: Pydantic（API）/ Zod（UI）
- 認証/認可: JWT + OAuth2、RBAC
- CSRF/XSS/SQLインジェクション対策: フレームワーク/ミドルウェアで実装
- レート制限: 重要エンドポイントに適用（今後強化）
- ログ/監視: JSON 構造化ログ、Prometheus 形式メトリクス、OpenTelemetry トレース

---

## テスト

- 単体/統合/E2E を段階的に整備（目標カバレッジ 80%+）

---

## デプロイ（概要）

- CI/CD: GitHub Actions
- フロントエンド: Vercel
- データベース: Neon (PostgreSQL + pgvector)
- バックエンド: 別途ホスティング（要検討）

---

## コントリビューション

1. リポジトリをフォーク
2. ブランチ作成: `feat/...` `fix/...`
3. コミット規約に従う（例: `feat(auth): JWT認証を追加`）
4. PR 作成

---

## ライセンス

MIT
