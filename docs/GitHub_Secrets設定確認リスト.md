# GitHub Secrets設定確認リスト

## Railway関連のSecrets

デプロイに必要な3つのSecretsを確認してください。

### 1. RAILWAY_TOKEN
- **種類**: Account API Token（推奨）
- **生成場所**: https://railway.app/account/tokens
- **値の形式**: `ey...`で始まる長い文字列（約200文字）
- **確認ポイント**:
  - [ ] Account API Tokenを生成（Project Tokenではない）
  - [ ] ワークスペースを正しく選択した
  - [ ] トークン全体をコピーした（先頭から最後まで）
  - [ ] 前後に空白・改行が混入していない
  - [ ] GitHub Secretsに正しく貼り付けた

### 2. RAILWAY_DEMO_PROJECT_ID
- **取得場所**: RailwayプロジェクトのURL
- **値の形式**: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`（UUID形式）
- **取得方法**:
  ```
  1. Railway Dashboard → プロジェクトを開く
  2. URLを確認: https://railway.app/project/{PROJECT_ID}
  3. PROJECT_IDの部分をコピー
  ```
- **確認ポイント**:
  - [ ] URLから正しくコピーした
  - [ ] UUIDの形式になっている
  - [ ] ハイフン（-）も含まれている
  - [ ] 前後に空白がない

### 3. RAILWAY_DEMO_SERVICE
- **取得場所**: Railwayプロジェクトの設定
- **値の形式**: サービス名（例：`ai_chatbot_app`）
- **取得方法**:
  ```
  1. Railway Dashboard → プロジェクト → Settings
  2. General → Service Name を確認
  3. サービス名をコピー
  ```
- **確認ポイント**:
  - [ ] Service Nameと完全一致
  - [ ] 大文字小文字が正しい
  - [ ] 前後に空白がない
  - [ ] アンダースコア（_）やハイフン（-）が正しい

## 設定確認手順

### GitHub側での確認
```
1. GitHubリポジトリを開く
2. Settings → Secrets and variables → Actions
3. 以下の3つが存在することを確認：
   - RAILWAY_TOKEN
   - RAILWAY_DEMO_PROJECT_ID
   - RAILWAY_DEMO_SERVICE
4. それぞれの「Updated」日時を確認（最近更新されているか）
```

### Railway側での確認
```
1. https://railway.app/account/tokens を開く
2. 作成したトークンが表示されているか確認
3. Last Used の日時を確認（GitHub Actionsで使用されたか）
4. ワークスペースが正しいか確認
```

## よくある間違い

### ❌ RAILWAY_TOKEN
1. **Project Tokenを使用している**
   - Account API Tokenを生成してください
   
2. **トークンのコピーが不完全**
   - 最後の数文字が欠けている
   - 先頭に空白が入っている
   
3. **古いトークンを使用**
   - 新しくトークンを生成したのにGitHub Secretsを更新していない
   
4. **間違ったワークスペースを選択**
   - デプロイ対象プロジェクトが属するワークスペースを選択してください

### ❌ RAILWAY_DEMO_PROJECT_ID
1. **URLの一部だけをコピー**
   - プロジェクトID全体（UUID形式）をコピーしてください
   
2. **別のプロジェクトのIDを使用**
   - デプロイ対象のプロジェクトIDを確認してください

### ❌ RAILWAY_DEMO_SERVICE
1. **表示名とService Nameの混同**
   - Settings → General → Service Name を使用してください
   
2. **大文字小文字の違い**
   - 完全一致が必要です（例：`AI_Chatbot_App` ≠ `ai_chatbot_app`）

## デバッグ方法

### トークンの長さを確認
```bash
# ローカルで確認（実際の値は表示されない）
echo ${#RAILWAY_TOKEN}
# 期待値: 約200前後の数字が表示される
```

### トークンの先頭を確認
```bash
# ローカルで確認
echo "$RAILWAY_TOKEN" | head -c 5
# 期待値: "ey..." のような文字列
```

### トークンの改行を確認
```bash
# ローカルで確認
echo "$RAILWAY_TOKEN" | wc -l
# 期待値: 1（1行のみ）
# NGパターン: 2以上（改行が混入している）
```

## トラブルシューティング

### エラー: "Unauthorized. Please login"
**原因**: RAILWAY_TOKEN が無効または設定されていない

**対処**:
1. Railway で新しい Account API Token を生成
2. GitHub Secrets の RAILWAY_TOKEN を更新
3. ワークフローを再実行

### エラー: "Project Token not found"
**原因**: トークンまたはプロジェクトIDが間違っている

**対処**:
1. Account API Token（ワークスペース選択版）を使用しているか確認
2. RAILWAY_DEMO_PROJECT_ID が正しいか確認
3. ワークスペースが正しいか確認

### エラー: "Service not found"
**原因**: RAILWAY_DEMO_SERVICE が間違っている

**対処**:
1. Railway Dashboard → Settings → General → Service Name を確認
2. GitHub Secrets の RAILWAY_DEMO_SERVICE を更新

## 推奨フロー

### 完全リセット手順（確実に動作させる）
```
1. Railway側
   ✓ Account API Token を新規生成
   ✓ ワークスペースを正しく選択
   ✓ トークンをコピー（「Copy」ボタン使用）
   
2. GitHub側
   ✓ RAILWAY_TOKEN を削除 → 再作成
   ✓ 新しいトークンを貼り付け
   ✓ RAILWAY_DEMO_PROJECT_ID を確認・更新
   ✓ RAILWAY_DEMO_SERVICE を確認・更新
   
3. 動作確認
   ✓ GitHub Actions → 手動実行
   ✓ デバッグ出力を確認
   ✓ デプロイ成功を確認
```

