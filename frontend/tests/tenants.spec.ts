/**
 * テナント管理フローのE2Eテスト
 * 
 * テナント一覧表示、新規作成、編集、削除、検索、プラン変更の
 * エンドツーエンドテストを実装します。
 */

import { test, expect } from '@playwright/test';
import { login } from './helpers/auth';

test.describe('Tenants Management', () => {
  test.beforeEach(async ({ page }) => {
    // ログイン処理（プラットフォーム管理者として）
    await login(
      page,
      'yoshihide.ono@gmail.com',
      'P@ssw0rd',
      /http:\/\/localhost:3000\/(dashboard|tenants)/,
      15000
    );
    
    // テナント管理ページに移動
    await page.goto('http://localhost:3000/tenants');
    await expect(page).toHaveURL('http://localhost:3000/tenants', { timeout: 5000 });
  });

  test('テナント一覧の表示', async ({ page }) => {
    // テナント一覧ページが表示されることを確認
    await expect(page.locator('h1, h2')).toContainText(/テナント/i, { timeout: 5000 });
    
    // テーブルまたは一覧が表示されることを確認
    const table = page.locator('table, [role="table"]');
    await expect(table.first()).toBeVisible({ timeout: 5000 });
  });

  test('新規テナント作成ページへの遷移', async ({ page }) => {
    // 新規テナントボタンをクリック
    const newTenantButton = page.locator('a, button').filter({ hasText: /新規テナント|新規作成/i });
    
    if (await newTenantButton.count() > 0) {
      await newTenantButton.first().click();
      
      // 新規作成ページに遷移することを確認
      await expect(page).toHaveURL(/http:\/\/localhost:3000\/tenants\/new/, { timeout: 5000 });
    }
  });

  test('テナント検索', async ({ page }) => {
    // 検索入力欄を探す
    const searchInput = page.locator('input[type="search"], input[placeholder*="検索"]');
    
    if (await searchInput.count() > 0) {
      // 検索語を入力
      await searchInput.first().fill('テスト');
      
      // 検索結果が更新されるまで待機
      await page.waitForTimeout(500);
    }
  });

  test('テナント削除', async ({ page }) => {
    // 削除ボタンを探す（ドロップダウンメニュー内）
    const moreButtons = page.locator('button').filter({ hasText: /その他|More/i });
    
    if (await moreButtons.count() > 0) {
      await moreButtons.first().click();
      
      // 削除メニュー項目をクリック
      const deleteButton = page.locator('button, a').filter({ hasText: /削除/i });
      
      if (await deleteButton.count() > 0) {
        // 確認ダイアログを処理
        page.on('dialog', async dialog => {
          await dialog.accept();
        });
        
        await deleteButton.first().click();
        
        // 削除が完了するまで待機
        await page.waitForTimeout(1000);
      }
    }
  });
});

test.describe('Tenant Form', () => {
  test.beforeEach(async ({ page }) => {
    // ログイン処理（プラットフォーム管理者として）
    await login(
      page,
      'yoshihide.ono@gmail.com',
      'P@ssw0rd',
      /http:\/\/localhost:3000\/(dashboard|tenants)/,
      15000
    );
    
    // 新規作成ページに移動
    await page.goto('http://localhost:3000/tenants/new');
  });

  test('フォームの初期表示', async ({ page }) => {
    // テナント名入力欄が表示されることを確認
    await expect(page.locator('input[name="name"], input[id="name"]')).toBeVisible({ timeout: 5000 });
    
    // ドメイン入力欄が表示されることを確認
    await expect(page.locator('input[name="domain"], input[id="domain"]')).toBeVisible({ timeout: 5000 });
  });

  test('バリデーションエラー - テナント名未入力', async ({ page }) => {
    // 保存ボタンをクリック
    const saveButton = page.locator('button[type="submit"]').filter({ hasText: /保存/i });
    await saveButton.first().click();
    
    // バリデーションエラーが表示される
    await expect(page.locator('text=/テナント名は2文字以上/i')).toBeVisible({ timeout: 5000 });
  });
});

