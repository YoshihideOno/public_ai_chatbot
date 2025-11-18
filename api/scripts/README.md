# データベーススキーマ比較ツール

モデル定義と実際のデータベーススキーマを比較し、不一致を検出するツールです。

## ツール一覧

### 1. `compare_schema.py` - スキーマ比較ツール

モデル定義と実際のデータベーススキーマを比較します。

#### 使用方法

```bash
# 環境変数DATABASE_URLを使用
cd api
python scripts/compare_schema.py

# データベースURLを直接指定
python scripts/compare_schema.py --database-url "postgresql://user:pass@host:5432/dbname"

# スキーマをJSONファイルに出力
python scripts/compare_schema.py --output-model model_schema.json --output-db db_schema.json
```

#### 出力例

```
❌ スキーマの不一致を検出しました:

❌ テーブル 'tenants' に存在しないカラム:
   - knowledge_registered_at (TIMESTAMP WITH TIME ZONE, nullable=True)
```

### 2. `check_migration_coverage.py` - マイグレーションカバレッジチェック

モデル定義とAlembicマイグレーションファイルを比較し、マイグレーションで追加されていないカラムを検出します。

#### 使用方法

```bash
cd api
python scripts/check_migration_coverage.py
```

**注意**: このスクリプトは簡易的な解析のため、一部のテーブルで誤検出の可能性があります。特に、初期マイグレーションで作成されたテーブルのカラムは正しく検出されない場合があります。

### 3. `check_neon_db.py` - Neonデータベース確認

Neonデータベースに接続し、テーブルの存在を確認します。

#### 使用方法

```bash
cd api
python scripts/check_neon_db.py --database-url "your_neon_database_url"
```

#### 出力例

```
📊 データベース: your_database_name
📋 スキーマ一覧: public

📋 スキーマ 'public' のテーブル (5個):
   - tenants (10カラム)
   - users (12カラム)
   ...
```

### 4. まとめ：推奨される確認手順

1. **マイグレーションカバレッジをチェック**
   ```bash
   cd api
   python scripts/check_migration_coverage.py
   ```

2. **ローカルデータベースとモデル定義を比較**
   ```bash
   python scripts/compare_schema.py --database-url "postgresql://postgres:postgres@localhost:5432/your_db"
   ```

3. **Neonデータベースの状態を確認**（Neonを使用している場合）
   ```bash
   python scripts/check_neon_db.py --database-url "your_neon_database_url"
   ```

4. **問題が見つかった場合の出力例**

マイグレーションカバレッジチェック:
```
❌ マイグレーションカバレッジの問題を検出しました:

📋 テーブル: tenants
   モデルに存在するがマイグレーションに存在しないカラム:
     - knowledge_registered_at
```

## 環境別のデータベース確認方法

### GitHub Actions テスト環境

GitHub Actionsのテスト環境では、以下のPostgreSQLサービスが起動します：

- **イメージ**: `pgvector/pgvector:pg17`
- **データベース名**: `test_db`
- **接続情報**: `postgresql://postgres:postgres@localhost:5432/test_db`

このデータベースは**GitHub Actionsの実行中のみ**存在し、実行終了後に削除されます。

### Neon データベース

Neonのデータベースは、デプロイ時に使用される本番/デモ環境のデータベースです。

**重要**: GitHub Actionsのテスト環境とNeonのデータベースは**別物**です。

- **GitHub Actions**: `pgvector/pgvector:pg17`イメージを使用した一時的なPostgreSQLサービス（テスト実行中のみ存在）
- **Neon**: 永続的なクラウドデータベース（デプロイ時に使用）

#### NeonのSQL Editorで`\d`を実行してもテーブルが表示されない場合

1. **マイグレーションが実行されていない可能性**
   - `.github/workflows/deploy.yml`の`run_migration`が`false`の場合、マイグレーションは実行されません
   - 手動でマイグレーションを実行する必要があります
   ```bash
   cd api
   DATABASE_URL="your_neon_database_url" alembic upgrade head
   ```

2. **別のデータベースを見ている可能性**
   - Neonのプロジェクトには複数のデータベースが存在する可能性があります
   - 正しいデータベースに接続しているか確認してください
   - `check_neon_db.py`スクリプトを使用して確認できます

3. **スキーマの問題**
   - PostgreSQLでは、デフォルトスキーマ（`public`）以外のスキーマにテーブルが作成されている可能性があります
   - `\dn`でスキーマ一覧を確認し、`SET search_path TO public;`でスキーマを設定してください

4. **GitHub Actions内で処理している可能性**
   - GitHub Actionsのテスト環境では、`localhost:5432`のPostgreSQLサービスを使用しています
   - これはNeonとは**完全に別のデータベース**です
   - Neonのデータベースは、デプロイステップ（`deploy-step1`など）でマイグレーションが実行されます

#### Neonデータベースの状態確認

```bash
# Neonデータベースの状態を確認
cd api
python scripts/check_neon_db.py --database-url "your_neon_database_url"
```

このスクリプトは以下を確認します：
- データベース名
- スキーマ一覧
- 各スキーマのテーブル一覧
- テーブルが存在しない場合の原因の可能性

### ローカル環境

Docker Composeを使用している場合：

```bash
# データベースに接続
docker compose exec postgres psql -U postgres -d your_database_name

# テーブル一覧を確認
\dt

# 特定のテーブルの構造を確認
\d tenants
```

## トラブルシューティング

### 1. モデルとマイグレーションの不一致を修正

```bash
# 1. マイグレーションカバレッジをチェック
cd api
python scripts/check_migration_coverage.py

# 2. 不足しているカラムを追加するマイグレーションを作成
alembic revision --autogenerate -m "add_missing_columns"

# 3. 生成されたマイグレーションファイルを確認・修正
# api/alembic/versions/ 内の最新ファイルを確認

# 4. マイグレーションを適用（ローカル環境）
alembic upgrade head
```

### 2. データベーススキーマを確認

```bash
# モデル定義とデータベースを比較
cd api
python scripts/compare_schema.py --database-url "your_database_url"
```

### 3. Alembicの状態を確認

```bash
cd api
# 現在のマイグレーション状態を確認
alembic current

# マイグレーション履歴を確認
alembic history

# モデル定義とマイグレーションの不一致をチェック
alembic check
```

## 注意事項

- `compare_schema.py`は実際のデータベースに接続するため、適切な権限が必要です
- 本番環境のデータベースに対して実行する場合は、読み取り専用の接続を使用してください
- マイグレーションファイルの解析は簡易的な実装のため、複雑なマイグレーションでは誤検出の可能性があります

