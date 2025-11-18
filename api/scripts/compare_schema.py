"""
データベーススキーマ比較スクリプト

モデル定義と実際のデータベーススキーマを比較し、
不一致を検出します。
"""

import os
import sys
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.schema import CreateTable
from sqlalchemy.dialects import postgresql

# プロジェクトルートをパスに追加
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(BASE_DIR)
sys.path.append(os.path.join(BASE_DIR, 'app'))

from app.core.database import Base
from app import models  # noqa: F401


def get_model_schema():
    """
    モデル定義からスキーマを取得
    
    戻り値:
        dict: テーブル名をキー、カラム情報のリストを値とする辞書
    """
    schema = {}
    
    for table_name, table in Base.metadata.tables.items():
        columns = []
        for column in table.columns:
            col_info = {
                'name': column.name,
                'type': str(column.type),
                'nullable': column.nullable,
                'default': str(column.default) if column.default else None,
                'primary_key': column.primary_key,
                'unique': column.unique,
                'foreign_keys': [str(fk) for fk in column.foreign_keys]
            }
            columns.append(col_info)
        schema[table_name] = columns
    
    return schema


def get_database_schema(database_url: str):
    """
    実際のデータベースからスキーマを取得
    
    引数:
        database_url: データベース接続URL
    
    戻り値:
        dict: テーブル名をキー、カラム情報のリストを値とする辞書
    """
    # asyncpg URLをpsycopg2 URLに変換
    if "postgresql+asyncpg://" in database_url:
        database_url = database_url.replace("postgresql+asyncpg://", "postgresql://")
    
    engine = create_engine(database_url)
    inspector = inspect(engine)
    
    schema = {}
    
    with engine.connect() as conn:
        # テーブル一覧を取得
        table_names = inspector.get_table_names()
        
        for table_name in table_names:
            columns = []
            for column in inspector.get_columns(table_name):
                col_info = {
                    'name': column['name'],
                    'type': str(column['type']),
                    'nullable': column['nullable'],
                    'default': str(column['default']) if column.get('default') else None,
                    'primary_key': False,  # 後で設定
                    'unique': False,  # 後で設定
                    'foreign_keys': []
                }
                columns.append(col_info)
            
            # 主キー情報を取得
            pk_constraint = inspector.get_pk_constraint(table_name)
            if pk_constraint and pk_constraint.get('constrained_columns'):
                for col_name in pk_constraint['constrained_columns']:
                    for col in columns:
                        if col['name'] == col_name:
                            col['primary_key'] = True
            
            # ユニーク制約を取得
            unique_constraints = inspector.get_unique_constraints(table_name)
            for uc in unique_constraints:
                for col_name in uc['column_names']:
                    for col in columns:
                        if col['name'] == col_name:
                            col['unique'] = True
            
            # 外部キー情報を取得
            foreign_keys = inspector.get_foreign_keys(table_name)
            for fk in foreign_keys:
                for col_name in fk['constrained_columns']:
                    for col in columns:
                        if col['name'] == col_name:
                            col['foreign_keys'].append(
                                f"{fk['referred_table']}.{fk['referred_columns'][0]}"
                            )
            
            schema[table_name] = columns
    
    return schema


def compare_schemas(model_schema: dict, db_schema: dict):
    """
    2つのスキーマを比較し、不一致を検出
    
    引数:
        model_schema: モデル定義のスキーマ
        db_schema: データベースのスキーマ
    
    戻り値:
        list: 不一致のリスト
    """
    differences = []
    
    # モデルに存在するがDBに存在しないテーブル
    model_tables = set(model_schema.keys())
    db_tables = set(db_schema.keys())
    
    missing_tables = model_tables - db_tables
    if missing_tables:
        differences.append({
            'type': 'missing_table',
            'tables': list(missing_tables)
        })
    
    # DBに存在するがモデルに存在しないテーブル
    extra_tables = db_tables - model_tables
    if extra_tables:
        differences.append({
            'type': 'extra_table',
            'tables': list(extra_tables)
        })
    
    # 共通テーブルのカラム比較
    common_tables = model_tables & db_tables
    for table_name in common_tables:
        model_cols = {col['name']: col for col in model_schema[table_name]}
        db_cols = {col['name']: col for col in db_schema[table_name]}
        
        # モデルに存在するがDBに存在しないカラム
        missing_cols = set(model_cols.keys()) - set(db_cols.keys())
        if missing_cols:
            differences.append({
                'type': 'missing_column',
                'table': table_name,
                'columns': [
                    {
                        'name': col_name,
                        'model_type': model_cols[col_name]['type'],
                        'model_nullable': model_cols[col_name]['nullable']
                    }
                    for col_name in missing_cols
                ]
            })
        
        # DBに存在するがモデルに存在しないカラム
        extra_cols = set(db_cols.keys()) - set(model_cols.keys())
        if extra_cols:
            differences.append({
                'type': 'extra_column',
                'table': table_name,
                'columns': [
                    {
                        'name': col_name,
                        'db_type': db_cols[col_name]['type'],
                        'db_nullable': db_cols[col_name]['nullable']
                    }
                    for col_name in extra_cols
                ]
            })
        
        # 共通カラムの型やnull制約の比較
        common_cols = set(model_cols.keys()) & set(db_cols.keys())
        for col_name in common_cols:
            model_col = model_cols[col_name]
            db_col = db_cols[col_name]
            
            # 型の比較（簡易版）
            if model_col['type'] != db_col['type']:
                differences.append({
                    'type': 'type_mismatch',
                    'table': table_name,
                    'column': col_name,
                    'model_type': model_col['type'],
                    'db_type': db_col['type']
                })
            
            # null制約の比較
            if model_col['nullable'] != db_col['nullable']:
                differences.append({
                    'type': 'nullable_mismatch',
                    'table': table_name,
                    'column': col_name,
                    'model_nullable': model_col['nullable'],
                    'db_nullable': db_col['nullable']
                })
    
    return differences


def print_differences(differences: list):
    """
    不一致を整形して出力
    
    引数:
        differences: 不一致のリスト
    """
    if not differences:
        print("✅ スキーマに不一致はありません。")
        return
    
    print("❌ スキーマの不一致を検出しました:\n")
    
    for diff in differences:
        if diff['type'] == 'missing_table':
            print(f"⚠️  データベースに存在しないテーブル:")
            for table in diff['tables']:
                print(f"   - {table}")
            print()
        
        elif diff['type'] == 'extra_table':
            print(f"ℹ️  モデルに存在しないテーブル（データベースのみ）:")
            for table in diff['tables']:
                print(f"   - {table}")
            print()
        
        elif diff['type'] == 'missing_column':
            print(f"❌ テーブル '{diff['table']}' に存在しないカラム:")
            for col in diff['columns']:
                print(f"   - {col['name']} ({col['model_type']}, nullable={col['model_nullable']})")
            print()
        
        elif diff['type'] == 'extra_column':
            print(f"ℹ️  テーブル '{diff['table']}' にモデルに存在しないカラム:")
            for col in diff['columns']:
                print(f"   - {col['name']} ({col['db_type']}, nullable={col['db_nullable']})")
            print()
        
        elif diff['type'] == 'type_mismatch':
            print(f"⚠️  テーブル '{diff['table']}' のカラム '{diff['column']}' の型が不一致:")
            print(f"   モデル: {diff['model_type']}")
            print(f"   データベース: {diff['db_type']}")
            print()
        
        elif diff['type'] == 'nullable_mismatch':
            print(f"⚠️  テーブル '{diff['table']}' のカラム '{diff['column']}' のnull制約が不一致:")
            print(f"   モデル: nullable={diff['model_nullable']}")
            print(f"   データベース: nullable={diff['db_nullable']}")
            print()


def main():
    """
    メイン処理
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='データベーススキーマを比較')
    parser.add_argument(
        '--database-url',
        type=str,
        default=os.getenv('DATABASE_URL'),
        help='データベース接続URL（環境変数DATABASE_URLがデフォルト）'
    )
    parser.add_argument(
        '--output-model',
        type=str,
        help='モデルスキーマをJSONファイルに出力'
    )
    parser.add_argument(
        '--output-db',
        type=str,
        help='データベーススキーマをJSONファイルに出力'
    )
    
    args = parser.parse_args()
    
    if not args.database_url:
        print("❌ エラー: DATABASE_URLが指定されていません。")
        print("   環境変数DATABASE_URLを設定するか、--database-urlオプションを使用してください。")
        sys.exit(1)
    
    print("📊 モデル定義からスキーマを取得中...")
    model_schema = get_model_schema()
    print(f"   テーブル数: {len(model_schema)}")
    
    print(f"\n📊 データベース '{args.database_url.split('@')[-1] if '@' in args.database_url else args.database_url}' からスキーマを取得中...")
    try:
        db_schema = get_database_schema(args.database_url)
        print(f"   テーブル数: {len(db_schema)}")
    except Exception as e:
        print(f"❌ エラー: データベースへの接続に失敗しました: {e}")
        sys.exit(1)
    
    print("\n🔍 スキーマを比較中...")
    differences = compare_schemas(model_schema, db_schema)
    
    print_differences(differences)
    
    # JSON出力
    if args.output_model:
        import json
        with open(args.output_model, 'w', encoding='utf-8') as f:
            json.dump(model_schema, f, indent=2, ensure_ascii=False, default=str)
        print(f"✅ モデルスキーマを '{args.output_model}' に出力しました。")
    
    if args.output_db:
        import json
        with open(args.output_db, 'w', encoding='utf-8') as f:
            json.dump(db_schema, f, indent=2, ensure_ascii=False, default=str)
        print(f"✅ データベーススキーマを '{args.output_db}' に出力しました。")
    
    if differences:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()

