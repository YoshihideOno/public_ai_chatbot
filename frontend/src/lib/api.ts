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

export interface TenantSettings {
  max_users?: number;
  max_contents?: number;
  max_storage_mb?: number;
  features?: string[];
  custom_domain?: string;
  branding?: {
    logo_url?: string;
    primary_color?: string;
    secondary_color?: string;
  };
  notifications?: {
    email_enabled?: boolean;
    webhook_url?: string;
  };
}

export interface Tenant {
  id: string;
  name: string;
  domain: string;
  plan: 'FREE' | 'BASIC' | 'PRO' | 'ENTERPRISE';
  status: 'ACTIVE' | 'SUSPENDED' | 'DELETED';
  api_key: string;
  settings: TenantSettings;
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
    user_metadata?: Record<string, string | number | boolean>;
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

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
  role: 'OPERATOR' | 'AUDITOR';
}

export interface TenantRegistrationRequest {
  tenant_name: string;
  tenant_domain: string;
  admin_email: string;
  admin_username: string;
  admin_password: string;
}

export interface TenantRegistrationResponse {
  tenant_id: string;
  tenant_name: string;
  admin_user_id: string;
  admin_email: string;
  message: string;
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
    details?: Record<string, unknown>;
  };
}

export interface AdminRequest {
  id: number;
  user_id: number;
  reason: string;
  status: 'PENDING' | 'APPROVED' | 'REJECTED';
  created_at: string;
  reviewed_at?: string;
  reviewed_by?: number;
  review_comment?: string;
}

export interface UsageStats {
  period: string;
  total_requests: number;
  total_tokens: number;
  total_cost: number;
  active_users: number;
  data_points: Array<{
    date: string;
    requests: number;
    tokens: number;
    cost: number;
    users: number;
  }>;
}

export interface DashboardStats {
  period: string;
  overview: {
    total_users: number;
    total_tenants: number;
    total_contents: number;
    total_chats: number;
  };
  usage: {
    requests_today: number;
    requests_this_month: number;
    tokens_today: number;
    tokens_this_month: number;
  };
  revenue: {
    monthly_revenue: number;
    yearly_revenue: number;
    growth_rate: number;
  };
  top_tenants: Array<{
    tenant_id: string;
    tenant_name: string;
    request_count: number;
    revenue: number;
  }>;
}

// APIクライアントクラス
export class ApiClient {
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

  constructor(baseURL?: string) {
    // 環境に応じてベースURLを設定
    if (baseURL) {
      this.baseURL = baseURL;
    } else if (typeof window !== 'undefined') {
      // ブラウザ環境では環境変数または localhost を使用
      this.baseURL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
    } else {
      // サーバーサイド環境では Docker サービス名を使用
      this.baseURL = 'http://fastapi:8000';
    }
    
    this.client = axios.create({
      baseURL: `${this.baseURL}/api/v1`,
      timeout: 30000,  // 30秒のタイムアウト
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
            } catch {
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

  async register(data: RegisterRequest): Promise<void> {
    const response = await this.client.post('/auth/register', data);
    return response.data;
  }

  async registerTenant(data: TenantRegistrationRequest): Promise<TenantRegistrationResponse> {
    // テナント登録のタイムアウト設定
    const response = await this.client.post('/auth/register-tenant', data, {
      timeout: 30000,  // 30秒のタイムアウト
    });
    return response.data;
  }

  async requestPasswordReset(email: string): Promise<void> {
    const response = await this.client.post('/auth/password-reset', { email });
    return response.data;
  }

  async confirmPasswordReset(token: string, newPassword: string): Promise<void> {
    const response = await this.client.post('/auth/password-reset/confirm', {
      token,
      new_password: newPassword
    });
    return response.data;
  }

  async verifyEmail(token: string): Promise<{ message: string; user_id: string; email: string }> {
    const response = await this.client.post('/auth/verify-email', null, {
      params: { token }
    });
    return response.data;
  }

  async requestAdminRole(reason: string): Promise<void> {
    const response = await this.client.post('/auth/admin-request', { reason });
    return response.data;
  }

  async getAdminRequests(): Promise<AdminRequest[]> {
    const response = await this.client.get('/auth/admin-requests');
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
    } catch (error) {
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
  async getUsageStats(startDate?: string, endDate?: string, granularity?: string): Promise<UsageStats> {
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    if (granularity) params.append('granularity', granularity);
    
    const response = await this.client.get(`/stats/usage?${params}`);
    return response.data;
  }

  async getDashboardStats(period: string = 'month'): Promise<DashboardStats> {
    const response = await this.client.get(`/stats/dashboard?period=${period}`);
    return response.data;
  }
}

// シングルトンインスタンス
export const apiClient = new ApiClient();

// エクスポート
export default apiClient;
