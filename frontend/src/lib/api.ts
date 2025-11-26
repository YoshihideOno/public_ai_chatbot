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
  id: string;
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
  max_queries_per_day?: number;
  chunk_size?: number;
  chunk_overlap?: number;
  enable_api_access?: boolean;
  enable_webhook?: boolean;
  webhook_url?: string;
  // 追加: LLMモデル既定
  default_model?: string | null; // 回答用モデル（nullは未選択を意味する）
  embedding_model?: string | null; // 埋め込み用モデル（nullは未選択を意味する）
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
  content_type?: 'PDF' | 'HTML' | 'MD' | 'CSV' | 'TXT'; // API送信用
  size_bytes?: number;
  file_size?: number;
  status: 'UPLOADED' | 'PROCESSING' | 'INDEXED' | 'FAILED';
  description?: string;
  tags: string[];
  uploaded_at: string;
  indexed_at?: string;
  chunk_count?: number;
  file_url?: string;
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

export interface UsageStats {
  tenant_id: string;
  metric_type: string;
  granularity: string;
  start_date: string;
  end_date: string;
  total_queries: number;
  unique_users: number;
  avg_response_time_ms: number;
  feedback_rate: number;
  like_rate: number;
}

export interface LlmUsageStats {
  tenant_id: string;
  model: string;
  total_tokens_in: number;
  total_tokens_out: number;
  total_cost: number;
  request_count: number;
  avg_tokens_per_request: number;
}

export interface DashboardStats {
  tenant_id: string;
  period: string;
  usage_stats: UsageStats;
  llm_usage: LlmUsageStats[];
  storage_stats: {
    tenant_id: string;
    total_files: number;
    total_size_mb: number;
    total_chunks: number;
    storage_limit_mb: number;
    usage_percentage: number;
    indexed_files?: number;
    processing_files?: number;
    failed_files?: number;
  };
  top_queries: Array<{
    query: string;
    count: number;
    avg_response_time_ms: number;
    like_rate: number;
  }>;
  recent_activity: Array<{
    type: string;
    description: string;
    timestamp: string;
    details: Record<string, unknown>;
  }>;
}

// コンテンツ統計（サマリー）
export interface ContentStatsSummary {
  total_files: number;
  status_counts: Record<string, number>;
  total_chunks: number;
  total_size_mb: number;
  file_types: Record<string, number>;
}

export interface RecentActivity {
  id: string;
  user_id?: string;
  tenant_id?: string;
  action: string;
  entity_type?: string;
  entity_id?: string;
  message?: string;
  created_at: string;
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
    // ベースURLは常にブラウザ到達可能なURLを優先
    // SSRで初期化されても、NEXT_PUBLIC_API_BASE_URL もしくは localhost を使う
    // Dockerコンテナ内のブラウザからは、host.docker.internalを使用する必要がある
    let browserBase = baseURL;
    
    if (!browserBase) {
      const staticEnvBase = process.env.NEXT_PUBLIC_API_BASE_URL || process.env.API_BASE_URL;
      // ブラウザ環境で実行されている場合、実行時に環境変数を読み込む
      if (typeof window !== 'undefined') {
        // 実行時にwindowオブジェクトから環境変数を取得（Next.jsのランタイム設定）
        const runtimeEnvBase = (window as typeof window & {
          __NEXT_DATA__?: {
            env?: {
              NEXT_PUBLIC_API_BASE_URL?: string;
            };
          };
        }).__NEXT_DATA__?.env?.NEXT_PUBLIC_API_BASE_URL;
        
        if (runtimeEnvBase) {
          browserBase = runtimeEnvBase;
        } else if (staticEnvBase) {
          // ビルド時に埋め込まれた環境変数を優先
          browserBase = staticEnvBase;
        } else if (window.location?.origin?.startsWith('http')) {
          // 同一オリジンホスティング時はフロントと同じオリジンにフォールバック
          browserBase = window.location.origin;
        } else {
          // 環境変数が設定されていない場合、Dockerコンテナ内で実行されている可能性を考慮
          // host.docker.internalを使用（WSL2環境ではextra_hostsで設定済み）
          browserBase = 'http://host.docker.internal:8000';
        }
      } else {
        // サーバーサイドでは、環境変数から取得
        browserBase = staticEnvBase || 'http://fastapi:8000';
      }
    }
    
    const resolvedBaseURL = browserBase ?? 'http://localhost:8000';
    this.baseURL = resolvedBaseURL;
    
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
          // /auth/me へのリクエストの場合は、リダイレクトせずにエラーを返す
          // （初期認証チェックでは、エラーを静かに処理するため）
          if (error.config?.url?.includes('/auth/me')) {
            return Promise.reject(error);
          }
          
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

  async updateCurrentUser(userData: Partial<User>): Promise<User> {
    const response = await this.client.put('/users/me', userData);
    return response.data;
  }

  // ユーザー管理
  async getUsers(skip: number = 0, limit: number = 100): Promise<User[]> {
    const response = await this.client.get(`/users/?skip=${skip}&limit=${limit}`);
    return response.data;
  }

  async getUser(id: string | number): Promise<User> {
    const response = await this.client.get(`/users/${id}`);
    return response.data;
  }

  async createUser(userData: Partial<User>): Promise<User> {
    const response = await this.client.post('/users/', userData);
    return response.data;
  }

  async updateUser(id: string | number, userData: Partial<User>): Promise<User> {
    const response = await this.client.put(`/users/${id}`, userData);
    return response.data;
  }

  async deleteUser(id: string | number): Promise<void> {
    await this.client.delete(`/users/${id}`);
  }

  // ユーザーのエクスポート（CSV/JSON）
  async exportUsers(params: { format: 'csv' | 'json'; search?: string; role?: User['role']; is_active?: boolean }): Promise<{ blob: Blob; filename?: string }> {
    const query = new URLSearchParams();
    query.set('format', params.format);
    if (params.search) query.set('search', params.search);
    if (params.role) query.set('role', params.role);
    if (typeof params.is_active === 'boolean') query.set('is_active', String(params.is_active));
    const response = await this.client.get(`/users/actions/export?${query.toString()}`, {
      responseType: 'blob',
    });
    const disposition = response.headers['content-disposition'] as string | undefined;
    let filename: string | undefined;
    if (disposition) {
      const match = disposition.match(/filename\*=UTF-8''([^;]+)|filename="?([^";]+)"?/);
      filename = decodeURIComponent((match?.[1] || match?.[2] || '').trim());
    }
    return { blob: response.data as Blob, filename };
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

  async getEmbedSnippet(tenantId: string): Promise<{ snippet: string; tenant_id: string; api_key: string }> {
    const response = await this.client.get(`/tenants/${tenantId}/embed-snippet`);
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

  async createContent(contentData: Partial<Content>): Promise<{ id: string; status: string; message?: string } | Content> {
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

  // ダウンロード（元ファイルバイナリ）
  async downloadContent(id: string): Promise<{ blob: Blob; filename?: string }> {
    const response = await this.client.get(`/contents/${id}/download`, {
      responseType: 'blob',
    });
    const disposition = response.headers['content-disposition'] as string | undefined;
    let filename: string | undefined;
    if (disposition) {
      const match = disposition.match(/filename\*=UTF-8''([^;]+)|filename="?([^";]+)"?/);
      filename = decodeURIComponent((match?.[1] || match?.[2] || '').trim());
    }
    return { blob: response.data as Blob, filename };
  }

  // エクスポート（CSV/JSON）
  async exportContents(params: { fileType?: string; status?: string; search?: string; format: 'csv' | 'json' }): Promise<{ blob: Blob; filename?: string }> {
    const query = new URLSearchParams();
    query.set('format', params.format);
    if (params.fileType) query.set('file_type', params.fileType);
    if (params.status) query.set('status', params.status);
    if (params.search) query.set('search', params.search);
    const response = await this.client.get(`/contents/actions/export?${query.toString()}`, {
      responseType: 'blob',
    });
    const disposition = response.headers['content-disposition'] as string | undefined;
    let filename: string | undefined;
    if (disposition) {
      const match = disposition.match(/filename\*=UTF-8''([^;]+)|filename="?([^";]+)"?/);
      filename = decodeURIComponent((match?.[1] || match?.[2] || '').trim());
    }
    return { blob: response.data as Blob, filename };
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

  // クエリアナリティクス（再集計/取得）
  async rebuildQueryAnalytics(params: { locale: string; period: 'today' | 'week' | 'month' | 'custom'; start_date?: string; end_date?: string; top_k?: number }): Promise<{ message: string }> {
    const query = new URLSearchParams();
    query.set('locale', params.locale);
    query.set('period', params.period);
    if (params.start_date) query.set('start_date', params.start_date);
    if (params.end_date) query.set('end_date', params.end_date);
    if (params.top_k) query.set('top_k', String(params.top_k));
    const res = await this.client.post(`/query-analytics/rebuild?${query.toString()}`);
    return res.data;
  }

  // コンテンツ統計サマリー
  async getContentStatsSummary(): Promise<ContentStatsSummary> {
    const response = await this.client.get('/contents/stats/summary');
    return response.data;
  }

  // ========== APIキー / モデル ========== 
  async getProvidersAndModels(): Promise<{ providers: Array<{ provider: string; models: string[] }> }> {
    const res = await this.client.get('/api-keys/providers');
    return res.data;
  }

  async getApiKeys(): Promise<{ api_keys: Array<{ id: string; tenant_id: string; provider: string; api_key_masked: string; model: string; is_active: boolean; created_at: string; updated_at?: string }>; total_count: number }> {
    const res = await this.client.get('/api-keys/');
    return res.data;
  }

  async createApiKey(payload: { provider: string; api_key: string; model: string }): Promise<{ id: string } & { tenant_id: string; provider: string; api_key_masked: string; model: string; is_active: boolean; created_at: string; updated_at?: string }> {
    const res = await this.client.post('/api-keys/', payload);
    return res.data;
  }

  async updateApiKey(
    apiKeyId: string,
    updateData: { is_active?: boolean; api_key?: string; model?: string }
  ): Promise<{ id: string; tenant_id: string; provider: string; api_key_masked: string; model: string; is_active: boolean; created_at: string; updated_at?: string }> {
    const res = await this.client.put(`/api-keys/${apiKeyId}`, updateData);
    return res.data;
  }

  async deleteApiKey(apiKeyId: string): Promise<void> {
    await this.client.delete(`/api-keys/${apiKeyId}`);
  }

  async verifyApiKey(apiKeyId: string): Promise<{ valid: boolean; provider: string; model: string; message?: string; error_code?: string }> {
    const res = await this.client.post(`/api-keys/${apiKeyId}/verify`);
    return res.data;
  }

  async verifyApiKeyInline(payload: { provider: string; model?: string; api_key: string }): Promise<{ valid: boolean; provider: string; model: string; message?: string; error_code?: string }> {
    const res = await this.client.post('/api-keys/verify-inline', payload);
    return res.data;
  }

  // テナント設定の取得/更新（自テナントはユーザー情報から取得している想定のため、ここでは汎用）
  async updateTenantSettings(tenantId: string, settings: Partial<TenantSettings>): Promise<{ message: string } | Tenant> {
    const res = await this.client.put(`/tenants/${tenantId}/settings`, settings);
    return res.data;
  }

  async exportTenants(format: 'csv' | 'json' = 'csv'): Promise<{ blob: Blob; filename: string }> {
    const res = await this.client.get<Blob>('/tenants/export', {
      params: { format },
      responseType: 'blob',
    });
    const disposition = res.headers['content-disposition'];
    const match = disposition?.match(/filename="?([^";]+)"?/i);
    const filename = match?.[1] ?? `tenants_export.${format}`;
    return {
      blob: res.data,
      filename,
    };
  }

  async getRecentActivities(limit: number = 10): Promise<RecentActivity[]> {
    const response = await this.client.get(`/audit-logs/recent?limit=${limit}`);
    return (response.data?.activities ?? []) as RecentActivity[];
  }
}

// シングルトンインスタンス
export const apiClient = new ApiClient();

// エクスポート
export default apiClient;
