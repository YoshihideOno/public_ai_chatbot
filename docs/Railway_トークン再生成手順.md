# Railway APIトークン設定確認手順（緊急対応）

## 状況確認

- ✅ Account API Token「Railway_Synergysoft_Token」は正しく生成されている
- ✅ Railwayのワークスペース「Synergysoft」が選択されている
- ⚠️ GitHub Secretsの値が正しく設定されていない可能性

## 対応手順

### 1. Railwayのトークン値を確認

Railway Shared Variables（画像4枚目）から確認：
```
RAILWAY_TOKEN = 9245c69f-682f-4ae7-b73f-dc0100c233b9
```

この値を**正確にコピー**してください（ダッシュも含めて全文字）。

### 2. GitHub Secretsの値を確認・更新

**重要**: Railway側の環境変数に表示されているトークン値は、GitHub Actionsでは使用されません。GitHub SecretsにAccount API Tokenの値を設定する必要があります。

しかし、**Account API Tokenは一度しか表示されません**。すでに画面を閉じてしまった場合は、以下の対処が必要です：

#### Option A: トークン値を覚えている・保存している場合
```
1. GitHub リポジトリ → Settings → Secrets and variables → Actions
2. RAILWAY_TOKEN をクリック → Update
3. 保存していたトークン値を貼り付け
4. Update secret をクリック
```

#### Option B: トークン値が不明な場合（推奨）
```
1. https://railway.app/account/tokens にアクセス
2. "Railway_Synergysoft_Token" を削除
3. 「Create Token」をクリック
4. Workspace: "Synergysoft" を選択
5. Token name: Railway_Synergysoft_Token_v2
6. 「Create」をクリック
7. ⚠️ 表示されたトークンを即座にコピー（一度しか表示されない！）
8. GitHub Secrets の RAILWAY_TOKEN を更新
```

**確認ポイント**:
- [ ] トークン全体をコピーした（最初から最後まで）
- [ ] トークンはUUID形式（例: 9245c69f-682f-4ae7-b73f-dc0100c233b9）
- [ ] 前後に空白・改行がない

### 3. 不要なRailway環境変数を削除（重要）

Railway側の環境変数に`RAILWAY_TOKEN`と`RAILWAY_DEMO_PROJECT_ID`が設定されていますが、これらは**不要**です。

#### Shared Variables（production環境）から削除
```
1. Railway Project → Settings → Shared Variables
2. "production" 環境を展開
3. "RAILWAY_TOKEN" の×ボタンをクリックして削除
4. "RAILWAY_DEMO_PROJECT_ID" の×ボタンをクリックして削除
```

#### Service Variables（ai_chatbot_app）から削除
```
1. Railway Project → ai_chatbot_app → Variables
2. "RAILWAY_TOKEN" を探して×ボタンをクリックして削除
3. "RAILWAY_DEMO_PROJECT_ID" を探して削除（存在する場合）
```

**理由**: これらの変数はGitHub Actions実行時に使用するものであり、Railway自体の環境変数として設定する必要はありません。

### 4. GitHub Secretsの最終確認

以下の3つが正しく設定されているか確認：

```
RAILWAY_TOKEN: 
  - 値: 新しく生成したAccount API Token（Hobby Workspace選択版）
  - 形式: UUID形式（例: 9245c69f-682f-4ae7-b73f-dc0100c233b9）

RAILWAY_DEMO_PROJECT_ID:
  - 値: 1dcf0ad6-d714-4359-bdcb-d35e03474226
  - ✅ 現在の設定が正しい

RAILWAY_DEMO_SERVICE:
  - 値: ai_chatbot_app
  - ✅ Railwayの画面で確認（RAILWAY_SERVICE_NAME）
```

### 5. GitHub Actionsを再実行

```
1. GitHubリポジトリ → Actions タブ
2. 失敗したワークフローを選択
3. 「Re-run all jobs」をクリック
```

## チェックリスト

作業前に確認：

- [ ] Account API Tokenの値を確認した（新規生成した場合はコピー済み）
- [ ] GitHub Secrets `RAILWAY_TOKEN` を更新した
- [ ] トークンに前後の空白・改行がないことを確認した
- [ ] Railway Shared Variablesから `RAILWAY_TOKEN` を削除した
- [ ] Railway Service Variablesから `RAILWAY_TOKEN` を削除した
- [ ] GitHub Secretsの3つの値（RAILWAY_TOKEN, RAILWAY_DEMO_PROJECT_ID, RAILWAY_DEMO_SERVICE）を確認した
- [ ] GitHub Actionsを再実行した

## 期待される結果

```
✅ Deploying to Railway...
✅ Railway CLI version: ...
✅ Checking token length: 36（UUID形式の場合）
✅ Project ID set: YES
✅ Service name: ai_chatbot_app
✅ Attempting authentication...
✅ Logged in as: Synergysoft (または表示名)
✅ Listing projects...
✅ AI Chatbot (プロジェクト名が表示される)
✅ Starting deployment...
✅ Deployment successful
```

## トラブルシューティング

### エラー: "Unauthorized"
- 原因: トークンが正しくコピーされていない
- 対処: トークンを再生成してコピーし直す

### エラー: "Project Token not found"
- 原因: RAILWAY_PROJECT_IDが間違っている
- 対処: Railway DashboardのURLから正しいプロジェクトIDを取得

