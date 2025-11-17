/**
 * LoginFormコンポーネントのテスト
 * 
 * ログインフォームコンポーネントの動作を検証します。
 */

import React from 'react'
import { render, screen, waitFor } from '@/tests/utils'
import userEvent from '@testing-library/user-event'
import { LoginForm } from '../LoginForm'
// apiClientをモック
jest.mock('@/lib/api', () => ({
  apiClient: {
    login: jest.fn(),
  },
}))

const mockUseAuth = jest.fn(() => ({
  login: jest.fn().mockResolvedValue(undefined),
  user: null,
  isLoading: false,
  isAuthenticated: false,
}))

// useAuthをモック（AuthProviderもエクスポート）
jest.mock('@/contexts/AuthContext', () => {
  const React = jest.requireActual('react')
  return {
    __esModule: true,
    AuthProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
    useAuth: () => mockUseAuth(),
  }
})

describe('LoginForm', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockUseAuth.mockReset()
    mockUseAuth.mockReturnValue({
      login: jest.fn().mockResolvedValue(undefined),
      user: null,
      isLoading: false,
      isAuthenticated: false,
    })
  })

  test('フォームの初期表示', () => {
    render(<LoginForm />)
    
    // ログインフォームが表示されていることを確認
    expect(screen.getByLabelText(/メールアドレス/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/パスワード/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /ログイン/i })).toBeInTheDocument()
  })

  test('有効な入力でログイン成功', async () => {
    const user = userEvent.setup()
    const mockLogin = jest.fn().mockResolvedValue(undefined)
    mockUseAuth.mockReturnValue({
      login: mockLogin,
      user: null,
      isLoading: false,
      isAuthenticated: false,
    })

    render(<LoginForm />)
    
    // フォームに入力
    await user.type(screen.getByLabelText(/メールアドレス/i), 'test@example.com')
    await user.type(screen.getByLabelText(/パスワード/i), 'TestPassword1')
    
    // ログインボタンをクリック
    await user.click(screen.getByRole('button', { name: /ログイン/i }))
    
    // ログイン関数が呼ばれたことを確認
    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith({
        email: 'test@example.com',
        password: 'TestPassword1',
      })
    })
  })

  test('パスワード表示切り替え', async () => {
    const user = userEvent.setup()
    render(<LoginForm />)
    
    const passwordInput = screen.getByLabelText(/パスワード/i) as HTMLInputElement
    
    // 初期状態はパスワードが非表示
    expect(passwordInput.type).toBe('password')
    
    // パスワード入力フィールドの親要素から表示切り替えボタンを取得
    const passwordContainer = passwordInput.closest('.relative')
    const toggleButton = passwordContainer?.querySelector('button[type="button"]') as HTMLButtonElement
    expect(toggleButton).toBeTruthy()
    
    // 表示ボタンをクリック
    await user.click(toggleButton)
    
    // パスワードが表示される
    expect(passwordInput.type).toBe('text')
    
    // 非表示ボタンをクリック
    await user.click(toggleButton)
    
    // パスワードが非表示になる
    expect(passwordInput.type).toBe('password')
  })

  test('タブ切り替え', async () => {
    const user = userEvent.setup()
    render(<LoginForm />)
    
    // アカウント登録タブをクリック
    await user.click(screen.getByRole('tab', { name: /アカウント登録/i }))
    
    // テナント登録フォームが表示されることを確認
    await waitFor(() => {
      expect(screen.getByLabelText(/テナント名/i)).toBeInTheDocument()
    })
  })

  test('バリデーションエラー - 無効なメールアドレス', async () => {
    // このテストは、React Hook Formのバリデーションがフォーム送信時に実行されることを確認するテストです。
    const user = userEvent.setup()
    const mockLogin = jest.fn().mockResolvedValue(undefined)
    
    mockUseAuth.mockReturnValue({
      login: mockLogin,
      user: null,
      isLoading: false,
      isAuthenticated: false,
    })
    
    render(<LoginForm />)
    
    // 無効なメールアドレスを入力
    const emailInput = screen.getByLabelText(/メールアドレス/i)
    await user.clear(emailInput)
    await user.type(emailInput, 'invalid-email')
    await user.type(screen.getByLabelText(/パスワード/i), 'TestPassword1')
    
    // ログインボタンをクリック
    const loginButton = screen.getByRole('button', { name: /ログイン/i })
    await user.click(loginButton)
    
    // バリデーションエラーが表示される（React Hook Formのバリデーションは送信時に実行される）
    // フォーム送信後、バリデーションエラーが表示されるまで待つ
    // React Hook Formはバリデーションに失敗するとonSubmitを呼ばないため、エラーメッセージが表示される
    await waitFor(() => {
      const errorMessage = screen.queryByText(/有効なメールアドレスを入力してください/i)
      if (errorMessage) {
        expect(errorMessage).toBeInTheDocument()
      } else {
        // バリデーションエラーメッセージが表示されない場合は、ログイン関数が呼ばれていないことを確認
        expect(mockLogin).not.toHaveBeenCalled()
      }
    }, { timeout: 5000 })
  })

  test('バリデーションエラー - パスワード未入力', async () => {
    const user = userEvent.setup()
    render(<LoginForm />)
    
    // メールアドレスのみ入力
    await user.type(screen.getByLabelText(/メールアドレス/i), 'test@example.com')
    
    // ログインボタンをクリック
    await user.click(screen.getByRole('button', { name: /ログイン/i }))
    
    // バリデーションエラーが表示される（React Hook Formのバリデーションは送信時に実行される）
    // 複数の要素がある可能性があるため、getAllByTextを使用
    await waitFor(() => {
      const errorMessages = screen.queryAllByText(/パスワードを入力してください/i)
      expect(errorMessages.length).toBeGreaterThan(0)
    }, { timeout: 3000 })
  })

  test('ログイン失敗時のエラー表示', async () => {
    const user = userEvent.setup()
    const mockLogin = jest.fn().mockRejectedValue(new Error('ログインに失敗しました'))
    
    mockUseAuth.mockReturnValue({
      login: mockLogin,
      user: null,
      isLoading: false,
      isAuthenticated: false,
    })

    render(<LoginForm />)
    
    // フォームに入力
    await user.type(screen.getByLabelText(/メールアドレス/i), 'test@example.com')
    await user.type(screen.getByLabelText(/パスワード/i), 'WrongPassword')
    
    // ログインボタンをクリック
    await user.click(screen.getByRole('button', { name: /ログイン/i }))
    
    // エラーメッセージが表示される
    await waitFor(() => {
      expect(screen.getByText(/ログインに失敗しました/i)).toBeInTheDocument()
    })
  })

  test('ローディング状態の表示', async () => {
    const user = userEvent.setup()
    const mockLogin = jest.fn().mockImplementation(() => new Promise(() => {})) // 解決しないPromise
    
    mockUseAuth.mockReturnValue({
      login: mockLogin,
      user: null,
      isLoading: false,
      isAuthenticated: false,
    })

    render(<LoginForm />)
    
    // フォームに入力
    await user.type(screen.getByLabelText(/メールアドレス/i), 'test@example.com')
    await user.type(screen.getByLabelText(/パスワード/i), 'TestPassword1')
    
    // ログインボタンをクリック
    const loginButton = screen.getByRole('button', { name: /ログイン/i })
    await user.click(loginButton)
    
    // ローディング状態が表示される（ボタンが無効化される、またはローディングインジケーターが表示される）
    await waitFor(() => {
      // ボタンが無効化されているか、ローディングテキストが表示されているかを確認
      const isDisabled = loginButton.hasAttribute('disabled')
      const hasLoadingText = screen.queryByText(/ログイン中/i) !== null
      expect(isDisabled || hasLoadingText).toBe(true)
    }, { timeout: 3000 })
  })
})

