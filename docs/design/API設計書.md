# API設計書

## 1. 概要

### 1.1 API仕様
- **形式**: RESTful API
- **バージョン**: v1
- **ベースURL**: `/api/v1`
- **データ形式**: JSON
- **認証**: JWT Bearer Token

### 1.2 OpenAPI仕様
- **形式**: OpenAPI 3.0
- **ドキュメント**: `/docs` (Swagger UI), `/redoc` (ReDoc)

---

## 2. 認証・認可

### 2.1 認証方式

#### 2.1.1 JWT認証
```
Authorization: Bearer <access_token>
```

#### 2.1.2 ウィジェット認証
```
X-API-Key: <tenant_api_key>
```

### 2.2 トークン管理

- **アクセストークン**: 30分有効
- **リフレッシュトークン**: 7日有効
- **トークン形式**: JWT (HS256)

---

## 3. エンドポイント設計

### 3.1 認証エンドポイント

#### POST /api/v1/auth/register
**説明**: ユーザー登録

**リクエスト**:
```json
{
  "email": "user@example.com",
  "username": "username",
  "password": "Password123",
  "tenant_name": "Company Name",
  "tenant_domain": "company.example.com"
}
```

**レスポンス**: `201 Created`
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "username": "username",
  "tenant_id": "uuid",
  "role": "OPERATOR"
}
```

#### POST /api/v1/auth/login
**説明**: ログイン

**リクエスト**:
```json
{
  "email": "user@example.com",
  "password": "Password123"
}
```

**レスポンス**: `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

#### GET /api/v1/auth/me
**説明**: 現在のユーザー情報取得

**認証**: 必須

**レスポンス**: `200 OK`
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "username": "username",
  "role": "OPERATOR",
  "tenant_id": "uuid",
  "is_active": true,
  "is_verified": true
}
```

### 3.2 チャットエンドポイント

#### POST /api/v1/chats/rag
**説明**: RAGチャット

**認証**: 必須

**リクエスト**:
```json
{
  "query": "質問内容",
  "model": "gpt-4",
  "top_k": 5,
  "session_id": "uuid",
  "temperature": 0.7,
  "max_tokens": 500
}
```

**レスポンス**: `200 OK`
```json
{
  "answer": "AI応答テキスト",
  "sources": [
    {
      "file_id": "uuid",
      "file_name": "document.pdf",
      "chunk_index": 0,
      "chunk_text": "関連チャンクテキスト..."
    }
  ],
  "conversation_id": "uuid",
  "metadata": {
    "model": "gpt-4",
    "tokens_in": 100,
    "tokens_out": 200,
    "latency_ms": 1500
  }
}
```

#### POST /api/v1/chats/widget/chat
**説明**: ウィジェット用RAGチャット

**認証**: テナントAPIキー（`X-API-Key`ヘッダー）

**リクエスト**: `/api/v1/chats/rag` と同じ

**レスポンス**: `/api/v1/chats/rag` と同じ

### 3.3 コンテンツ管理エンドポイント

#### GET /api/v1/contents
**説明**: ファイル一覧取得

**認証**: 必須

**クエリパラメータ**:
- `skip`: スキップ数（デフォルト: 0）
- `limit`: 取得件数（デフォルト: 100、最大: 1000）
- `file_type`: ファイル形式（`pdf`, `txt`, `docx`）
- `status`: ステータス（`pending`, `processing`, `completed`, `failed`）
- `search`: 検索キーワード

**レスポンス**: `200 OK`
```json
[
  {
    "id": "uuid",
    "file_name": "document.pdf",
    "file_type": "pdf",
    "title": "ドキュメントタイトル",
    "status": "completed",
    "file_size": 1024000,
    "created_at": "2025-01-01T00:00:00Z"
  }
]
```

#### POST /api/v1/contents/upload
**説明**: ファイルアップロード

**認証**: 必須（Admin権限）

**リクエスト形式**: `multipart/form-data`

**パラメータ**:
- `file`: ファイル（必須）
- `title`: タイトル（オプション）
- `description`: 説明（オプション）
- `tags`: タグ（カンマ区切り、オプション）

**レスポンス**: `201 Created`
```json
{
  "id": "uuid",
  "file_name": "document.pdf",
  "file_type": "pdf",
  "title": "ドキュメントタイトル",
  "status": "pending",
  "file_size": 1024000,
  "created_at": "2025-01-01T00:00:00Z"
}
```

#### DELETE /api/v1/contents/{file_id}
**説明**: ファイル削除

**認証**: 必須（Admin権限）

**レスポンス**: `200 OK`
```json
{
  "message": "ファイルが削除されました"
}
```

### 3.4 テナント管理エンドポイント

#### GET /api/v1/tenants/{tenant_id}
**説明**: テナント情報取得

**認証**: 必須（テナントユーザー）

**レスポンス**: `200 OK`
```json
{
  "id": "uuid",
  "name": "Company Name",
  "domain": "company.example.com",
  "plan": "PRO",
  "status": "ACTIVE",
  "settings": {
    "embedding_model": "text-embedding-3-small",
    "llm_model": "gpt-4"
  },
  "created_at": "2025-01-01T00:00:00Z"
}
```

#### GET /api/v1/tenants/{tenant_id}/embed-snippet
**説明**: 埋め込みコード取得

**認証**: 必須（テナントユーザー）

**レスポンス**: `200 OK`
```json
{
  "snippet": "<script src=\"https://cdn.example.com/widget.js\"></script>",
  "api_key": "tenant-api-key",
  "tenant_id": "uuid"
}
```

### 3.5 APIキー管理エンドポイント

#### GET /api/v1/api-keys
**説明**: APIキー一覧取得

**認証**: 必須（Admin権限）

**レスポンス**: `200 OK`
```json
[
  {
    "id": "uuid",
    "provider": "openai",
    "model": "gpt-4",
    "is_active": true,
    "created_at": "2025-01-01T00:00:00Z"
  }
]
```

#### POST /api/v1/api-keys
**説明**: APIキー作成

**認証**: 必須（Admin権限）

**リクエスト**:
```json
{
  "provider": "openai",
  "model": "gpt-4",
  "api_key": "sk-..."
}
```

**レスポンス**: `201 Created`
```json
{
  "id": "uuid",
  "provider": "openai",
  "model": "gpt-4",
  "is_active": true,
  "created_at": "2025-01-01T00:00:00Z"
}
```

#### DELETE /api/v1/api-keys/{api_key_id}
**説明**: APIキー削除

**認証**: 必須（Admin権限）

**レスポンス**: `200 OK`
```json
{
  "message": "APIキーが削除されました"
}
```

### 3.6 統計エンドポイント

#### GET /api/v1/stats/usage
**説明**: 使用量統計取得

**認証**: 必須

**クエリパラメータ**:
- `start_date`: 開始日（ISO 8601形式）
- `end_date`: 終了日（ISO 8601形式）
- `granularity`: 集計粒度（`day`, `week`, `month`）

**レスポンス**: `200 OK`
```json
{
  "total_tokens": 100000,
  "total_cost": 10.50,
  "by_date": [
    {
      "date": "2025-01-01",
      "tokens": 5000,
      "cost": 0.50
    }
  ]
}
```

### 3.7 課金エンドポイント

#### POST /api/v1/billing/checkout
**説明**: Checkout Session作成

**認証**: 必須

**リクエスト**:
```json
{
  "plan": "PRO",
  "billing_cycle": "MONTHLY"
}
```

**レスポンス**: `200 OK`
```json
{
  "url": "https://checkout.stripe.com/...",
  "session_id": "cs_..."
}
```

---

## 4. エラーハンドリング

### 4.1 エラーレスポンス形式

```json
{
  "detail": "エラーメッセージ",
  "error_code": "ERROR_CODE",
  "timestamp": "2025-01-01T00:00:00Z"
}
```

### 4.2 HTTPステータスコード

| コード | 説明 |
|---|---|
| 200 | OK |
| 201 | Created |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 422 | Unprocessable Entity |
| 500 | Internal Server Error |

### 4.3 エラーコード一覧

| エラーコード | 説明 |
|---|---|
| `AUTHENTICATION_ERROR` | 認証エラー |
| `INVALID_CREDENTIALS` | 認証情報が無効 |
| `PERMISSION_DENIED` | 権限不足 |
| `VALIDATION_ERROR` | バリデーションエラー |
| `RESOURCE_NOT_FOUND` | リソースが見つからない |
| `RATE_LIMIT_EXCEEDED` | レート制限超過 |

---

## 5. バリデーション

### 5.1 リクエストバリデーション

- **Pydantic**: バックエンドでスキーマ定義
- **Zod**: フロントエンドでスキーマ定義

### 5.2 バリデーションルール

#### ユーザー登録
- `email`: メールアドレス形式
- `username`: 3-100文字、英数字とアンダースコア
- `password`: 8文字以上、大文字・小文字・数字を含む

#### ファイルアップロード
- `file`: 必須、最大100MB
- `file_type`: PDF, TXT, DOCXのみ

#### チャットリクエスト
- `query`: 必須、1-1000文字
- `model`: オプション、サポートされているモデル名
- `top_k`: オプション、1-20の整数
- `temperature`: オプション、0.0-2.0の数値

---

## 6. レート制限

### 6.1 制限（将来実装予定）

- **認証エンドポイント**: 10リクエスト/分
- **チャットエンドポイント**: 60リクエスト/分
- **ファイルアップロード**: 10リクエスト/分

### 6.2 レート制限超過時

- HTTPステータスコード: `429 Too Many Requests`
- レスポンスヘッダー: `Retry-After: <秒数>`

---

## 7. バージョニング

### 7.1 バージョン管理

- URLパスにバージョンを含める: `/api/v1/...`
- 将来のバージョン: `/api/v2/...`

### 7.2 後方互換性

- 既存エンドポイントは維持
- 新しい機能は新しいエンドポイントで提供

---

**作成日**: 2025-01-XX  
**最終更新日**: 2025-01-XX

