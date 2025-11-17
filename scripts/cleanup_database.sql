-- ============================================================================
-- データベースクレンジングSQLスクリプト
-- ============================================================================
-- 
-- 【重要】実行前に必ずデータベースのバックアップを取得してください！
-- 
-- このスクリプトは以下のデータのみを残し、それ以外を削除します：
-- - tenants: name = 'シナジーソフトウェア'
-- - users: 指定された4つのメールアドレスのいずれか
-- - files: 指定された3つのファイル名のいずれか
--
-- 実行方法：
--   1. データベースのバックアップを取得
--   2. BEGIN; でトランザクションを開始（既に含まれています）
--   3. このスクリプトを実行
--   4. 削除結果を確認
--   5. 問題なければ COMMIT; を実行、問題があれば ROLLBACK; を実行
--
-- ============================================================================

BEGIN;

-- ============================================================================
-- 1. 残すデータのIDを一時テーブルに保存
-- ============================================================================

-- 一時テーブルを作成して残すIDを保存
CREATE TEMP TABLE keep_tenants AS
SELECT id
FROM tenants
WHERE name = 'シナジーソフトウェア';

CREATE TEMP TABLE keep_users AS
SELECT id
FROM users
WHERE email IN (
    'yoshihide.ono@gmail.com',
    'yono1961@gmail.com',
    'yono@geothermal.jp',
    'y.ono@synergysoft.jp'
);

CREATE TEMP TABLE keep_files AS
SELECT id
FROM files
WHERE file_name IN (
    'service_info.md',
    'ai_chatbot_manual.md',
    'localhost.txt'
);

CREATE TEMP TABLE keep_billing_info AS
SELECT id
FROM billing_info
WHERE tenant_id IN (SELECT id FROM keep_tenants);

CREATE TEMP TABLE keep_conversations AS
SELECT id
FROM conversations
WHERE tenant_id IN (SELECT id FROM keep_tenants);

-- インデックスを作成してパフォーマンスを向上
CREATE INDEX idx_keep_tenants_id ON keep_tenants(id);
CREATE INDEX idx_keep_users_id ON keep_users(id);
CREATE INDEX idx_keep_files_id ON keep_files(id);
CREATE INDEX idx_keep_billing_info_id ON keep_billing_info(id);
CREATE INDEX idx_keep_conversations_id ON keep_conversations(id);

-- ============================================================================
-- 2. 削除前のレコード数確認（参考用）
-- ============================================================================

-- 削除対象のレコード数を確認（実行前に確認推奨）
-- 以下のクエリを個別に実行して、削除されるレコード数を確認してください

/*
SELECT 'query_clusters' AS table_name, COUNT(*) AS delete_count
FROM query_clusters qc
WHERE NOT EXISTS (SELECT 1 FROM keep_tenants kt WHERE qc.tenant_id = kt.id)
UNION ALL
SELECT 'top_query_aggregates', COUNT(*)
FROM top_query_aggregates tqa
WHERE NOT EXISTS (SELECT 1 FROM keep_tenants kt WHERE tqa.tenant_id = kt.id)
UNION ALL
SELECT 'audit_logs', COUNT(*)
FROM audit_logs al
WHERE NOT EXISTS (SELECT 1 FROM keep_tenants kt WHERE al.tenant_id = kt.id)
   OR (al.user_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM keep_users ku WHERE al.user_id = ku.id))
UNION ALL
SELECT 'usage_logs', COUNT(*)
FROM usage_logs ul
WHERE NOT EXISTS (SELECT 1 FROM keep_tenants kt WHERE ul.tenant_id = kt.id)
UNION ALL
SELECT 'conversations', COUNT(*)
FROM conversations c
WHERE NOT EXISTS (SELECT 1 FROM keep_tenants kt WHERE c.tenant_id = kt.id)
UNION ALL
SELECT 'reminder_logs', COUNT(*)
FROM reminder_logs rl
WHERE NOT EXISTS (SELECT 1 FROM keep_tenants kt WHERE rl.tenant_id = kt.id)
UNION ALL
SELECT 'notifications', COUNT(*)
FROM notifications n
WHERE NOT EXISTS (SELECT 1 FROM keep_tenants kt WHERE n.tenant_id = kt.id)
   OR (n.user_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM keep_users ku WHERE n.user_id = ku.id))
UNION ALL
SELECT 'invoices', COUNT(*)
FROM invoices i
WHERE NOT EXISTS (SELECT 1 FROM keep_billing_info kbi WHERE i.billing_info_id = kbi.id)
UNION ALL
SELECT 'billing_info', COUNT(*)
FROM billing_info bi
WHERE NOT EXISTS (SELECT 1 FROM keep_tenants kt WHERE bi.tenant_id = kt.id)
UNION ALL
SELECT 'chunks', COUNT(*)
FROM chunks ch
WHERE NOT EXISTS (SELECT 1 FROM keep_tenants kt WHERE ch.tenant_id = kt.id)
   OR NOT EXISTS (SELECT 1 FROM keep_files kf WHERE ch.file_id = kf.id)
UNION ALL
SELECT 'api_keys', COUNT(*)
FROM api_keys ak
WHERE NOT EXISTS (SELECT 1 FROM keep_tenants kt WHERE ak.tenant_id = kt.id)
UNION ALL
SELECT 'verification_tokens', COUNT(*)
FROM verification_tokens vt
WHERE NOT EXISTS (SELECT 1 FROM keep_users ku WHERE vt.user_id = ku.id)
UNION ALL
SELECT 'files', COUNT(*)
FROM files f
WHERE NOT EXISTS (SELECT 1 FROM keep_tenants kt WHERE f.tenant_id = kt.id)
   OR f.file_name NOT IN ('service_info.md', 'ai_chatbot_manual.md', 'localhost.txt')
UNION ALL
SELECT 'users', COUNT(*)
FROM users u
WHERE NOT EXISTS (SELECT 1 FROM keep_tenants kt WHERE u.tenant_id = kt.id)
   OR u.email NOT IN ('yoshihide.ono@gmail.com', 'yono1961@gmail.com', 'yono@geothermal.jp', 'y.ono@synergysoft.jp')
UNION ALL
SELECT 'tenants', COUNT(*)
FROM tenants t
WHERE t.name != 'シナジーソフトウェア';
*/

-- ============================================================================
-- 3. 論理的な関連テーブルの削除（外部キー制約なし）
-- ============================================================================

-- top_query_aggregates: query_clustersに依存する可能性があるため先に削除
DELETE FROM top_query_aggregates
WHERE NOT EXISTS (SELECT 1 FROM keep_tenants kt WHERE top_query_aggregates.tenant_id = kt.id);

-- query_clusters
DELETE FROM query_clusters
WHERE NOT EXISTS (SELECT 1 FROM keep_tenants kt WHERE query_clusters.tenant_id = kt.id);

-- usage_logs: conversationsに依存するため先に削除
DELETE FROM usage_logs
WHERE NOT EXISTS (SELECT 1 FROM keep_tenants kt WHERE usage_logs.tenant_id = kt.id);

-- conversations
DELETE FROM conversations
WHERE NOT EXISTS (SELECT 1 FROM keep_tenants kt WHERE conversations.tenant_id = kt.id);

-- audit_logs
DELETE FROM audit_logs
WHERE NOT EXISTS (SELECT 1 FROM keep_tenants kt WHERE audit_logs.tenant_id = kt.id)
   OR (audit_logs.user_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM keep_users ku WHERE audit_logs.user_id = ku.id));

-- invoices: billing_infoに依存するため先に削除
DELETE FROM invoices
WHERE NOT EXISTS (SELECT 1 FROM keep_billing_info kbi WHERE invoices.billing_info_id = kbi.id);

-- billing_info
DELETE FROM billing_info
WHERE NOT EXISTS (SELECT 1 FROM keep_tenants kt WHERE billing_info.tenant_id = kt.id);

-- ============================================================================
-- 4. 物理的な外部キー制約があるテーブルの削除
-- ============================================================================

-- chunks: filesに依存（CASCADE DELETEだが明示的に削除）
DELETE FROM chunks
WHERE NOT EXISTS (SELECT 1 FROM keep_tenants kt WHERE chunks.tenant_id = kt.id)
   OR NOT EXISTS (SELECT 1 FROM keep_files kf WHERE chunks.file_id = kf.id);

-- reminder_logs
DELETE FROM reminder_logs
WHERE NOT EXISTS (SELECT 1 FROM keep_tenants kt WHERE reminder_logs.tenant_id = kt.id);

-- notifications
DELETE FROM notifications
WHERE NOT EXISTS (SELECT 1 FROM keep_tenants kt WHERE notifications.tenant_id = kt.id)
   OR (notifications.user_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM keep_users ku WHERE notifications.user_id = ku.id));

-- api_keys
DELETE FROM api_keys
WHERE NOT EXISTS (SELECT 1 FROM keep_tenants kt WHERE api_keys.tenant_id = kt.id);

-- verification_tokens: usersに依存（CASCADE DELETEだが明示的に削除）
DELETE FROM verification_tokens
WHERE NOT EXISTS (SELECT 1 FROM keep_users ku WHERE verification_tokens.user_id = ku.id);

-- ============================================================================
-- 5. 親テーブルの削除
-- ============================================================================

-- files: chunksは既に削除済み
-- 残すテナントに所属し、かつ指定されたファイル名のいずれかに該当するファイルのみを残す
DELETE FROM files
WHERE NOT EXISTS (SELECT 1 FROM keep_tenants kt WHERE files.tenant_id = kt.id)
   OR file_name NOT IN ('service_info.md', 'ai_chatbot_manual.md', 'localhost.txt');

-- users: verification_tokensは既に削除済み
-- 指定されたメールアドレスのユーザーは残す（テナントに関係なく）
DELETE FROM users
WHERE email NOT IN ('yoshihide.ono@gmail.com', 'yono1961@gmail.com', 'yono@geothermal.jp', 'y.ono@synergysoft.jp');

-- tenants: 最後に削除（他のテーブルは既に削除済み）
DELETE FROM tenants
WHERE name != 'シナジーソフトウェア';

-- ============================================================================
-- 6. 削除後の確認クエリ（参考用）
-- ============================================================================

-- 残っているレコード数を確認
SELECT 'tenants' AS table_name, COUNT(*) AS remaining_count FROM tenants
UNION ALL
SELECT 'users', COUNT(*) FROM users
UNION ALL
SELECT 'files', COUNT(*) FROM files
UNION ALL
SELECT 'chunks', COUNT(*) FROM chunks
UNION ALL
SELECT 'api_keys', COUNT(*) FROM api_keys
UNION ALL
SELECT 'billing_info', COUNT(*) FROM billing_info
UNION ALL
SELECT 'invoices', COUNT(*) FROM invoices
UNION ALL
SELECT 'conversations', COUNT(*) FROM conversations
UNION ALL
SELECT 'usage_logs', COUNT(*) FROM usage_logs
UNION ALL
SELECT 'audit_logs', COUNT(*) FROM audit_logs
UNION ALL
SELECT 'notifications', COUNT(*) FROM notifications
UNION ALL
SELECT 'reminder_logs', COUNT(*) FROM reminder_logs
UNION ALL
SELECT 'verification_tokens', COUNT(*) FROM verification_tokens
UNION ALL
SELECT 'query_clusters', COUNT(*) FROM query_clusters
UNION ALL
SELECT 'top_query_aggregates', COUNT(*) FROM top_query_aggregates;

-- ============================================================================
-- 7. トランザクションの確定
-- ============================================================================

-- 削除結果を確認後、問題がなければ以下のコマンドを実行してください：
-- COMMIT;

-- 問題がある場合は、以下のコマンドでロールバックしてください：
-- ROLLBACK;

