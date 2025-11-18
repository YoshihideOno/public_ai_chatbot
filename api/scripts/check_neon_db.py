"""
Neonデータベース接続確認スクリプト

Neonデータベースに接続し、テーブルの存在を確認します。
"""

import os
import sys
from sqlalchemy import create_engine, inspect, text

def check_neon_database(database_url: str):
    """
    Neonデータベースの状態を確認
    
    引数:
        database_url: データベース接続URL
    """
    # asyncpg URLをpsycopg2 URLに変換
    if "postgresql+asyncpg://" in database_url:
        database_url = database_url.replace("postgresql+asyncpg://", "postgresql://")
    
    try:
        engine = create_engine(database_url)
        inspector = inspect(engine)
        
        with engine.connect() as conn:
            # データベース名を取得
            db_name_result = conn.execute(text("SELECT current_database()"))
            db_name = db_name_result.scalar()
            
            # スキーマ一覧を取得
            schema_result = conn.execute(text("""
                SELECT schema_name 
                FROM information_schema.schemata 
                WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
                ORDER BY schema_name
            """))
            schemas = [row[0] for row in schema_result]
            
            print(f"📊 データベース: {db_name}")
            print(f"📋 スキーマ一覧: {', '.join(schemas) if schemas else '(なし)'}\n")
            
            # 各スキーマのテーブルを確認
            for schema in schemas:
                # スキーマを設定
                conn.execute(text(f"SET search_path TO {schema}"))
                
                # テーブル一覧を取得
                tables = inspector.get_table_names(schema=schema)
                
                if tables:
                    print(f"📋 スキーマ '{schema}' のテーブル ({len(tables)}個):")
                    for table in sorted(tables):
                        # テーブルのカラム数を取得
                        columns = inspector.get_columns(table, schema=schema)
                        print(f"   - {table} ({len(columns)}カラム)")
                    print()
                else:
                    print(f"📋 スキーマ '{schema}' にはテーブルがありません。\n")
            
            # デフォルトスキーマ（public）に戻す
            conn.execute(text("SET search_path TO public"))
            
            # 全テーブル数
            all_tables = inspector.get_table_names()
            print(f"✅ 合計テーブル数: {len(all_tables)}")
            
            if not all_tables:
                print("\n⚠️  テーブルが存在しません。")
                print("   以下の可能性があります:")
                print("   1. マイグレーションが実行されていない")
                print("   2. 別のデータベースに接続している")
                print("   3. 別のスキーマにテーブルが作成されている")
                print("\n💡 確認方法:")
                print("   - GitHub Actionsのワークフローでrun_migrationがtrueになっているか確認")
                print("   - 正しいデータベースURLを使用しているか確認")
                print("   - スキーマ一覧を確認（上記の出力を参照）")
            
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    """
    メイン処理
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Neonデータベースの状態を確認')
    parser.add_argument(
        '--database-url',
        type=str,
        default=os.getenv('DATABASE_URL'),
        help='データベース接続URL（環境変数DATABASE_URLがデフォルト）'
    )
    
    args = parser.parse_args()
    
    if not args.database_url:
        print("❌ エラー: DATABASE_URLが指定されていません。")
        print("   環境変数DATABASE_URLを設定するか、--database-urlオプションを使用してください。")
        sys.exit(1)
    
    # URLの一部をマスク（セキュリティのため）
    masked_url = args.database_url
    if '@' in masked_url:
        parts = masked_url.split('@')
        if '://' in parts[0]:
            protocol_part = parts[0].split('://')
            if ':' in protocol_part[1]:
                user_pass = protocol_part[1].split(':')
                masked_url = f"{protocol_part[0]}://{user_pass[0]}:****@{parts[1]}"
    
    print(f"🔍 データベースに接続中: {masked_url}\n")
    check_neon_database(args.database_url)


if __name__ == '__main__':
    main()

