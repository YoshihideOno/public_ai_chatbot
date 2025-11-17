/**
 * TenantFormコンポーネントのテスト
 * 
 * テナント管理フォームコンポーネントの動作を検証します。
 */

import React from 'react'
import { render, screen, waitFor } from '@/tests/utils'
import userEvent from '@testing-library/user-event'
import { TenantForm } from '../TenantForm'
import { apiClient } from '@/lib/api'

// apiClientをモック
jest.mock('@/lib/api', () => ({
  apiClient: {
    getTenant: jest.fn(),
    createTenant: jest.fn(),
    updateTenant: jest.fn(),
  },
}))

// useAuthをモック
jest.mock('@/contexts/AuthContext', () => {
  const React = jest.requireActual('react')
  return {
    __esModule: true,
    AuthProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
    useAuth: () => ({
      user: {
        id: 'user-1',
        email: 'test@example.com',
        username: 'testuser',
        role: 'PLATFORM_ADMIN',
        tenant_id: 'tenant-1',
        is_active: true,
      },
      isLoading: false,
      isAuthenticated: true,
    }),
  }
})

// useRouterをモック
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: jest.fn(),
    replace: jest.fn(),
    prefetch: jest.fn(),
    back: jest.fn(),
    pathname: '/',
    query: {},
    asPath: '/',
  }),
}))

describe('TenantForm', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('作成モード', () => {
    test('フォームの初期表示', () => {
      render(<TenantForm mode="create" />)
      
      // テナント名入力欄が表示されていることを確認
      expect(screen.getByLabelText(/テナント名/i)).toBeInTheDocument()
      // ドメイン入力欄が表示されていることを確認
      expect(screen.getByLabelText(/ドメイン/i)).toBeInTheDocument()
      // 保存ボタンが表示されていることを確認
      expect(screen.getByRole('button', { name: /保存/i })).toBeInTheDocument()
    })

    test('バリデーションエラー - テナント名が短すぎる', async () => {
      const user = userEvent.setup()
      render(<TenantForm mode="create" />)
      
      // テナント名に1文字を入力
      await user.type(screen.getByLabelText(/テナント名/i), 'A')
      
      // 保存ボタンをクリック
      await user.click(screen.getByRole('button', { name: /保存/i }))
      
      // バリデーションエラーが表示される
      await waitFor(() => {
        expect(screen.getByText(/テナント名は2文字以上である必要があります/i)).toBeInTheDocument()
      }, { timeout: 3000 })
    })

    test('バリデーションエラー - ドメインが短すぎる', async () => {
      const user = userEvent.setup()
      render(<TenantForm mode="create" />)
      
      // テナント名を入力
      await user.type(screen.getByLabelText(/テナント名/i), 'テストテナント')
      // ドメインに2文字を入力
      await user.type(screen.getByLabelText(/ドメイン/i), 'ab')
      
      // 保存ボタンをクリック
      await user.click(screen.getByRole('button', { name: /保存/i }))
      
      // バリデーションエラーが表示される
      await waitFor(() => {
        expect(screen.getByText(/ドメインは3文字以上である必要があります/i)).toBeInTheDocument()
      }, { timeout: 3000 })
    })

    test('テナント作成成功', async () => {
      const user = userEvent.setup()
      const mockCreateTenant = jest.fn().mockResolvedValue({ id: 'tenant-1' })
      ;(apiClient.createTenant as jest.Mock) = mockCreateTenant
      
      render(<TenantForm mode="create" />)
      
      // フォームに入力
      await user.type(screen.getByLabelText(/テナント名/i), 'テストテナント')
      await user.type(screen.getByLabelText(/ドメイン/i), 'test-tenant')
      
      // 保存ボタンをクリック
      await user.click(screen.getByRole('button', { name: /保存/i }))
      
      // 作成関数が呼ばれたことを確認
      await waitFor(() => {
        expect(mockCreateTenant).toHaveBeenCalled()
      })
    })
  })

  describe('編集モード', () => {
    test('既存テナントの読み込み', async () => {
      const mockTenant = {
        id: 'tenant-1',
        name: 'テストテナント',
        domain: 'test-tenant',
        plan: 'BASIC',
        status: 'ACTIVE',
        api_key: 'test-api-key',
        settings: {
          default_model: 'gpt-4',
          chunk_size: 1024,
          chunk_overlap: 200,
        },
        created_at: '2024-01-01T00:00:00Z',
      }
      
      ;(apiClient.getTenant as jest.Mock) = jest.fn().mockResolvedValue(mockTenant)
      
      render(<TenantForm tenantId="tenant-1" mode="edit" />)
      
      // テナント情報が読み込まれるまで待機
      await waitFor(() => {
        expect(apiClient.getTenant).toHaveBeenCalledWith('tenant-1')
      })
      
      // テナント名がフォームに設定されていることを確認
      await waitFor(() => {
        const nameInput = screen.getByLabelText(/テナント名/i) as HTMLInputElement
        expect(nameInput.value).toBe('テストテナント')
      })
    })

    test('テナント更新成功', async () => {
      const user = userEvent.setup()
      const mockTenant = {
        id: 'tenant-1',
        name: 'テストテナント',
        domain: 'test-tenant',
        plan: 'BASIC',
        status: 'ACTIVE',
        api_key: 'test-api-key',
        settings: {},
        created_at: '2024-01-01T00:00:00Z',
      }
      
      const mockUpdateTenant = jest.fn().mockResolvedValue(undefined)
      ;(apiClient.getTenant as jest.Mock) = jest.fn().mockResolvedValue(mockTenant)
      ;(apiClient.updateTenant as jest.Mock) = mockUpdateTenant
      
      render(<TenantForm tenantId="tenant-1" mode="edit" />)
      
      // テナント情報が読み込まれるまで待機
      await waitFor(() => {
        expect(apiClient.getTenant).toHaveBeenCalled()
      })
      
      // ローディングが終了し、テナント名入力欄が表示されるまで待機
      await waitFor(() => {
        const nameInput = screen.getByLabelText(/テナント名/i) as HTMLInputElement
        expect(nameInput.value).toBe('テストテナント')
      }, { timeout: 5000 })
      
      // テナント名を変更
      const nameInput = screen.getByLabelText(/テナント名/i)
      await user.clear(nameInput)
      await user.type(nameInput, '更新されたテナント')
      
      // 保存ボタンをクリック
      await user.click(screen.getByRole('button', { name: /保存/i }))
      
      // 更新関数が呼ばれたことを確認
      await waitFor(() => {
        expect(mockUpdateTenant).toHaveBeenCalledWith('tenant-1', expect.objectContaining({
          name: '更新されたテナント',
        }))
      })
    })
  })

  describe('表示モード', () => {
    test('テナント情報の表示', async () => {
      const mockTenant = {
        id: 'tenant-1',
        name: 'テストテナント',
        domain: 'test-tenant',
        plan: 'BASIC',
        status: 'ACTIVE',
        api_key: 'test-api-key',
        settings: {},
        created_at: '2024-01-01T00:00:00Z',
      }
      
      ;(apiClient.getTenant as jest.Mock) = jest.fn().mockResolvedValue(mockTenant)
      
      render(<TenantForm tenantId="tenant-1" mode="view" />)
      
      // テナント情報が読み込まれるまで待機
      await waitFor(() => {
        expect(apiClient.getTenant).toHaveBeenCalledWith('tenant-1')
      })
      
      // テナント名が表示されることを確認
      await waitFor(() => {
        const nameInput = screen.getByLabelText(/テナント名/i) as HTMLInputElement
        expect(nameInput.value).toBe('テストテナント')
      }, { timeout: 5000 })
    })

    test('編集ボタンが表示されない（表示モード）', async () => {
      const mockTenant = {
        id: 'tenant-1',
        name: 'テストテナント',
        domain: 'test-tenant',
        plan: 'BASIC',
        status: 'ACTIVE',
        api_key: 'test-api-key',
        settings: {},
        created_at: '2024-01-01T00:00:00Z',
      }
      
      ;(apiClient.getTenant as jest.Mock) = jest.fn().mockResolvedValue(mockTenant)
      
      render(<TenantForm tenantId="tenant-1" mode="view" />)
      
      // 保存ボタンが表示されないことを確認
      await waitFor(() => {
        expect(screen.queryByRole('button', { name: /保存/i })).not.toBeInTheDocument()
      })
    })
  })

  describe('エラーハンドリング', () => {
    test('テナント取得エラー', async () => {
      ;(apiClient.getTenant as jest.Mock) = jest.fn().mockRejectedValue(new Error('取得に失敗しました'))
      
      render(<TenantForm tenantId="tenant-1" mode="edit" />)
      
      // エラーメッセージが表示される
      await waitFor(() => {
        expect(screen.getByText(/テナント情報の取得に失敗しました/i)).toBeInTheDocument()
      }, { timeout: 5000 })
    })

    test('テナント保存エラー', async () => {
      const user = userEvent.setup()
      const mockCreateTenant = jest.fn().mockRejectedValue(new Error('保存に失敗しました'))
      ;(apiClient.createTenant as jest.Mock) = mockCreateTenant
      
      render(<TenantForm mode="create" />)
      
      // フォームに入力
      await user.type(screen.getByLabelText(/テナント名/i), 'テストテナント')
      await user.type(screen.getByLabelText(/ドメイン/i), 'test-tenant')
      
      // 保存ボタンをクリック
      await user.click(screen.getByRole('button', { name: /保存/i }))
      
      // エラーメッセージが表示される
      await waitFor(() => {
        expect(screen.getByText(/テナントの保存に失敗しました/i)).toBeInTheDocument()
      }, { timeout: 5000 })
    })
  })
})

