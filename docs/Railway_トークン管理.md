# Railway APIトークン管理ガイド

## Railwayの階層構造とトークン

### Railwayの構造
```
Account（アカウント）
  └── Workspace（ワークスペース）
       ├── Project A
       ├── Project B
       └── Project C
```

### 2種類のトークン

### 1. Account API Token（推奨：CI/CD用）
- **スコープ**: 特定の**ワークスペース**を指定し、そのワークスペース配下の**全プロジェクト**にアクセス可能
- **生成場所**: Account Settings → Tokens (https://railway.app/account/tokens)
- **生成時の設定**: ワークスペースを選択する必要がある
- **用途**: GitHub Actions、同一ワークスペース内の複数プロジェクト管理、長期運用
- **メリット**:
  - ✅ 1つのトークンでワークスペース内の複数プロジェクトを管理
  - ✅ プロジェクト再作成時も継続使用可能（同一ワークスペース内）
  - ✅ CI/CDパイプラインに最適
  - ✅ 管理が容易
  - ✅ ワークスペースレベルでの統一的な管理

### 2. Project Token（限定的な用途向け）
- **スコープ**: 特定の**プロジェクトのみ**にアクセス可能
- **生成場所**: Project Settings → Tokens
- **用途**: 単一プロジェクトへの限定的なアクセス
- **メリット**:
  - ✅ セキュリティスコープが最も限定的
  - ✅ 外部サービスへの共有に適している
  - ✅ プロジェクト単位での細かいアクセス制御
- **デメリット**:
  - ❌ プロジェクトごとに生成・管理が必要
  - ❌ プロジェクト削除時にトークンも無効化
  - ❌ 複数プロジェクトで共有できない

### 推奨：GitHub ActionsにはAccount API Token（ワークスペース指定）を使用

### 重要なポイント

#### ワークスペースとプロジェクトの関係
- 1つのアカウントは複数のワークスペースを持つことができる
- 1つのワークスペースは複数のプロジェクトを持つことができる
- Account API Tokenは**1つのワークスペース**を指定して生成する
- そのトークンは指定したワークスペース配下の**全プロジェクト**にアクセス可能

#### トークン選択の基準
| 状況 | 推奨トークン | 理由 |
|------|------------|------|
| CI/CDで複数プロジェクトをデプロイ | Account API Token | 1つのトークンで管理可能 |
| 単一プロジェクトのみ使用 | Account API Token | 将来の拡張性を考慮 |
| 外部サービスとの連携 | Project Token | セキュリティスコープを最小化 |
| 一時的なアクセス権限付与 | Project Token | プロジェクト削除で自動無効化 |

## トークンが無効になる理由

### 1. Account API Tokenが無効化される場合
- ❌ **パスワード変更時**（セキュリティ設定による）
- ❌ **アカウント削除・停止**
- ❌ **セキュリティ違反の検出**
- 🗑️ **手動での削除**（Railway Dashboard → Account Settings → Tokens）

### 2. Project Tokenが無効化される場合（より頻繁に発生）
- ❌ **プロジェクトの削除**
- ❌ **プロジェクトトークンの再生成**（古いトークンが無効化される）
- ⚠️ **プロジェクトへのアクセス権限喪失**
- 🗑️ **手動での削除**（Project Settings → Tokens）
- ⚠️ **プロジェクト設定の変更**（まれ）

### 3. 共通の原因
- ⚠️ **GitHub Secretsへの設定ミス**（空白・改行の混入）
- ⚠️ **環境変数名の間違い**（`RAILWAY_TOKEN`）
- ⚠️ **トークンのコピー時の不備**

### 3. 設定ミスの可能性
- ⚠️ トークンのコピー時に空白・改行が混入
- ⚠️ GitHub Secretsへの貼り付けミス
- ⚠️ 環境変数名の間違い（`RAILWAY_TOKEN`）

## トークンの確認方法

### Railway側
1. [Railway Dashboard](https://railway.app/) → Account Settings → Tokens
2. 現在のトークン一覧を確認
3. トークンの作成日時とLast Usedを確認

### GitHub側
1. GitHubリポジトリ → Settings → Secrets and variables → Actions
2. `RAILWAY_TOKEN`が存在するか確認
3. 更新日時を確認

## トークンの生成・再生成手順

### 推奨：Account API Tokenの生成（CI/CD用）

#### 1. Railway側
```
1. https://railway.app/account/tokens にアクセス
2. 「Create Token」をクリック
3. 対象の**ワークスペースを選択**（重要！）
   - デフォルトワークスペースまたは特定のワークスペース
   - 選択したワークスペース配下の全プロジェクトにアクセス可能になる
4. Token name: github-actions-ci-cd（わかりやすい名前）
5. 生成されたトークンをコピー（⚠️ 一度しか表示されない！）
```

**ワークスペースの確認方法**:
- Railway Dashboard → 左上のドロップダウンでワークスペース一覧を確認
- プロジェクトがどのワークスペースに属しているか確認
- 複数ワークスペースがある場合は、対象プロジェクトと同じワークスペースを選択

#### 2. GitHub側
```
1. リポジトリ → Settings → Secrets and variables → Actions
2. RAILWAY_TOKEN を探す（なければ「New repository secret」）
3. 「Update」をクリック（新規の場合はスキップ）
4. 新しいAccount API Tokenを貼り付け
5. 「Update secret」または「Add secret」をクリック
```

### オプション：Project Tokenの生成（限定的な用途）

#### 1. Railway側
```
1. Railway Project → Settings → Tokens
2. 「Create Token」をクリック
3. Token name: ci-cd-project-specific
4. 生成されたトークンをコピー
```

⚠️ **注意**: Project Tokenはプロジェクト再作成時に無効化されるため、長期運用にはAccount API Tokenを推奨

## デバッグ方法

### GitHub Actionsで確認
```yaml
- name: Test Railway Authentication
  run: |
    npm install -g @railway/cli
    railway whoami
  env:
    RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
```

### ローカルで確認
```bash
# トークンをエクスポート
export RAILWAY_TOKEN="your-token-here"

# 認証確認
railway whoami

# プロジェクト一覧
railway list
```

## 予防策

### 1. トークンの定期的な更新
- 3〜6ヶ月ごとにトークンを更新
- 古いトークンを削除

### 2. トークンの使用状況を監視
- Railway Dashboard でLast Usedを確認
- 不審なアクティビティがないか確認

### 3. 複数のトークンを管理
- CI/CD用
- 開発用
- 緊急用（バックアップ）

## トラブルシューティング

### エラー: "Unauthorized. Please login with `railway login`"

**原因**:
- トークンが無効または期限切れ
- トークンの形式が間違っている
- 環境変数が正しく設定されていない

**解決策**:
1. トークンを再生成
2. GitHub Secretsを更新
3. ワークフローを再実行

### エラー: "The RAILWAY_TOKEN environment variable is set but may be invalid or expired"

**原因**:
- トークンが期限切れ
- トークンが削除された
- トークンに必要な権限がない

**解決策**:
1. Railway Dashboard でトークンの状態を確認
2. 必要に応じて再生成
3. プロジェクトへのアクセス権限を確認

