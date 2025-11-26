# Railway デプロイエラー 即座対応手順

## 状況
- 以前: `ai_chatbot_token`（`19bf157e-dba6-4c5d-8a2d-170ebcfd591d`）を使用
- 現在: `ai_chatbot_token`が削除されているため、GitHub Actionsで"Unauthorized"エラー
- 新規生成: `Railway_Synergysoft_Token_v2`（`e62118d3-49b7-4c5b-80e6-54265e78bce0`）

## 即座対応

### Step 1: 新しいトークンをコピー（完了済み）
```
✅ e62118d3-49b7-4c5b-80e6-54265e78bce0
```
既に生成済みで、画面に表示されています。

### Step 2: GitHub Secretsを更新

```
1. GitHub リポジトリを開く
   https://github.com/YoshihideOno/ai_chatbot_project

2. Settings → Secrets and variables → Actions

3. RAILWAY_TOKEN をクリック → Update

4. 新しい値を貼り付け:
   e62118d3-49b7-4c5b-80e6-54265e78bce0

5. Update secret をクリック
```

### Step 3: 他のSecretsを確認

```
RAILWAY_DEMO_PROJECT_ID = 1dcf0ad6-d714-4359-bdcb-d35e03474226
（変更不要）

RAILWAY_DEMO_SERVICE = ai_chatbot_app
（変更不要）
```

### Step 4: 不要なRailway環境変数を削除

Railway側のShared VariablesとService Variablesから以下を削除：
```
- RAILWAY_TOKEN（削除）
- RAILWAY_DEMO_PROJECT_ID（削除）
```

理由: これらはGitHub Actions専用で、Railway側では不要。

### Step 5: GitHub Actionsを再実行

```
1. GitHub リポジトリ → Actions タブ
2. 失敗したワークフローを選択
3. Re-run all jobs をクリック
```

## 期待される結果

```
✅ Deploying to Railway...
✅ Railway CLI version: x.x.x
✅ Checking token length: 36
✅ Project ID set: YES
✅ Service name: ai_chatbot_app
✅ Attempting authentication...
✅ Logged in as: Synergysoft
✅ Listing projects...
✅ AI Chatbot
✅ Starting deployment...
✅ Build started...
✅ Deployment successful
```

## チェックリスト

- [ ] 新しいトークンをコピーした（`e62118d3-49b7-4c5b-80e6-54265e78bce0`）
- [ ] GitHub Secrets `RAILWAY_TOKEN` を更新した
- [ ] Railway Shared Variables から `RAILWAY_TOKEN` を削除した
- [ ] Railway Service Variables から `RAILWAY_TOKEN` を削除した
- [ ] GitHub Actions を再実行した

## トークンの確認

### 現在有効なトークン
- `Railway_Synergysoft_Token` (****-33b9)
- `Railway_Synergysoft_Token_v2` (****-bce0) ← 使用中

### 削除されたトークン（無効）
- `ai_chatbot_token` (`19bf157e-dba6-4c5d-8a2d-170ebcfd591d`) ← 以前使用していたが削除済み

## 今後の管理

### トークンの命名規則
- Account API Tokenには分かりやすい名前を付ける
- 例: `github-actions-{環境名}`、`{プロジェクト名}-token`

### トークンの保管
- 生成時に必ず安全な場所に保管する
- パスワードマネージャーに保存推奨
- 削除前に新しいトークンに移行完了を確認

### トークンのローテーション
- 定期的にトークンを更新（3〜6ヶ月ごと）
- 古いトークンは新しいトークンに移行後に削除

