/**
 * TenantRegistrationFormコンポーネントのテスト
 * 
 * テナント登録フォームコンポーネントの動作を検証します。
 */

import React from 'react'
import { render, screen, waitFor } from '@/tests/utils'
import userEvent from '@testing-library/user-event'
import { TenantRegistrationForm } from '../TenantRegistrationForm'
import { apiClient } from '@/lib/api'

// apiClientをモック
jest.mock('@/lib/api', () => ({
  apiClient: {
    registerTenant: jest.fn(),
  },
}))

describe('TenantRegistrationForm', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    // window.confirmをモック
    window.confirm = jest.fn().mockReturnValue(true)
  })

  test('フォームの初期表示', () => {
    render(<TenantRegistrationForm />)
    
    // フォームフィールドが表示されていることを確認
    expect(screen.getByLabelText(/テナント名/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/テナント識別子/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/メールアドレス/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/ユーザー名/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/^パスワード$/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/パスワード確認/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /アカウントを登録/i })).toBeInTheDocument()
  })

  test('有効な入力で登録成功', async () => {
    const user = userEvent.setup()
    const mockRegisterTenant = jest.fn().mockResolvedValue({
      tenant_id: 'test-tenant-id',
      tenant_name: 'Test Tenant',
      admin_user_id: 'test-user-id',
      admin_email: 'admin@example.com',
      message: '登録が完了しました',
    })

    ;(apiClient.registerTenant as jest.Mock) = mockRegisterTenant

    render(<TenantRegistrationForm />)
    
    // フォームに入力
    await user.type(screen.getByLabelText(/テナント名/i), 'Test Tenant')
    await user.type(screen.getByLabelText(/テナント識別子/i), 'test-tenant')
    await user.type(screen.getByLabelText(/メールアドレス/i), 'admin@example.com')
    await user.type(screen.getByLabelText(/ユーザー名/i), 'adminuser')
    await user.type(screen.getByLabelText(/^パスワード$/i), 'AdminPassword1')
    await user.type(screen.getByLabelText(/パスワード確認/i), 'AdminPassword1')
    
    // 登録ボタンをクリック
    await user.click(screen.getByRole('button', { name: /登録/i }))
    
    // 登録関数が呼ばれたことを確認
    await waitFor(() => {
      expect(mockRegisterTenant).toHaveBeenCalledWith({
        tenant_name: 'Test Tenant',
        tenant_domain: 'test-tenant',
        admin_email: 'admin@example.com',
        admin_username: 'adminuser',
        admin_password: 'AdminPassword1',
      })
    })
  })

  test('パスワード確認の一致チェック', async () => {
    const user = userEvent.setup()
    render(<TenantRegistrationForm />)
    
    // パスワードとパスワード確認を異なる値で入力
    await user.type(screen.getByLabelText(/^パスワード$/i), 'AdminPassword1')
    await user.type(screen.getByLabelText(/パスワード確認/i), 'DifferentPassword1')
    
    // 登録ボタンをクリック
    await user.click(screen.getByRole('button', { name: /登録/i }))
    
    // バリデーションエラーが表示される
    await waitFor(() => {
      expect(screen.getByText(/パスワードが一致しません/i)).toBeInTheDocument()
    })
  })

  test('バリデーションエラー - テナント名が短すぎる', async () => {
    const user = userEvent.setup()
    render(<TenantRegistrationForm />)
    
    // テナント名を1文字で入力
    await user.type(screen.getByLabelText(/テナント名/i), 'A')
    
    // 登録ボタンをクリック
    await user.click(screen.getByRole('button', { name: /登録/i }))
    
    // バリデーションエラーが表示される
    await waitFor(() => {
      expect(screen.getByText(/テナント名は2文字以上で入力してください/i)).toBeInTheDocument()
    })
  })

  test('バリデーションエラー - テナント識別子に無効な文字', async () => {
    const user = userEvent.setup()
    render(<TenantRegistrationForm />)
    
    // テナント識別子にスペースを含む
    await user.type(screen.getByLabelText(/テナント識別子/i), 'test tenant')
    
    // 登録ボタンをクリック
    await user.click(screen.getByRole('button', { name: /登録/i }))
    
    // バリデーションエラーが表示される
    await waitFor(() => {
      expect(screen.getByText(/テナント識別子は英数字、ハイフン、アンダースコアのみ使用可能です/i)).toBeInTheDocument()
    })
  })

  test('バリデーションエラー - パスワード強度不足', async () => {
    const user = userEvent.setup()
    render(<TenantRegistrationForm />)
    
    // 弱いパスワードを入力（大文字がない）
    await user.type(screen.getByLabelText(/^パスワード$/i), 'weakpassword1')
    await user.type(screen.getByLabelText(/パスワード確認/i), 'weakpassword1')
    
    // 登録ボタンをクリック
    await user.click(screen.getByRole('button', { name: /登録/i }))
    
    // バリデーションエラーが表示される
    await waitFor(() => {
      expect(screen.getByText(/パスワードには大文字、小文字、数字を含める必要があります/i)).toBeInTheDocument()
    })
  })

  test('境界値テスト - 最小長', async () => {
    const user = userEvent.setup()
    render(<TenantRegistrationForm />)
    
    // 最小長の値を入力
    await user.type(screen.getByLabelText(/テナント名/i), 'AB') // 2文字
    await user.type(screen.getByLabelText(/テナント識別子/i), 'abc') // 3文字
    await user.type(screen.getByLabelText(/ユーザー名/i), 'abc') // 3文字
    await user.type(screen.getByLabelText(/^パスワード$/i), 'AdminPass1') // 10文字
    await user.type(screen.getByLabelText(/パスワード確認/i), 'AdminPass1')
    
    // 登録ボタンをクリック
    await user.click(screen.getByRole('button', { name: /登録/i }))
    
    // バリデーションエラーが表示されないことを確認（最小長は有効）
    await waitFor(() => {
      expect(screen.queryByText(/テナント名は2文字以上で入力してください/i)).not.toBeInTheDocument()
      expect(screen.queryByText(/テナント識別子は3文字以上で入力してください/i)).not.toBeInTheDocument()
      expect(screen.queryByText(/ユーザー名は3文字以上で入力してください/i)).not.toBeInTheDocument()
    })
  })

  test('ローディング状態の表示', async () => {
    const user = userEvent.setup()
    const mockRegisterTenant = jest.fn().mockImplementation(() => new Promise(() => {})) // 解決しないPromise
    
    ;(apiClient.registerTenant as jest.Mock) = mockRegisterTenant

    render(<TenantRegistrationForm />)
    
    // フォームに入力
    await user.type(screen.getByLabelText(/テナント名/i), 'Test Tenant')
    await user.type(screen.getByLabelText(/テナント識別子/i), 'test-tenant')
    await user.type(screen.getByLabelText(/メールアドレス/i), 'admin@example.com')
    await user.type(screen.getByLabelText(/ユーザー名/i), 'adminuser')
    await user.type(screen.getByLabelText(/^パスワード$/i), 'AdminPassword1')
    await user.type(screen.getByLabelText(/パスワード確認/i), 'AdminPassword1')
    
    // 登録ボタンをクリック
    const registerButton = screen.getByRole('button', { name: /アカウントを登録/i })
    await user.click(registerButton)
    
    // ローディング状態が表示される（ボタンが無効化される、またはローディングインジケーターが表示される）
    await waitFor(() => {
      // ボタンが無効化されているか、ローディングテキストが表示されているかを確認
      const isDisabled = registerButton.hasAttribute('disabled')
      const hasLoadingText = screen.queryByText(/登録中/i) !== null
      expect(isDisabled || hasLoadingText).toBe(true)
    }, { timeout: 3000 })
  })
})

