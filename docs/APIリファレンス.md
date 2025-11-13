# APIリファレンス

本ドキュメントでは、RAG AIプラットフォームのRESTful APIエンドポイントについて説明します。

## 目次

- [ベースURL](#ベースurl)
- [認証](#認証)
- [エンドポイント一覧](#エンドポイント一覧)
- [エラーハンドリング](#エラーハンドリング)
- [レート制限](#レート制限)

---

## ベースURL

- **開発環境**: `http://localhost:8000`
- **本番環境**: `https://api.example.com`（環境に応じて変更）

すべてのAPIエンドポイントは `/api/v1` プレフィックスで始まります。

---

## 認証

### JWT認証

ほとんどのエンドポイントはJWT（JSON Web Token）認証が必要です。

#### 認証ヘッダー

```
Authorization: Bearer <access_token>
```

#### トークン取得

ログインエンドポイント（`POST /api/v1/auth/login`）からアクセストークンを取得します。

#### トークン有効期限

- **アクセストークン**: 30分（デフォルト）
- **リフレッシュトークン**: 7日（デフォルト）

### ウィジェット認証

ウィジェット用のエンドポイントは、テナントのAPIキーを使用します。

```
X-API-Key: <tenant_api_key>
```

---

## エンドポイント一覧

### 認証 (`/api/v1/auth`)

#### ユーザー登録

```http
POST /api/v1/auth/register
```

**リクエストボディ:**

```json
{
  "email": "user@example.com",
  "username": "username",
  "password": "password123",
  "tenant_name": "Company Name",
  "tenant_domain": "company.example.com"
}
```

**レスポンス:**

```json
{
  "id": "uuid",
  "email": "user@example.com",
  "username": "username",
  "tenant_id": "uuid",
  "role": "OPERATOR"
}
```

#### ログイン

```http
POST /api/v1/auth/login
```

**リクエストボディ:**

```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**レスポンス:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

#### 現在のユーザー情報取得

```http
GET /api/v1/auth/me
```

**認証**: 必須

**レスポンス:**

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

---

### チャット (`/api/v1/chats`)

#### RAGチャット

```http
POST /api/v1/chats/rag
```

**認証**: 必須

**リクエストボディ:**

```json
{
  "query": "質問内容",
  "model": "gpt-4",
  "top_k": 5,
  "session_id": "uuid（オプション）"
}
```

**レスポンス:**

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

#### ウィジェットチャット

```http
POST /api/v1/chats/widget/chat
```

**認証**: テナントAPIキー（`X-API-Key`ヘッダー）

**リクエストボディ:**

```json
{
  "query": "質問内容",
  "model": "gpt-4",
  "top_k": 5,
  "session_id": "uuid（オプション）"
}
```

**レスポンス:** RAGチャットと同じ形式

---

### コンテンツ管理 (`/api/v1/contents`)

#### ファイル一覧取得

```http
GET /api/v1/contents?skip=0&limit=100&file_type=pdf&status=completed
```

**認証**: 必須

**クエリパラメータ:**

- `skip`: スキップ数（デフォルト: 0）
- `limit`: 取得件数（デフォルト: 100、最大: 1000）
- `file_type`: ファイル形式（`pdf`, `txt`, `docx`等）
- `status`: ステータス（`pending`, `processing`, `completed`, `failed`）
- `search`: 検索キーワード

**レスポンス:**

```json
[
  {
    "id": "uuid",
    "file_name": "document.pdf",
    "file_type": "pdf",
    "title": "ドキュメントタイトル",
    "status": "completed",
    "file_size": 1024000,
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-01-01T00:00:00Z"
  }
]
```

#### ファイルアップロード

```http
POST /api/v1/contents/upload
```

**認証**: 必須（Admin権限）

**リクエスト形式:** `multipart/form-data`

**パラメータ:**

- `file`: ファイル（必須）
- `title`: タイトル（オプション）
- `description`: 説明（オプション）
- `tags`: タグ（カンマ区切り、オプション）

**レスポンス:**

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

#### ファイル削除

```http
DELETE /api/v1/contents/{file_id}
```

**認証**: 必須（Admin権限）

**レスポンス:**

```json
{
  "message": "ファイルが削除されました"
}
```

---

### テナント管理 (`/api/v1/tenants`)

#### テナント情報取得

```http
GET /api/v1/tenants/{tenant_id}
```

**認証**: 必須（テナントユーザー）

**レスポンス:**

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

#### 埋め込みコード取得

```http
GET /api/v1/tenants/{tenant_id}/embed-snippet
```

**認証**: 必須（テナントユーザー）

**レスポンス:**

```json
{
  "snippet": "<script src=\"https://cdn.example.com/widget.js\"></script>",
  "api_key": "tenant-api-key",
  "tenant_id": "uuid"
}
```

---

### APIキー管理 (`/api/v1/api-keys`)

#### APIキー一覧取得

```http
GET /api/v1/api-keys
```

**認証**: 必須（Admin権限）

**レスポンス:**

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

#### APIキー作成

```http
POST /api/v1/api-keys
```

**認証**: 必須（Admin権限）

**リクエストボディ:**

```json
{
  "provider": "openai",
  "model": "gpt-4",
  "api_key": "sk-..."
}
```

**レスポンス:**

```json
{
  "id": "uuid",
  "provider": "openai",
  "model": "gpt-4",
  "is_active": true,
  "created_at": "2025-01-01T00:00:00Z"
}
```

#### APIキー削除

```http
DELETE /api/v1/api-keys/{api_key_id}
```

**認証**: 必須（Admin権限）

**レスポンス:**

```json
{
  "message": "APIキーが削除されました"
}
```

---

### 統計 (`/api/v1/stats`)

#### 使用量統計取得

```http
GET /api/v1/stats/usage?start_date=2025-01-01&end_date=2025-01-31&granularity=day
```

**認証**: 必須

**クエリパラメータ:**

- `start_date`: 開始日（ISO 8601形式）
- `end_date`: 終了日（ISO 8601形式）
- `granularity`: 集計粒度（`day`, `week`, `month`）

**レスポンス:**

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

---

### 課金 (`/api/v1/billing`)

#### Checkout Session作成

```http
POST /api/v1/billing/checkout
```

**認証**: 必須

**リクエストボディ:**

```json
{
  "plan": "PRO",
  "billing_cycle": "MONTHLY"
}
```

**レスポンス:**

```json
{
  "url": "https://checkout.stripe.com/...",
  "session_id": "cs_..."
}
```

---

## エラーハンドリング

### エラーレスポンス形式

```json
{
  "detail": "エラーメッセージ",
  "error_code": "ERROR_CODE",
  "timestamp": "2025-01-01T00:00:00Z"
}
```

### HTTPステータスコード

- `200 OK`: リクエスト成功
- `201 Created`: リソース作成成功
- `400 Bad Request`: リクエストが不正
- `401 Unauthorized`: 認証が必要
- `403 Forbidden`: アクセス権限がない
- `404 Not Found`: リソースが見つからない
- `422 Unprocessable Entity`: バリデーションエラー
- `500 Internal Server Error`: サーバーエラー

### エラーコード一覧

| エラーコード | 説明 |
|---|---|
| `AUTHENTICATION_ERROR` | 認証エラー |
| `INVALID_CREDENTIALS` | 認証情報が無効 |
| `PERMISSION_DENIED` | 権限不足 |
| `VALIDATION_ERROR` | バリデーションエラー |
| `RESOURCE_NOT_FOUND` | リソースが見つからない |
| `RATE_LIMIT_EXCEEDED` | レート制限超過 |

---

## レート制限

現在、レート制限は実装されていませんが、将来実装予定です。

予定されている制限:

- **認証エンドポイント**: 10リクエスト/分
- **チャットエンドポイント**: 60リクエスト/分
- **ファイルアップロード**: 10リクエスト/分

レート制限超過時は、HTTPステータスコード `429 Too Many Requests` を返します。

---

## OpenAPIドキュメント

詳細なAPI仕様は、Swagger UIで確認できます。

- **開発環境**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

---

## サンプルコード

### cURL

```bash
# ログイン
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123"}'

# RAGチャット
curl -X POST http://localhost:8000/api/v1/chats/rag \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"query": "質問内容", "model": "gpt-4"}'
```

### Python

```python
import requests

# ログイン
response = requests.post(
    "http://localhost:8000/api/v1/auth/login",
    json={"email": "user@example.com", "password": "password123"}
)
token = response.json()["access_token"]

# RAGチャット
response = requests.post(
    "http://localhost:8000/api/v1/chats/rag",
    headers={"Authorization": f"Bearer {token}"},
    json={"query": "質問内容", "model": "gpt-4"}
)
print(response.json())
```

### JavaScript

```javascript
// ログイン
const loginResponse = await fetch('http://localhost:8000/api/v1/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'password123'
  })
});
const { access_token } = await loginResponse.json();

// RAGチャット
const chatResponse = await fetch('http://localhost:8000/api/v1/chats/rag', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${access_token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    query: '質問内容',
    model: 'gpt-4'
  })
});
const result = await chatResponse.json();
console.log(result);
```

---

**最終更新日**: 2025-01-XX

