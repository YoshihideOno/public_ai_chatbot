# API認証機能テスト設計書

## 1. 概要
本ドキュメントは、AI Chatbot APIの認証関連エンドポイントに対する包括的なテストケースを定義する。
pytestを用いた単体テストおよび統合テストを想定している。

## 2. テスト対象エンドポイント
- `POST /api/v1/auth/register` (ユーザー登録 - 単体ユーザー登録)
- `POST /api/v1/auth/register-tenant` (テナント登録 - テナントと管理者ユーザーを同時に登録)
- `POST /api/v1/auth/login` (ユーザーログイン)
- `POST /api/v1/auth/logout` (ユーザーログアウト)
- `POST /api/v1/auth/password-reset` (パスワードリセット要求)
- `POST /api/v1/auth/password-reset/confirm` (パスワードリセット確認)
- `POST /api/v1/auth/verify-email` (メールアドレス検証)
- `GET /api/v1/auth/me` (現在のユーザー情報取得)
- `POST /api/v1/auth/refresh` (トークンリフレッシュ)
- `POST /api/v1/auth/login/oauth` (OAuth2ログイン - 実装済みだがフロントエンド未使用のためテストスキップ)

## 3. バリデーションルール

### 3.1. メールアドレス
- 形式: RFC 5322準拠
- 最小長: 5文字（例: a@b.c）
- 最大長: 255文字
- 境界値: 4文字（無効）、5文字（有効）、255文字（有効）、256文字（無効）

### 3.2. パスワード
- 最小長: 8文字
- 最大長: 128文字（想定）
- 必須要件: 大文字、小文字、数字を含む
- 推奨: 特殊文字を含む
- 境界値: 7文字（無効）、8文字（有効）、128文字（有効）、129文字（無効）

### 3.3. ユーザー名
- 最小長: 3文字
- 最大長: 100文字
- 許可文字: 英数字、アンダースコア
- 境界値: 2文字（無効）、3文字（有効）、100文字（有効）、101文字（無効）

### 3.4. テナント名
- 最小長: 2文字
- 最大長: 255文字
- 境界値: 1文字（無効）、2文字（有効）、255文字（有効）、256文字（無効）

### 3.5. テナント識別子
- 最小長: 3文字
- 最大長: 255文字
- 許可文字: 英数字、ハイフン、アンダースコア
- 境界値: 2文字（無効）、3文字（有効）、255文字（有効）、256文字（無効）

## 4. テストケース詳細

### 4.1. `POST /api/v1/auth/register` (ユーザー登録)

#### 4.1.1. 正常系テストケース

**ケース1: 有効なユーザー情報で登録**
- 入力: 
  - email: "test@example.com"
  - username: "testuser"
  - password: "Test1234"
  - tenant_name: "Test Tenant"
- 期待結果: 
  - ステータスコード: 201 Created
  - レスポンスにaccess_tokenが含まれる
  - データベースにユーザーとテナントが作成される
  - パスワードがハッシュ化されている

**ケース2: 最小長の境界値で登録**
- 入力:
  - email: "a@b.c" (5文字)
  - username: "abc" (3文字)
  - password: "Test1234" (8文字)
  - tenant_name: "AB" (2文字)
- 期待結果: 201 Created

**ケース3: 最大長の境界値で登録**
- 入力:
  - email: "a" * 240 + "@example.com" (255文字以内)
  - username: "a" * 100 (100文字)
  - password: "Test1234" + "a" * 120 (128文字以内)
  - tenant_name: "a" * 255 (255文字)
- 期待結果: 201 Created

#### 4.1.2. 異常系テストケース

**ケース1: 既存のメールアドレスで登録**
- 入力: 既存のメールアドレス、有効なパスワード、テナント名
- 期待結果: 
  - ステータスコード: 400 Bad Request
  - エラーメッセージ: "Email already registered"

**ケース2: 既存のユーザー名で登録**
- 入力: 有効なメールアドレス、既存のユーザー名、有効なパスワード、テナント名
- 期待結果: 
  - ステータスコード: 400 Bad Request
  - エラーメッセージ: "Username already exists"

**ケース3: 無効なメールアドレス形式（境界値）**
- 入力: 
  - email: "a@b" (4文字、無効)
  - email: "invalid-email" (形式無効)
  - email: "@example.com" (@で始まる)
  - email: "test@" (@で終わる)
  - email: "test@example" (TLDなし)
- 期待結果: 422 Unprocessable Entity

**ケース4: メールアドレス最大長超過**
- 入力: email: "a" * 250 + "@example.com" (256文字以上)
- 期待結果: 422 Unprocessable Entity

**ケース5: 短すぎるパスワード（境界値）**
- 入力: password: "Test123" (7文字)
- 期待結果: 422 Unprocessable Entity

**ケース6: パスワードに大文字がない**
- 入力: password: "test1234"
- 期待結果: 422 Unprocessable Entity

**ケース7: パスワードに小文字がない**
- 入力: password: "TEST1234"
- 期待結果: 422 Unprocessable Entity

**ケース8: パスワードに数字がない**
- 入力: password: "TestTest"
- 期待結果: 422 Unprocessable Entity

**ケース9: パスワード最大長超過**
- 入力: password: "Test1234" + "a" * 125 (129文字以上)
- 期待結果: 422 Unprocessable Entity

**ケース10: 短すぎるユーザー名（境界値）**
- 入力: username: "ab" (2文字)
- 期待結果: 422 Unprocessable Entity

**ケース11: ユーザー名最大長超過**
- 入力: username: "a" * 101 (101文字)
- 期待結果: 422 Unprocessable Entity

**ケース12: ユーザー名に無効な文字**
- 入力: username: "test-user" (ハイフン含む)
- 期待結果: 422 Unprocessable Entity

**ケース13: 短すぎるテナント名（境界値）**
- 入力: tenant_name: "A" (1文字)
- 期待結果: 422 Unprocessable Entity

**ケース14: テナント名最大長超過**
- 入力: tenant_name: "a" * 256 (256文字)
- 期待結果: 422 Unprocessable Entity

### 4.2. `POST /api/v1/auth/register-tenant` (テナント登録)

**注意**: このエンドポイントは、テナントと管理者ユーザーを同時に登録します。`/api/v1/auth/register`とは異なり、テナント情報も含まれます。

#### 4.2.1. 正常系テストケース

**ケース1: 有効なテナント情報で登録**
- 入力:
  - tenant_name: "Test Tenant"
  - tenant_domain: "test-tenant"
  - admin_email: "admin@example.com"
  - admin_username: "adminuser"
  - admin_password: "AdminPassword1"
- 期待結果:
  - ステータスコード: 201 Created
  - レスポンスにtenant_id、admin_user_idが含まれる
  - データベースにテナントと管理者ユーザーが作成される
  - ユーザーがテナントに所属している

**ケース2: 最小長の境界値で登録**
- 入力:
  - tenant_name: "AB" (2文字)
  - tenant_domain: "abc" (3文字)
  - admin_email: "a@b.c" (5文字)
  - admin_username: "abc" (3文字)
  - admin_password: "AdminPass1" (8文字以上)
- 期待結果: 201 Created

**ケース3: 最大長の境界値で登録**
- 入力:
  - tenant_name: "a" * 255 (255文字)
  - tenant_domain: "a" * 255 (255文字)
  - admin_email: "a" * 240 + "@example.com" (255文字以内)
  - admin_username: "a" * 100 (100文字)
  - admin_password: "AdminPass1" + "a" * 120 (128文字以内)
- 期待結果: 201 Created

#### 4.2.2. 異常系テストケース

**ケース1: 既存のメールアドレスで登録**
- 入力: 既存のメールアドレス、有効なパスワード、テナント情報
- 期待結果:
  - ステータスコード: 409 Conflict
  - エラーメッセージ: "メールアドレスは既に登録されています" または "Email already registered"

**ケース2: 既存のテナント識別子で登録**
- 入力: 有効なメールアドレス、既存のtenant_domain、有効なパスワード
- 期待結果:
  - ステータスコード: 409 Conflict
  - エラーメッセージ: "テナント識別子は既に使用されています" または "Tenant domain already exists"

**ケース3: 無効なテナント識別子（短すぎる）**
- 入力: tenant_domain: "ab" (2文字、無効)
- 期待結果: 422 Unprocessable Entity

**ケース4: 無効なテナント識別子（無効な文字）**
- 入力: tenant_domain: "test tenant" (スペース含む)
- 期待結果: 422 Unprocessable Entity

**ケース5: 必須フィールド欠損**
- 入力: tenant_name、tenant_domain、admin_email、admin_username、admin_passwordのいずれかが欠損
- 期待結果: 422 Unprocessable Entity

### 4.3. `POST /api/v1/auth/login` (ユーザーログイン)

**ケース16: 空文字列**
- 入力: email: "", password: "", username: "", tenant_name: ""
- 期待結果: 422 Unprocessable Entity

**ケース17: 空白のみ**
- 入力: email: "   ", password: "   ", username: "   ", tenant_name: "   "
- 期待結果: 422 Unprocessable Entity

**ケース18: SQLインジェクション試行**
- 入力: username: "admin'; DROP TABLE users; --"
- 期待結果: 422 Unprocessable Entity または適切にエスケープされる

**ケース19: XSS試行**
- 入力: username: "<script>alert('XSS')</script>"
- 期待結果: 422 Unprocessable Entity または適切にサニタイズされる

### 4.2. `POST /api/v1/auth/login` (ユーザーログイン)

#### 4.2.1. 正常系テストケース

**ケース1: 有効な認証情報でログイン**
- 入力: 登録済みのメールアドレス、正しいパスワード
- 期待結果: 
  - ステータスコード: 200 OK
  - レスポンスにaccess_token、refresh_tokenが含まれる
  - token_type: "bearer"
  - expires_inが設定されている

**ケース2: ログイン後にlast_loginが更新される**
- 入力: 有効な認証情報
- 期待結果: データベースのlast_loginが更新される

#### 4.2.2. 異常系テストケース

**ケース1: 登録されていないメールアドレス**
- 入力: 未登録のメールアドレス、任意のパスワード
- 期待結果: 
  - ステータスコード: 401 Unauthorized
  - エラーメッセージ: "Incorrect email or password"

**ケース2: 間違ったパスワード**
- 入力: 登録済みのメールアドレス、間違ったパスワード
- 期待結果: 
  - ステータスコード: 401 Unauthorized
  - エラーメッセージ: "Incorrect email or password"

**ケース3: 非アクティブユーザー**
- 入力: 非アクティブユーザーのメールアドレス、正しいパスワード
- 期待結果: 
  - ステータスコード: 401 Unauthorized
  - エラーメッセージ: "Inactive user"

**ケース4: メールアドレス未入力**
- 入力: email: "", password: "Test1234"
- 期待結果: 422 Unprocessable Entity

**ケース5: パスワード未入力**
- 入力: email: "test@example.com", password: ""
- 期待結果: 422 Unprocessable Entity

**ケース6: 無効なメールアドレス形式**
- 入力: email: "invalid-email", password: "Test1234"
- 期待結果: 422 Unprocessable Entity

**ケース7: 大文字小文字の区別**
- 入力: email: "Test@Example.Com" (登録時は小文字)
- 期待結果: 200 OK または 401 Unauthorized（実装による）

**ケース8: 前後の空白**
- 入力: email: "  test@example.com  ", password: "  Test1234  "
- 期待結果: 200 OK または 422 Unprocessable Entity（実装による）

### 4.3. `POST /api/v1/auth/logout` (ユーザーログアウト)

#### 4.3.1. 正常系テストケース

**ケース1: 有効なアクセストークンでログアウト**
- 入力: 有効なアクセストークン
- 期待結果: 
  - ステータスコード: 200 OK
  - メッセージ: "Successfully logged out"
  - トークンが無効化される

**ケース2: ログアウト後のトークン使用不可**
- 入力: ログアウト済みのトークン
- 期待結果: 401 Unauthorized

#### 4.3.2. 異常系テストケース

**ケース1: 無効なアクセストークン**
- 入力: 無効なトークン
- 期待結果: 401 Unauthorized

**ケース2: トークンなし**
- 入力: Authorizationヘッダーなし
- 期待結果: 401 Unauthorized

**ケース3: 期限切れトークン**
- 入力: 期限切れのトークン
- 期待結果: 401 Unauthorized

**ケース4: 不正なトークン形式**
- 入力: "Bearer invalid.token.format"
- 期待結果: 401 Unauthorized

### 4.4. `POST /api/v1/auth/password-reset` (パスワードリセット要求)

#### 4.4.1. 正常系テストケース

**ケース1: 登録済みのメールアドレスでリセット要求**
- 入力: 登録済みのメールアドレス
- 期待結果: 
  - ステータスコード: 200 OK
  - メッセージ: "Password reset email sent"
  - パスワードリセットトークンが生成される
  - メール送信が実行される（モック）

#### 4.4.2. 異常系テストケース

**ケース1: 未登録のメールアドレスでリセット要求**
- 入力: 未登録のメールアドレス
- 期待結果: 
  - ステータスコード: 200 OK（セキュリティ上の理由）
  - メール送信されない

**ケース2: 無効なメールアドレス形式**
- 入力: "invalid-email-format"
- 期待結果: 422 Unprocessable Entity

**ケース3: メールアドレス未入力**
- 入力: email: ""
- 期待結果: 422 Unprocessable Entity

**ケース4: 最大長超過のメールアドレス**
- 入力: "a" * 250 + "@example.com"
- 期待結果: 422 Unprocessable Entity

### 4.5. `POST /api/v1/auth/password-reset/confirm` (パスワードリセット確認)

#### 4.5.1. 正常系テストケース

**ケース1: 有効なトークンと新しいパスワードでリセット**
- 入力: 有効なリセットトークン、新しいパスワード
- 期待結果: 
  - ステータスコード: 200 OK
  - メッセージ: "Password has been reset"
  - パスワードが更新される
  - 新しいパスワードでログイン可能

**ケース2: 最小長のパスワードでリセット**
- 入力: 有効なトークン、password: "Test1234" (8文字)
- 期待結果: 200 OK

#### 4.5.2. 異常系テストケース

**ケース1: 無効なリセットトークン**
- 入力: 無効なトークン、新しいパスワード
- 期待結果: 
  - ステータスコード: 400 Bad Request
  - エラーメッセージ: "Invalid or expired token"

**ケース2: 期限切れトークン**
- 入力: 期限切れのトークン、新しいパスワード
- 期待結果: 400 Bad Request

**ケース3: 短すぎる新しいパスワード**
- 入力: 有効なトークン、password: "Test123" (7文字)
- 期待結果: 422 Unprocessable Entity

**ケース4: パスワード要件不満足**
- 入力: 有効なトークン、password: "test1234" (大文字なし)
- 期待結果: 422 Unprocessable Entity

**ケース5: トークンなし**
- 入力: token: "", password: "Test1234"
- 期待結果: 422 Unprocessable Entity

**ケース6: 新しいパスワードなし**
- 入力: token: "valid-token", password: ""
- 期待結果: 422 Unprocessable Entity

### 4.6. `POST /api/v1/auth/verify-email` (メールアドレス検証)

#### 4.6.1. 正常系テストケース

**ケース1: 有効な検証トークンでメールアドレス検証**
- 入力: 有効な検証トークン
- 期待結果: 
  - ステータスコード: 200 OK
  - メッセージ: "Email successfully verified"
  - ユーザーのis_verifiedがtrueになる

#### 4.6.2. 異常系テストケース

**ケース1: 無効な検証トークン**
- 入力: 無効な検証トークン
- 期待結果: 
  - ステータスコード: 400 Bad Request
  - エラーメッセージ: "Invalid or expired token"

**ケース2: 期限切れトークン**
- 入力: 期限切れのトークン
- 期待結果: 400 Bad Request

**ケース3: トークンなし**
- 入力: token: ""
- 期待結果: 422 Unprocessable Entity

**ケース4: 既に検証済みのメールアドレス**
- 入力: 既に検証済みユーザーの有効なトークン
- 期待結果: 200 OK または 400 Bad Request（実装による）

### 4.7. `GET /api/v1/auth/me` (現在のユーザー情報取得)

#### 4.7.1. 正常系テストケース

**ケース1: 有効なアクセストークンでユーザー情報取得**
- 入力: 有効なアクセストークン
- 期待結果: 
  - ステータスコード: 200 OK
  - レスポンスにユーザー情報が含まれる
  - email、id、tenant_id、roleが含まれる
  - パスワードが含まれない

#### 4.7.2. 異常系テストケース

**ケース1: 無効なアクセストークン**
- 入力: 無効なトークン
- 期待結果: 401 Unauthorized

**ケース2: トークンなし**
- 入力: Authorizationヘッダーなし
- 期待結果: 401 Unauthorized

**ケース3: 期限切れトークン**
- 入力: 期限切れのトークン
- 期待結果: 401 Unauthorized

**ケース4: 非アクティブユーザーのトークン**
- 入力: 非アクティブユーザーの有効なトークン
- 期待結果: 401 Unauthorized または 403 Forbidden（実装による）

### 4.8. `POST /api/v1/auth/refresh` (トークンリフレッシュ)

#### 4.8.1. 正常系テストケース

**ケース1: 有効なリフレッシュトークンでトークン更新**
- 入力: 有効なリフレッシュトークン
- 期待結果: 
  - ステータスコード: 200 OK
  - 新しいaccess_tokenとrefresh_tokenが返却される

#### 4.8.2. 異常系テストケース

**ケース1: 無効なリフレッシュトークン**
- 入力: 無効なトークン
- 期待結果: 401 Unauthorized

**ケース2: 期限切れリフレッシュトークン**
- 入力: 期限切れのトークン
- 期待結果: 401 Unauthorized

**ケース3: トークンなし**
- 入力: refresh_token: ""
- 期待結果: 422 Unprocessable Entity

### 4.9. `POST /api/v1/auth/login/oauth` (OAuth2ログイン)

#### 4.9.1. 正常系テストケース

**ケース1: 有効な認証情報でOAuth2ログイン**
- 入力: username（メールアドレス）、password
- 期待結果: 
  - ステータスコード: 200 OK
  - access_token、refresh_tokenが返却される

#### 4.9.2. 異常系テストケース

**ケース1: 無効な認証情報**
- 入力: 間違ったusername、password
- 期待結果: 401 Unauthorized

**ケース2: 必須フィールド欠損**
- 入力: username: "", password: ""
- 期待結果: 422 Unprocessable Entity

## 5. セキュリティテスト

### 5.1. SQLインジェクション対策
- 全ての入力値に対してSQLインジェクション試行をテスト
- ORM使用の確認

### 5.2. XSS対策
- 全ての入力値に対してXSS試行をテスト
- 出力時のサニタイズ確認

### 5.3. CSRF対策
- トークンベース認証の確認
- セッション管理の確認

### 5.4. レート制限
- ログイン試行回数制限
- パスワードリセット要求回数制限

### 5.5. パスワード強度
- 弱いパスワードの拒否
- パスワードハッシュ化の確認

## 6. パフォーマンステスト

### 6.1. レスポンス時間
- ログイン: 3秒以内
- 登録: 5秒以内
- その他: 2秒以内

### 6.2. 同時接続
- 100並行リクエストでの動作確認

## 7. テストデータ

### 7.1. テストユーザー
- アクティブユーザー
- 非アクティブユーザー
- 検証済みユーザー
- 未検証ユーザー

### 7.2. テストテナント
- アクティブテナント
- 停止テナント

## 8. テスト実行手順

```bash
cd api
pytest tests/test_auth.py -v --cov=app.api.v1.endpoints.auth
```

## 9. 期待されるカバレッジ

- 行カバレッジ: 90%以上
- 分岐カバレッジ: 85%以上
- 関数カバレッジ: 100%
