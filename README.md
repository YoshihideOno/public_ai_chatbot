## RAG AI プラットフォーム（マイクロサービス）

本リポジトリは、RAG（Retrieval-Augmented Generation）方式のAIチャットボットプラットフォームです。マイクロサービス指向、マルチテナント、セキュリティファーストを重視し、フロントエンド（Next.js）とバックエンド（FastAPI）で構成されています。

### 🚀 技術スタック

- **フロントエンド**: Next.js 15+, React 18+, TypeScript 5.2+, Tailwind CSS, shadcn/ui, React Hook Form + Zod
- **バックエンド**: Python 3.11+, FastAPI, PostgreSQL + pgvector, Redis
- **インフラ**: Docker, Docker Compose, Vercel, Neon
- **CI/CD**: GitHub Actions
- **AI/ML**: OpenAI, Anthropic, Google Gemini (LangChain統合)

### 📁 ディレクトリ構成

```
ai_chatbot_project/
├── api/                          # FastAPI バックエンド
│   ├── app/
│   │   ├── api/                  # APIエンドポイント
│   │   │   └── v1/
│   │   │       └── endpoints/    # 認証、チャット、テナント、コンテンツなど
│   │   ├── core/                 # 設定・セキュリティ・データベース
│   │   ├── models/               # SQLAlchemyモデル
│   │   ├── schemas/              # Pydanticスキーマ
│   │   ├── services/             # ドメインサービス（RAG、認証、テナントなど）
│   │   ├── repositories/         # データアクセス層
│   │   └── utils/                # 共通ユーティリティ
│   ├── alembic/                  # データベースマイグレーション
│   ├── tests/                    # テストコード
│   ├── requirements.txt          # Python依存関係
│   └── Dockerfile
├── frontend/                     # Next.js フロントエンド
│   ├── src/
│   │   ├── app/                  # Next.js App Router
│   │   │   ├── page.tsx          # ランディングページ
│   │   │   ├── dashboard/        # ダッシュボード
│   │   │   └── layout.tsx
│   │   ├── components/           # Reactコンポーネント
│   │   │   ├── auth/             # 認証関連
│   │   │   ├── contents/         # コンテンツ管理
│   │   │   └── widget/           # チャットウィジェット
│   │   └── lib/                  # ユーティリティ・設定
│   ├── package.json
│   └── Dockerfile
├── packages/
│   └── widget/                   # チャットボットウィジェット（CDN配信用）
│       ├── src/
│       │   └── index.js          # ウィジェット本体
│       └── Dockerfile
├── static-site/                  # 静的サイト（任意）
├── docs/                         # ドキュメント
│   └── background_tasks_implementation_plan.md
├── docker-compose.yml            # ローカル開発環境
├── env.example                   # 環境変数テンプレート
├── vercel.json                   # Vercel設定
└── README.md
```

---

## 機能概要

### コア機能

- **AIチャット**: RAG による文書検索と生成
  - 複数LLMプロバイダー対応（OpenAI, Anthropic, Google Gemini）
  - ベクトル検索による高精度な文書検索
  - 会話履歴の保持とコンテキスト管理
- **マルチテナント**: テナント毎にデータを完全分離
  - テナント単位での設定管理
  - テナント専用のAPIキー管理
  - 埋め込み用ウィジェットコード生成
- **認証/認可**: JWT + OAuth2、RBAC（Role-Based Access Control）
  - ユーザー登録・ログイン・パスワードリセット
  - ロールベースのアクセス制御（Platform Admin, Admin, Operator, User）
  - トークン管理（アクセス・リフレッシュ）
- **コンテンツ管理**: 文書のアップロード・管理
  - 複数ファイル形式対応（PDF, TXT, DOCX等）
  - 自動チャンキングとベクトル化
  - コンテンツのステータス管理
- **チャットウィジェット**: 外部サイトへの埋め込み対応
  - Shadow DOMによるスタイル分離
  - SPA/MPA自動検出
  - カスタマイズ可能なUI
- **統計・分析**: 使用状況の可視化
  - 使用量統計
  - クエリ分析
  - 監査ログ
- **課金管理**: Stripe統合
  - サブスクリプションプラン管理
  - 使用量ベースの課金
- **APIキー管理**: テナント単位でのAI APIキー管理
  - 複数プロバイダー対応
  - セキュアなキー保存

### 観測性

- 構造化ログ（JSON形式）
- メトリクス（Prometheus形式）
- トレーシング（OpenTelemetry）

---

## 🛠 セットアップ

### 前提条件

- Docker & Docker Compose（推奨）
- Node.js 20+（フロントエンド開発時）
- Python 3.11+（バックエンドローカル実行時）
- PostgreSQL 17+ with pgvector（Docker Composeで自動セットアップ）

### リポジトリ取得

```bash
git clone https://github.com/YOUR_ORG/ai_chatbot_project.git
cd ai_chatbot_project
```

### 環境変数設定

1. ルートディレクトリの `env.example` を `.env.local` にコピー

```bash
cp env.example .env.local
```

2. 必要な環境変数を設定（`.env.local` を編集）

主要な環境変数:

| 変数名 | 用途 | 例 |
|---|---|---|
| `DATABASE_URL` | PostgreSQL 接続（pgvector 拡張有）| `postgresql://user:password@db:5432/ai_chatbot_db` |
| `POSTGRES_USER` | PostgreSQL ユーザー名 | `user` |
| `POSTGRES_PASSWORD` | PostgreSQL パスワード | `password` |
| `POSTGRES_DB` | データベース名 | `ai_chatbot_db` |
| `SECRET_KEY` | JWT署名用シークレット | `your-secret-key-change-in-production` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | アクセストークン有効期限 | `30` |
| `OPENAI_API_KEY` | OpenAI APIキー（任意） | `sk-...` |
| `ANTHROPIC_API_KEY` | Anthropic APIキー（任意） | `...` |
| `NEXT_PUBLIC_APP_NAME` | フロントエンドのアプリ名 | `AI Chatbot` |
| `FASTAPI_BASE_URL` | FastAPIのベースURL | `http://localhost:8000` |
| `STORAGE_LOCAL_PATH` | ローカルストレージパス（未設定時は `/tmp/rag_storage`） | `/tmp/rag_storage` |

3. フロントエンド用の環境変数（`frontend/.env.local`）も必要に応じて設定

---

## ▶ ローカル実行

### 方法1: Docker Compose（推奨）

すべてのサービスを一括起動:

```bash
docker compose up -d
```

起動するサービス:
- **frontend-admin**: Next.js管理画面（`http://localhost:3000`）
- **widget-cdn**: チャットウィジェット配信サーバー（`http://localhost:3001`）
- **fastapi**: FastAPIバックエンド（`http://localhost:8000`）
- **db**: PostgreSQL + pgvector（`localhost:5432`）

ログ確認:

```bash
docker compose logs -f
```

停止:

```bash
docker compose down
```

### 方法2: 個別起動

#### 1) データベース（Docker Compose）

```bash
docker compose up -d db
```

#### 2) バックエンド（FastAPI）

```bash
cd api
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

- OpenAPI: `http://localhost:8000/docs`
- ヘルスチェック: `http://localhost:8000/health`

#### 3) フロントエンド（Next.js）

```bash
cd frontend
npm install
npm run dev
```

- Web: `http://localhost:3000`

#### 4) ウィジェットCDN（任意）

```bash
cd packages/widget
npm install
npm run build
npm run serve
```

- CDN: `http://localhost:3001`

### データベースマイグレーション

初回起動時またはスキーマ変更時:

```bash
cd api
alembic upgrade head
```

---

## セキュリティ/品質

### セキュリティ対策

- **入力バリデーション**: Pydantic（API）/ Zod（UI）
- **認証/認可**: JWT + OAuth2、RBAC（Role-Based Access Control）
- **CSRF対策**: フレームワーク標準機能
- **XSS対策**: 入力サニタイゼーション、CSP
- **SQLインジェクション対策**: ORM使用、パラメータ化クエリ
- **レート制限**: 重要エンドポイントに適用（今後強化）

### コード品質

- **型安全性**: Python型ヒント、TypeScript strict mode
- **エラーハンドリング**: 統一された例外処理
- **ログ**: 構造化ログ（JSON形式）
- **テスト**: 単体/統合/E2E（目標カバレッジ 80%+）

### 監視・観測性

- **ログ**: JSON構造化ログ、ログレベル（ERROR, WARN, INFO, DEBUG）
- **メトリクス**: Prometheus形式
- **トレーシング**: OpenTelemetry対応

---

## コーディング規約

本プロジェクトでは、`.cursorrules` に記載されたコーディング規約に従います。

### 主要な規約

- **Python (FastAPI)**: PEP 8準拠、型ヒント必須、関数50行以内、クラス300行以内
- **TypeScript (Next.js)**: strict mode、関数30行以内、コンポーネント200行以内
- **コメント**: 日本語で記述
- **エラーハンドリング**: 必ず実装
- **認証・認可**: 必ず実装
- **入力バリデーション**: 必ず実装

詳細は `.cursorrules` を参照してください。

---

## テスト

### バックエンド

```bash
cd api
pytest
```

### フロントエンド

```bash
cd frontend
npm test
```

### カバレッジ目標

- 単体テスト: 80%以上
- 統合テスト: 主要フロー
- E2Eテスト: ユーザーシナリオ

---

## デプロイ（概要）

### 環境

- **開発環境**: ローカル（Docker Compose）
- **ステージング環境**: Vercel（フロントエンド）、別途ホスティング（バックエンド）
- **本番環境**: Vercel（フロントエンド）、Neon（PostgreSQL + pgvector）

### CI/CD

- **GitHub Actions**: 自動テスト・デプロイ
- **フロントエンド**: Vercel自動デプロイ
- **バックエンド**: 別途ホスティング（要検討）

### デプロイ手順

1. コードをmainブランチにマージ
2. GitHub Actionsが自動でテスト実行
3. テスト通過後、自動デプロイ（Vercel）
4. データベースマイグレーションは手動実行（必要に応じて）

---

## APIエンドポイント

主要なAPIエンドポイント:

- **認証**: `/api/v1/auth/*` - 登録、ログイン、トークン管理
- **ユーザー**: `/api/v1/users/*` - ユーザー情報管理
- **チャット**: `/api/v1/chats/*` - RAGチャット、ウィジェットチャット
- **テナント**: `/api/v1/tenants/*` - テナント管理、埋め込みコード取得
- **コンテンツ**: `/api/v1/contents/*` - ファイルアップロード・管理
- **統計**: `/api/v1/stats/*` - 使用量統計
- **課金**: `/api/v1/billing/*` - Stripe統合
- **APIキー**: `/api/v1/api-keys/*` - AI APIキー管理
- **監査ログ**: `/api/v1/audit-logs/*` - 監査ログ取得

詳細は `http://localhost:8000/docs` のOpenAPIドキュメントを参照してください。

---

## 📚 ドキュメント

### 設計書

設計書は `docs/design/` ディレクトリにあります。

- [設計書一覧](./docs/design/README.md)
- [要件定義書](./docs/design/要件定義書.md)
- [システム設計書](./docs/design/システム設計書.md)
- [データベース設計書](./docs/design/データベース設計書.md)
- [API設計書](./docs/design/API設計書.md)
- [画面設計書](./docs/design/画面設計書.md)
- [セキュリティ設計書](./docs/design/セキュリティ設計書.md)

### 技術ドキュメント

詳細な技術ドキュメントは `docs/` ディレクトリにあります。

- [ドキュメント一覧](./docs/ドキュメント一覧.md)
- [開発環境セットアップ](./docs/開発環境セットアップ.md)
- [環境変数リファレンス](./docs/環境変数リファレンス.md)
- [システムアーキテクチャ](./docs/システムアーキテクチャ.md)
- [RAGパイプライン詳細](./docs/RAGパイプライン詳細.md)
- [開発ガイドライン](./docs/開発ガイドライン.md)
- [APIリファレンス](./docs/APIリファレンス.md)
- [デプロイガイド](./docs/デプロイガイド.md)
- [トラブルシューティング](./docs/トラブルシューティング.md)

---

## コントリビューション

1. リポジトリをフォーク
2. ブランチ作成: `feat/...` `fix/...` `docs/...` など
3. コミット規約に従う（例: `feat(auth): JWT認証を追加`）
4. テストを追加・更新
5. PR 作成

### コミット規約

- `feat`: 新機能
- `fix`: バグ修正
- `docs`: ドキュメント
- `style`: フォーマット
- `refactor`: リファクタリング
- `test`: テスト
- `chore`: その他

---

## ライセンス

MIT
