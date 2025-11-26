# Railway デプロイエラー 段階的トラブルシューティング

## 状況整理

### 元の設定（動いていたはず）
```
GitHub Secrets RAILWAY_TOKEN = 19bf157e-dba6-4c5d-8a2d-170ebcfd591d
（ai_chatbot_token の値）
```

### 現在の状況
- GitHub Actionsで "Unauthorized" エラー
- "Project Token not found" エラー

### 推測される原因
1. GitHub Secretsの値が壊れた（改行・空白混入）
2. トークンが実際に無効化された
3. 他の設定（PROJECT_ID、SERVICE名など）が間違っている

## 段階的テスト手順

### 🔍 Test 1: 元の値で再試行（最優先）

#### 1-1. GitHub Secretsを元の値に戻す

```
1. GitHub リポジトリ → Settings → Secrets and variables → Actions
2. RAILWAY_TOKEN をクリック → Update
3. 以下の値を**慎重に**貼り付け（前後に空白・改行なし）:
   19bf157e-dba6-4c5d-8a2d-170ebcfd591d
4. Update secret をクリック
```

**重要なポイント**:
- [ ] 値の前後に空白がないことを確認
- [ ] 改行が入っていないことを確認
- [ ] ハイフン（-）も含めて全文字が入っていることを確認
- [ ] コピー元のテキストファイルにも改行がないことを確認

#### 1-2. 他のSecretsも確認

```
RAILWAY_DEMO_PROJECT_ID = 1dcf0ad6-d714-4359-bdcb-d35e03474226
→ 正しいか確認（RailwayのURLから取得）

RAILWAY_DEMO_SERVICE = ai_chatbot_app
→ Railway Service Name と一致するか確認
```

#### 1-3. GitHub Actionsを実行

```
Actions タブ → Deploy to Environments → Run workflow
→ deploy_backend: true を選択
→ Run workflow
```

#### 1-4. 結果を確認

**✅ 成功した場合**:
→ 問題はGitHub Secretsの値の入力ミスだった
→ このトークンを継続使用（問題なし）

**❌ 失敗した場合（同じエラー）**:
→ Test 2 へ進む

---

### 🔍 Test 2: トークンの有効性を確認

元の値で失敗した場合、トークンが実際に無効化されている可能性があります。

#### 2-1. Railway Tokensページを確認

```
https://railway.app/account/tokens

確認事項:
- "ai_chatbot_token" が存在するか？
- 存在しない → Test 3（新トークン）へ
- 存在する → Last Used を確認
```

#### 2-2. トークンが存在する場合

```
Last Used を確認:
- 最近使用されている → トークンは有効
- 使用履歴なし → GitHub Secretsの値が間違っている可能性

対処:
1. Railway側でトークンの末尾を確認（****-591d など）
2. GitHub Secretsの値と一致するか推測
3. 一致していそうなら、Test 1 を再度実行
```

---

### 🔍 Test 3: 新しいトークンで試行

元のトークンが無効な場合、新しいトークンを使用します。

#### 3-1. 新しいトークンを使用

すでに生成済みのトークン:
```
Railway_Synergysoft_Token_v2
e62118d3-49b7-4c5b-80e6-54265e78bce0
```

#### 3-2. GitHub Secretsを更新

```
RAILWAY_TOKEN = e62118d3-49b7-4c5b-80e6-54265e78bce0
```

#### 3-3. GitHub Actionsを実行

```
Actions タブ → Run workflow
```

#### 3-4. 結果を確認

**✅ 成功した場合**:
→ 元のトークンが無効化されていた
→ 新しいトークンを継続使用
→ 古い`ai_chatbot_token`を削除（存在する場合）

**❌ 失敗した場合（同じエラー）**:
→ Test 4 へ進む

---

### 🔍 Test 4: 他の設定を確認

トークンを変えても失敗する場合、他に問題があります。

#### 4-1. PROJECT_ID を確認

```
Railway Dashboard → プロジェクトを開く
URL を確認: https://railway.app/project/{PROJECT_ID}

GitHub Secrets の RAILWAY_DEMO_PROJECT_ID と一致するか？
- 一致しない → 更新
- 一致する → 4-2 へ
```

#### 4-2. SERVICE名を確認

```
Railway Dashboard → プロジェクト → Variables タブ
RAILWAY_SERVICE_NAME の値を確認（例: ai_chatbot_app）

GitHub Secrets の RAILWAY_DEMO_SERVICE と一致するか？
- 一致しない → 更新
- 一致する → 4-3 へ
```

#### 4-3. ワークフローファイルを確認

```bash
# ローカルで確認
cat .github/workflows/deploy.yml | grep -A 10 "Deploy Backend to Railway"
```

確認ポイント:
- [ ] `RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}` が正しいか
- [ ] `RAILWAY_PROJECT_ID: ${{ secrets.RAILWAY_DEMO_PROJECT_ID }}` が正しいか
- [ ] `RAILWAY_SERVICE: ${{ secrets.RAILWAY_DEMO_SERVICE }}` が設定されているか

---

### 🔍 Test 5: Railway CLIをローカルでテスト

GitHub Actions の問題か、Railway の問題かを切り分けます。

#### 5-1. ローカル環境でテスト

```bash
# Railway CLI をインストール
npm install -g @railway/cli

# トークンを設定
export RAILWAY_TOKEN="19bf157e-dba6-4c5d-8a2d-170ebcfd591d"
export RAILWAY_PROJECT_ID="1dcf0ad6-d714-4359-bdcb-d35e03474226"

# 認証確認
railway whoami

# プロジェクト一覧
railway list
```

**結果**:
- ✅ 成功 → トークンは有効、GitHub Actions側に問題
- ❌ 失敗 → トークンが無効、新しいトークンで再テスト

---

## テスト結果記録

### Test 1: 元の値で再試行
- [ ] 実施日時: ___________
- [ ] 結果: ✅ 成功 / ❌ 失敗
- [ ] エラーメッセージ: ___________

### Test 2: トークンの有効性確認
- [ ] `ai_chatbot_token` 存在: YES / NO
- [ ] Last Used: ___________

### Test 3: 新しいトークンで試行
- [ ] 実施日時: ___________
- [ ] 結果: ✅ 成功 / ❌ 失敗
- [ ] エラーメッセージ: ___________

### Test 4: 他の設定確認
- [ ] PROJECT_ID 一致: YES / NO
- [ ] SERVICE名 一致: YES / NO

### Test 5: ローカルテスト
- [ ] `railway whoami` 結果: ___________
- [ ] `railway list` 結果: ___________

---

## 最終判断

### 成功したテスト
Test _____ で成功

### 使用するトークン
```
Token名: ___________
Token値: ___________
```

### 今後の対応
- [ ] 古いトークンを削除（必要に応じて）
- [ ] トークンを安全な場所に保管
- [ ] ドキュメントを更新

