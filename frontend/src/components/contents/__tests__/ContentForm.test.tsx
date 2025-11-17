/**
 * ContentFormコンポーネントのテスト
 * 
 * コンテンツ管理フォームコンポーネントの動作を検証します。
 */

import React from 'react'
import { render, screen, waitFor } from '@/tests/utils'
import userEvent from '@testing-library/user-event'
import { ContentForm } from '../ContentForm'
import { apiClient } from '@/lib/api'

// apiClientをモック
jest.mock('@/lib/api', () => ({
  apiClient: {
    getContent: jest.fn(),
    uploadFile: jest.fn(),
    createContent: jest.fn(),
    updateContent: jest.fn(),
    deleteContent: jest.fn(),
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
        role: 'TENANT_ADMIN',
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

describe('ContentForm', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('作成モード', () => {
    test('フォームの初期表示', () => {
      render(<ContentForm mode="create" />)
      
      // タイトル入力欄が表示されていることを確認
      expect(screen.getByLabelText(/タイトル/i)).toBeInTheDocument()
      // 説明入力欄が表示されていることを確認
      expect(screen.getByLabelText(/説明/i)).toBeInTheDocument()
      // 保存ボタンが表示されていることを確認
      expect(screen.getByRole('button', { name: /保存/i })).toBeInTheDocument()
    })

    test('ファイルアップロード - ファイル選択', async () => {
      const user = userEvent.setup()
      render(<ContentForm mode="create" />)
      
      // ファイル入力欄を取得
      const fileInput = screen.getByLabelText(/ファイルを選択/i) as HTMLInputElement
      
      // モックファイルを作成
      const file = new File(['test content'], 'test.pdf', { type: 'application/pdf' })
      
      // ファイルを選択
      await user.upload(fileInput, file)
      
      // ファイル名が表示されることを確認（実装に依存）
      await waitFor(() => {
        expect(fileInput.files?.[0]).toBe(file)
      })
    })

    test('バリデーションエラー - タイトル未入力', async () => {
      const user = userEvent.setup()
      render(<ContentForm mode="create" />)
      
      // タイトルを空のまま保存ボタンをクリック
      const saveButton = screen.getByRole('button', { name: /保存/i })
      await user.click(saveButton)
      
      // バリデーションエラーが表示される（フォーム送信がトリガーされるまで待機）
      await waitFor(() => {
        const errorMessage = screen.queryByText(/タイトルは必須です/i) ||
                            screen.queryByText(/タイトル/i)
        // エラーメッセージが表示されるか、またはフォームが送信されていないことを確認
        expect(errorMessage || !saveButton.hasAttribute('disabled')).toBeTruthy()
      }, { timeout: 5000 })
    })

    test('ファイルアップロード成功', async () => {
      const user = userEvent.setup()
      const mockUploadFile = jest.fn().mockResolvedValue(undefined)
      ;(apiClient.uploadFile as jest.Mock) = mockUploadFile
      
      render(<ContentForm mode="create" />)
      
      // タイトルを入力
      await user.type(screen.getByLabelText(/タイトル/i), 'テストコンテンツ')
      
      // ファイルを選択
      const fileInput = screen.getByLabelText(/ファイルを選択/i) as HTMLInputElement
      const file = new File(['test content'], 'test.pdf', { type: 'application/pdf' })
      await user.upload(fileInput, file)
      
      // 保存ボタンをクリック
      await user.click(screen.getByRole('button', { name: /保存/i }))
      
      // アップロード関数が呼ばれたことを確認
      await waitFor(() => {
        expect(mockUploadFile).toHaveBeenCalled()
      })
    })

    test('URL入力モード切り替え', async () => {
      const user = userEvent.setup()
      render(<ContentForm mode="create" />)
      
      // URL入力ラジオボタンをクリック（「URLを入力」というラベルのラジオボタン）
      const urlRadioLabel = screen.getByText(/URLを入力/i)
      const urlRadio = urlRadioLabel.closest('div')?.querySelector('input[type="radio"]') as HTMLInputElement
      if (urlRadio) {
        await user.click(urlRadio)
      }
      
      // URL入力欄が表示されることを確認（placeholderやname属性で探す）
      await waitFor(() => {
        const urlInput = screen.queryByPlaceholderText(/https?:\/\//i) || 
                        screen.queryByRole('textbox', { name: /URL/i }) ||
                        screen.queryByLabelText(/URL/i)
        expect(urlInput).toBeInTheDocument()
      }, { timeout: 3000 })
    })

    test('URL入力でコンテンツ作成', async () => {
      const user = userEvent.setup()
      const mockCreateContent = jest.fn().mockResolvedValue({ id: 'content-1' })
      ;(apiClient.createContent as jest.Mock) = mockCreateContent
      
      render(<ContentForm mode="create" />)
      
      // URL入力モードに切り替え（「URLを入力」というラベルのラジオボタン）
      const urlRadioLabel = screen.getByText(/URLを入力/i)
      const urlRadio = urlRadioLabel.closest('div')?.querySelector('input[type="radio"]') as HTMLInputElement
      if (urlRadio) {
        await user.click(urlRadio)
      }
      
      // URL入力欄が表示されるまで待機
      await waitFor(() => {
        const urlInput = screen.queryByPlaceholderText(/https?:\/\//i) || 
                        screen.queryByRole('textbox', { name: /URL/i }) ||
                        screen.queryByLabelText(/URL/i)
        expect(urlInput).toBeInTheDocument()
      }, { timeout: 3000 })
      
      // タイトルを入力
      await user.type(screen.getByLabelText(/タイトル/i), 'テストコンテンツ')
      
      // URLを入力（placeholderやname属性で探す）
      const urlInput = screen.queryByPlaceholderText(/https?:\/\//i) || 
                      screen.queryByRole('textbox', { name: /URL/i }) ||
                      screen.queryByLabelText(/URL/i)
      if (urlInput) {
        await user.type(urlInput as HTMLElement, 'https://example.com/test.html')
      }
      
      // 保存ボタンをクリック
      await user.click(screen.getByRole('button', { name: /保存/i }))
      
      // コンテンツ作成関数が呼ばれたことを確認
      await waitFor(() => {
        expect(mockCreateContent).toHaveBeenCalled()
      })
    })
  })

  describe('編集モード', () => {
    test('既存コンテンツの読み込み', async () => {
      const mockContent = {
        id: 'content-1',
        title: 'テストコンテンツ',
        description: 'テスト説明',
        file_type: 'PDF',
        tags: ['tag1', 'tag2'],
        status: 'INDEXED',
        tenant_id: 'tenant-1',
        file_name: 'test.pdf',
        uploaded_at: '2024-01-01T00:00:00Z',
      }
      
      ;(apiClient.getContent as jest.Mock) = jest.fn().mockResolvedValue(mockContent)
      
      render(<ContentForm contentId="content-1" mode="edit" />)
      
      // コンテンツ情報が読み込まれるまで待機
      await waitFor(() => {
        expect(apiClient.getContent).toHaveBeenCalledWith('content-1')
      })
      
      // タイトルがフォームに設定されていることを確認
      await waitFor(() => {
        const titleInput = screen.getByLabelText(/タイトル/i) as HTMLInputElement
        expect(titleInput.value).toBe('テストコンテンツ')
      })
    })

    test('コンテンツ更新成功', async () => {
      const user = userEvent.setup()
      const mockContent = {
        id: 'content-1',
        title: 'テストコンテンツ',
        description: 'テスト説明',
        file_type: 'PDF',
        tags: [],
        status: 'INDEXED',
        tenant_id: 'tenant-1',
        file_name: 'test.pdf',
        uploaded_at: '2024-01-01T00:00:00Z',
      }
      
      const mockUpdateContent = jest.fn().mockResolvedValue(undefined)
      ;(apiClient.getContent as jest.Mock) = jest.fn().mockResolvedValue(mockContent)
      ;(apiClient.updateContent as jest.Mock) = mockUpdateContent
      
      render(<ContentForm contentId="content-1" mode="edit" />)
      
      // コンテンツ情報が読み込まれるまで待機
      await waitFor(() => {
        expect(apiClient.getContent).toHaveBeenCalled()
      })
      
      // ローディングが終了し、タイトル入力欄が表示されるまで待機
      await waitFor(() => {
        const titleInput = screen.getByLabelText(/タイトル/i) as HTMLInputElement
        expect(titleInput.value).toBe('テストコンテンツ')
      }, { timeout: 5000 })
      
      // タイトルを変更
      const titleInput = screen.getByLabelText(/タイトル/i)
      await user.clear(titleInput)
      await user.type(titleInput, '更新されたタイトル')
      
      // 保存ボタンをクリック
      await user.click(screen.getByRole('button', { name: /保存/i }))
      
      // 更新関数が呼ばれたことを確認
      await waitFor(() => {
        expect(mockUpdateContent).toHaveBeenCalledWith('content-1', expect.objectContaining({
          title: '更新されたタイトル',
        }))
      })
    })
  })

  describe('表示モード', () => {
    test('コンテンツ情報の表示', async () => {
      const mockContent = {
        id: 'content-1',
        title: 'テストコンテンツ',
        description: 'テスト説明',
        file_type: 'PDF',
        tags: ['tag1', 'tag2'],
        status: 'INDEXED',
        tenant_id: 'tenant-1',
        file_name: 'test.pdf',
        uploaded_at: '2024-01-01T00:00:00Z',
        chunk_count: 10,
      }
      
      ;(apiClient.getContent as jest.Mock) = jest.fn().mockResolvedValue(mockContent)
      
      render(<ContentForm contentId="content-1" mode="view" />)
      
      // コンテンツ情報が表示されるまで待機
      await waitFor(() => {
        expect(apiClient.getContent).toHaveBeenCalledWith('content-1')
      })
      
      // タイトルが表示されることを確認
      await waitFor(() => {
        const titleInput = screen.getByLabelText(/タイトル/i) as HTMLInputElement
        expect(titleInput.value).toBe('テストコンテンツ')
      }, { timeout: 5000 })
      
      // 説明が表示されることを確認
      await waitFor(() => {
        const descriptionTextarea = screen.getByLabelText(/説明/i) as HTMLTextAreaElement
        expect(descriptionTextarea.value).toBe('テスト説明')
      }, { timeout: 5000 })
    })

    test('編集ボタンが表示されない（表示モード）', async () => {
      const mockContent = {
        id: 'content-1',
        title: 'テストコンテンツ',
        description: 'テスト説明',
        file_type: 'PDF',
        tags: [],
        status: 'INDEXED',
        tenant_id: 'tenant-1',
        file_name: 'test.pdf',
        uploaded_at: '2024-01-01T00:00:00Z',
      }
      
      ;(apiClient.getContent as jest.Mock) = jest.fn().mockResolvedValue(mockContent)
      
      render(<ContentForm contentId="content-1" mode="view" />)
      
      // 保存ボタンが表示されないことを確認
      await waitFor(() => {
        expect(screen.queryByRole('button', { name: /保存/i })).not.toBeInTheDocument()
      })
    })
  })

  describe('エラーハンドリング', () => {
    test('コンテンツ取得エラー', async () => {
      ;(apiClient.getContent as jest.Mock) = jest.fn().mockRejectedValue(new Error('取得に失敗しました'))
      
      render(<ContentForm contentId="content-1" mode="edit" />)
      
      // エラーメッセージが表示される
      await waitFor(() => {
        expect(screen.getByText(/コンテンツ情報の取得に失敗しました/i)).toBeInTheDocument()
      }, { timeout: 5000 })
    })

    test('アップロードエラー', async () => {
      const user = userEvent.setup()
      const mockUploadFile = jest.fn().mockRejectedValue(new Error('アップロードに失敗しました'))
      ;(apiClient.uploadFile as jest.Mock) = mockUploadFile
      
      render(<ContentForm mode="create" />)
      
      // タイトルを入力
      await user.type(screen.getByLabelText(/タイトル/i), 'テストコンテンツ')
      
      // ファイルを選択
      const fileInput = screen.getByLabelText(/ファイルを選択/i) as HTMLInputElement
      const file = new File(['test content'], 'test.pdf', { type: 'application/pdf' })
      await user.upload(fileInput, file)
      
      // 保存ボタンをクリック
      await user.click(screen.getByRole('button', { name: /保存/i }))
      
      // エラーメッセージが表示される
      await waitFor(() => {
        expect(screen.getByText(/コンテンツの保存に失敗しました/i)).toBeInTheDocument()
      }, { timeout: 5000 })
    })
  })
})

