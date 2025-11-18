"""
マイグレーションカバレッジチェックスクリプト

モデル定義とAlembicマイグレーションファイルを比較し、
モデルに存在するがマイグレーションで追加されていないカラムを検出します。
"""

import os
import sys
import re
from pathlib import Path
from sqlalchemy import create_engine, inspect
from sqlalchemy.schema import CreateTable

# プロジェクトルートをパスに追加
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(BASE_DIR)
sys.path.append(os.path.join(BASE_DIR, 'app'))

from app.core.database import Base
from app import models  # noqa: F401


def get_model_columns():
    """
    モデル定義から全テーブルのカラム情報を取得
    
    戻り値:
        dict: テーブル名をキー、カラム名のセットを値とする辞書
    """
    model_columns = {}
    
    for table_name, table in Base.metadata.tables.items():
        columns = {col.name for col in table.columns}
        model_columns[table_name] = columns
    
    return model_columns


def parse_migration_files():
    """
    Alembicマイグレーションファイルを解析して、各テーブルのカラム追加履歴を取得
    
    戻り値:
        dict: テーブル名をキー、マイグレーションで追加されたカラム名のセットを値とする辞書
    """
    versions_dir = Path(BASE_DIR) / 'alembic' / 'versions'
    migration_columns = {}
    
    # マイグレーションファイルをリビジョン順にソート
    migration_files = sorted(versions_dir.glob('*.py'), key=lambda p: p.stat().st_mtime)
    
    for migration_file in migration_files:
        if migration_file.name == '__init__.py':
            continue
        
        try:
            content = migration_file.read_text(encoding='utf-8')
            
            # create_table を検出
            create_table_pattern = r"op\.create_table\(['\"]([^'\"]+)['\"]"
            for match in re.finditer(create_table_pattern, content):
                table_name = match.group(1)
                if table_name not in migration_columns:
                    migration_columns[table_name] = set()
                
                # そのテーブルのカラム定義を抽出
                start_pos = match.end()
                # 次のcreate_tableまたは関数の終わりまでを取得
                end_match = re.search(r'(?:op\.create_table|def downgrade|#)', content[start_pos:])
                if end_match:
                    table_def = content[start_pos:start_pos + end_match.start()]
                else:
                    table_def = content[start_pos:]
                
                # sa.Column を検出
                column_pattern = r"sa\.Column\(['\"]([^'\"]+)['\"]"
                for col_match in re.finditer(column_pattern, table_def):
                    col_name = col_match.group(1)
                    migration_columns[table_name].add(col_name)
            
            # add_column を検出
            add_column_pattern = r"op\.add_column\(['\"]([^'\"]+)['\"],\s*sa\.Column\(['\"]([^'\"]+)['\"]"
            for match in re.finditer(add_column_pattern, content):
                table_name = match.group(1)
                col_name = match.group(2)
                if table_name not in migration_columns:
                    migration_columns[table_name] = set()
                migration_columns[table_name].add(col_name)
            
        except Exception as e:
            print(f"⚠️  警告: {migration_file.name} の解析中にエラー: {e}", file=sys.stderr)
    
    return migration_columns


def check_migration_coverage():
    """
    マイグレーションカバレッジをチェック
    
    戻り値:
        list: 不一致のリスト
    """
    model_columns = get_model_columns()
    migration_columns = parse_migration_files()
    
    issues = []
    
    for table_name, model_cols in model_columns.items():
        mig_cols = migration_columns.get(table_name, set())
        
        # モデルに存在するがマイグレーションに存在しないカラム
        missing_in_migration = model_cols - mig_cols
        
        if missing_in_migration:
            issues.append({
                'table': table_name,
                'missing_columns': sorted(missing_in_migration),
                'model_columns': sorted(model_cols),
                'migration_columns': sorted(mig_cols)
            })
    
    return issues


def print_issues(issues: list):
    """
    問題を整形して出力
    
    引数:
        issues: 問題のリスト
    """
    if not issues:
        print("✅ すべてのモデルカラムがマイグレーションファイルに含まれています。")
        return
    
    print("❌ マイグレーションカバレッジの問題を検出しました:\n")
    
    for issue in issues:
        print(f"📋 テーブル: {issue['table']}")
        print(f"   モデルに存在するがマイグレーションに存在しないカラム:")
        for col in issue['missing_columns']:
            print(f"     - {col}")
        print()


def main():
    """
    メイン処理
    """
    print("🔍 マイグレーションカバレッジをチェック中...\n")
    
    issues = check_migration_coverage()
    print_issues(issues)
    
    if issues:
        print("\n💡 解決方法:")
        print("   1. 不足しているカラムを追加するマイグレーションファイルを作成してください。")
        print("   2. 以下のコマンドでマイグレーションファイルを生成:")
        print("      cd api")
        print("      alembic revision --autogenerate -m 'add_missing_columns'")
        print("   3. 生成されたマイグレーションファイルを確認・修正してください。")
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()

