/**
 * API クライアント
 * 
 * このファイルはバックエンドAPIとの通信を行うためのクライアントを定義します。
 * Axiosを使用してHTTPリクエストを送信し、認証、エラーハンドリング、レスポンス処理を統合的に管理します。
 * 
 * 主な機能:
 * - HTTPリクエストの送信
 * - JWT認証トークンの管理
 * - エラーハンドリング
 * - レスポンスの型安全な処理
 * - リクエスト/レスポンスのインターセプト
 */

import axios, { AxiosInstance, AxiosResponse } from 'axios';

// 型定義
export interface User {
  id: number;
  email: string;
  username: string;
  role: 'PLATFORM_ADMIN' | 'TENANT_ADMIN' | 'OPERATOR' | 'AUDITOR';
  tenant_id?: string;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
  last_login_at?: string;
}

export interface Tenant {
  id: string;
  name: string;
  domain: string;
  plan: 'FREE' | 'BASIC' | 'PRO' | 'ENTERPRISE';
  status: 'ACTIVE' | 'SUSPENDED' | 'DELETED';
  api_key: string;
  settings: Record<string, any>;
  created_at: string;
  updated_at?: string;
}

export interface Content {
  id: string;
  tenant_id: string;
  title: string;
  file_name: string;
  file_type: 'PDF' | 'HTML' | 'MD' | 'CSV' | 'TXT';
  size_bytes: number;
  status: 'UPLOADED' | 'PROCESSING' | 'INDEXED' | 'FAILED';
  description?: string;
  tags: string[];
  uploaded_at: string;
  indexed_at?: string;
  chunk_count?: number;
}

export interface ChatRequest {
  session_id: string;
  query: string;
  context?: {
    user_metadata?: Record<string, any>;
  };
  options?: {
    model?: string;
    top_k?: number;
    include_sources?: boolean;
    stream?: boolean;
  };
}

export interface ChatResponse {
  conversation_id: string;
  answer: string;
  sources: Array<{
    chunk_id: string;
    file_name: string;
    page?: number;
    score: number;
    snippet: string;
  }>;
  metadata: {
    model: string;
    tokens_in: number;
    tokens_out: number;
    latency_ms: number;
  };
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface ApiError {
  error: {
    code: string;
    message: string;
    details?: any;
  };
}

// APIクライアントクラス
class ApiClient {
  /**
   * APIクライアント
   * 
   * バックエンドAPIとの通信を管理するクラスです。
   * Axiosインスタンスをラップし、認証、エラーハンドリング、リクエスト/レスポンスの
   * インターセプト機能を提供します。
   * 
   * 属性:
   *   client: Axiosインスタンス
   *   baseURL: APIのベースURL
   */
  private client: AxiosInstance;
  private baseURL: string;

  constructor(baseURL: string = 'http://localhost:8000') {
    this.baseURL = baseURL;
    this.client = axios.create({
      baseURL: `${baseURL}/api/v1`,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // リクエストインターセプター（認証トークン追加）
    this.client.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('access_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // レスポンスインターセプター（エラーハンドリング）
    this.client.interceptors.response.use(
      (response: AxiosResponse) => {
        return response;
      },
      async (error) => {
        if (error.response?.status === 401) {
          // トークン期限切れの場合、リフレッシュトークンで更新を試行
          const refreshToken = localStorage.getItem('refresh_token');
          if (refreshToken) {
            try {
              const response = await this.refreshToken(refreshToken);
              localStorage.setItem('access_token', response.access_token);
              localStorage.setItem('refresh_token', response.refresh_token);
              
              // 元のリクエストを再実行
              const originalRequest = error.config;
              originalRequest.headers.Authorization = `Bearer ${response.access_token}`;
              return this.client(originalRequest);
            } catch (refreshError) {
              // リフレッシュも失敗した場合、ログイン画面にリダイレクト
              localStorage.removeItem('access_token');
              localStorage.removeItem('refresh_token');
              window.location.href = '/login';
            }
          } else {
            window.location.href = '/login';
          }
        }
        return Promise.reject(error);
      }
    );
  }

  // 認証関連
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const response = await this.client.post('/auth/login', credentials);
    return response.data;
  }

  async logout(): Promise<void> {
    await this.client.post('/auth/logout');
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  }

  // 課金: Checkoutセッション作成
  async createCheckoutSession(plan: 'BASIC' | 'PRO', billingCycle: 'MONTHLY' | 'YEARLY' = 'MONTHLY'): Promise<{ url: string; session_id: string; }> {
    try {
      const res = await this.client.post('/billing/checkout', {
        plan,
        billing_cycle: billingCycle
      });
      return res.data;
    } catch (error: any) {
      throw error;
    }
  }

  async refreshToken(refreshToken: string): Promise<{ access_token: string; refresh_token: string }> {
    const response = await this.client.post('/auth/refresh', { refresh_token: refreshToken });
    return response.data;
  }

  async getCurrentUser(): Promise<User> {
    const response = await this.client.get('/auth/me');
    return response.data;
  }

  // ユーザー管理
  async getUsers(skip: number = 0, limit: number = 100): Promise<User[]> {
    const response = await this.client.get(`/users/?skip=${skip}&limit=${limit}`);
    return response.data;
  }

  async getUser(id: number): Promise<User> {
    const response = await this.client.get(`/users/${id}`);
    return response.data;
  }

  async createUser(userData: Partial<User>): Promise<User> {
    const response = await this.client.post('/users/', userData);
    return response.data;
  }

  async updateUser(id: number, userData: Partial<User>): Promise<User> {
    const response = await this.client.put(`/users/${id}`, userData);
    return response.data;
  }

  async deleteUser(id: number): Promise<void> {
    await this.client.delete(`/users/${id}`);
  }

  // テナント管理
  async getTenants(skip: number = 0, limit: number = 100, status?: string): Promise<Tenant[]> {
    const params = new URLSearchParams({ skip: skip.toString(), limit: limit.toString() });
    if (status) params.append('status', status);
    const response = await this.client.get(`/tenants/?${params}`);
    return response.data;
  }

  async getTenant(id: string): Promise<Tenant> {
    const response = await this.client.get(`/tenants/${id}`);
    return response.data;
  }

  async createTenant(tenantData: Partial<Tenant>): Promise<Tenant> {
    const response = await this.client.post('/tenants/', tenantData);
    return response.data;
  }

  async updateTenant(id: string, tenantData: Partial<Tenant>): Promise<Tenant> {
    const response = await this.client.put(`/tenants/${id}`, tenantData);
    return response.data;
  }

  async deleteTenant(id: string): Promise<void> {
    await this.client.delete(`/tenants/${id}`);
  }

  async regenerateApiKey(id: string): Promise<{ api_key: string }> {
    const response = await this.client.post(`/tenants/${id}/regenerate-api-key`);
    return response.data;
  }

  // コンテンツ管理
  async getContents(skip: number = 0, limit: number = 100, fileType?: string, status?: string, search?: string): Promise<Content[]> {
    const params = new URLSearchParams({ skip: skip.toString(), limit: limit.toString() });
    if (fileType) params.append('file_type', fileType);
    if (status) params.append('status', status);
    if (search) params.append('search', search);
    const response = await this.client.get(`/contents/?${params}`);
    return response.data;
  }

  async getContent(id: string): Promise<Content> {
    const response = await this.client.get(`/contents/${id}`);
    return response.data;
  }

  async createContent(contentData: Partial<Content>): Promise<Content> {
    const response = await this.client.post('/contents/', contentData);
    return response.data;
  }

  async updateContent(id: string, contentData: Partial<Content>): Promise<Content> {
    const response = await this.client.put(`/contents/${id}`, contentData);
    return response.data;
  }

  async deleteContent(id: string): Promise<void> {
    await this.client.delete(`/contents/${id}`);
  }

  async uploadFile(file: File, title?: string, description?: string, tags?: string[]): Promise<Content> {
    const formData = new FormData();
    formData.append('file', file);
    if (title) formData.append('title', title);
    if (description) formData.append('description', description);
    if (tags) formData.append('tags', tags.join(','));

    const response = await this.client.post('/contents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data.content;
  }

  // チャット機能
  async sendMessage(request: ChatRequest): Promise<ChatResponse> {
    const response = await this.client.post('/chats', request);
    return response.data;
  }

  // 統計情報
  async getUsageStats(startDate?: string, endDate?: string, granularity?: string): Promise<any> {
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    if (granularity) params.append('granularity', granularity);
    
    const response = await this.client.get(`/stats/usage?${params}`);
    return response.data;
  }

  async getDashboardStats(period: string = 'month'): Promise<any> {
    const response = await this.client.get(`/stats/dashboard?period=${period}`);
    return response.data;
  }
}

// シングルトンインスタンス
export const apiClient = new ApiClient();

// エクスポート
export default apiClient;
