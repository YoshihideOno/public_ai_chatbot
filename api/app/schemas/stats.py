from pydantic import BaseModel, validator
from typing import Optional, Dict, Any, List
from datetime import datetime, date
from enum import Enum


class TimeGranularity(str, Enum):
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"


class MetricType(str, Enum):
    QUERIES = "queries"
    USERS = "users"
    RESPONSE_TIME = "response_time"
    FEEDBACK = "feedback"
    LLM_USAGE = "llm_usage"
    STORAGE = "storage"


class StatsBase(BaseModel):
    tenant_id: str
    metric_type: MetricType
    granularity: TimeGranularity
    start_date: datetime
    end_date: datetime
    
    @validator('end_date')
    def validate_date_range(cls, v, values):
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError('終了日は開始日より後である必要があります')
        return v


class UsageStats(StatsBase):
    total_queries: int = 0
    unique_users: int = 0
    avg_response_time_ms: float = 0.0
    feedback_rate: float = 0.0
    like_rate: float = 0.0
    
    @validator('total_queries')
    def validate_total_queries(cls, v):
        if v < 0:
            raise ValueError('総質問数は0以上である必要があります')
        return v
    
    @validator('unique_users')
    def validate_unique_users(cls, v):
        if v < 0:
            raise ValueError('ユニークユーザー数は0以上である必要があります')
        return v
    
    @validator('avg_response_time_ms')
    def validate_response_time(cls, v):
        if v < 0:
            raise ValueError('平均応答時間は0以上である必要があります')
        return v
    
    @validator('feedback_rate')
    def validate_feedback_rate(cls, v):
        if v < 0 or v > 1:
            raise ValueError('評価率は0-1の範囲である必要があります')
        return v
    
    @validator('like_rate')
    def validate_like_rate(cls, v):
        if v < 0 or v > 1:
            raise ValueError('いいね率は0-1の範囲である必要があります')
        return v


class TimeSeriesData(BaseModel):
    timestamp: datetime
    value: float
    metadata: Dict[str, Any] = {}


class UsageTimeSeries(BaseModel):
    queries: List[TimeSeriesData] = []
    users: List[TimeSeriesData] = []
    response_time: List[TimeSeriesData] = []
    feedback_rate: List[TimeSeriesData] = []


class TopQuery(BaseModel):
    query: str
    count: int
    like_rate: float
    avg_response_time_ms: float
    
    @validator('query')
    def validate_query(cls, v):
        if len(v) > 500:
            raise ValueError('質問文は500文字以内である必要があります')
        return v.strip()
    
    @validator('count')
    def validate_count(cls, v):
        if v < 0:
            raise ValueError('質問回数は0以上である必要があります')
        return v
    
    @validator('like_rate')
    def validate_like_rate(cls, v):
        if v < 0 or v > 1:
            raise ValueError('いいね率は0-1の範囲である必要があります')
        return v


class LLMUsageStats(BaseModel):
    tenant_id: str
    model: str
    total_tokens_in: int = 0
    total_tokens_out: int = 0
    total_cost: float = 0.0
    request_count: int = 0
    avg_tokens_per_request: float = 0.0
    
    @validator('total_tokens_in')
    def validate_tokens_in(cls, v):
        if v < 0:
            raise ValueError('入力トークン数は0以上である必要があります')
        return v
    
    @validator('total_tokens_out')
    def validate_tokens_out(cls, v):
        if v < 0:
            raise ValueError('出力トークン数は0以上である必要があります')
        return v
    
    @validator('total_cost')
    def validate_cost(cls, v):
        if v < 0:
            raise ValueError('コストは0以上である必要があります')
        return v


class LLMUsageTimeSeries(BaseModel):
    model: str
    tokens_in: List[TimeSeriesData] = []
    tokens_out: List[TimeSeriesData] = []
    cost: List[TimeSeriesData] = []
    requests: List[TimeSeriesData] = []


class FeedbackStats(BaseModel):
    tenant_id: str
    total_feedback: int = 0
    positive_feedback: int = 0
    negative_feedback: int = 0
    no_feedback: int = 0
    positive_rate: float = 0.0
    
    @validator('total_feedback')
    def validate_total_feedback(cls, v):
        if v < 0:
            raise ValueError('総評価数は0以上である必要があります')
        return v
    
    @validator('positive_feedback')
    def validate_positive_feedback(cls, v):
        if v < 0:
            raise ValueError('ポジティブ評価数は0以上である必要があります')
        return v
    
    @validator('negative_feedback')
    def validate_negative_feedback(cls, v):
        if v < 0:
            raise ValueError('ネガティブ評価数は0以上である必要があります')
        return v


class FeedbackAnalysis(BaseModel):
    low_rated_queries: List[Dict[str, Any]] = []
    improvement_suggestions: List[str] = []
    sentiment_trends: List[TimeSeriesData] = []


class StorageStats(BaseModel):
    tenant_id: str
    total_files: int = 0
    total_size_mb: float = 0.0
    total_chunks: int = 0
    storage_limit_mb: int = 100
    usage_percentage: float = 0.0
    # ステータス別件数
    indexed_files: int = 0
    processing_files: int = 0
    failed_files: int = 0
    
    @validator('total_files')
    def validate_total_files(cls, v):
        if v < 0:
            raise ValueError('総ファイル数は0以上である必要があります')
        return v
    
    @validator('total_size_mb')
    def validate_total_size(cls, v):
        if v < 0:
            raise ValueError('総サイズは0以上である必要があります')
        return v
    
    @validator('total_chunks')
    def validate_total_chunks(cls, v):
        if v < 0:
            raise ValueError('総チャンク数は0以上である必要があります')
        return v

    @validator('indexed_files')
    def validate_indexed_files(cls, v):
        if v < 0:
            raise ValueError('インデックス済みファイル数は0以上である必要があります')
        return v

    @validator('processing_files')
    def validate_processing_files(cls, v):
        if v < 0:
            raise ValueError('処理中ファイル数は0以上である必要があります')
        return v

    @validator('failed_files')
    def validate_failed_files(cls, v):
        if v < 0:
            raise ValueError('失敗ファイル数は0以上である必要があります')
        return v


class DashboardStats(BaseModel):
    tenant_id: str
    period: str  # "today", "week", "month"
    usage_stats: UsageStats
    llm_usage: List[LLMUsageStats] = []
    storage_stats: StorageStats
    top_queries: List[TopQuery] = []
    recent_activity: List[Dict[str, Any]] = []


class AlertRule(BaseModel):
    id: str
    tenant_id: str
    name: str
    metric_type: MetricType
    threshold: float
    operator: str  # "gt", "lt", "eq", "gte", "lte"
    is_active: bool = True
    notification_channels: List[str] = []
    
    @validator('name')
    def validate_name(cls, v):
        if len(v) < 1 or len(v) > 100:
            raise ValueError('アラート名は1-100文字である必要があります')
        return v.strip()
    
    @validator('threshold')
    def validate_threshold(cls, v):
        if v < 0:
            raise ValueError('閾値は0以上である必要があります')
        return v
    
    @validator('operator')
    def validate_operator(cls, v):
        valid_operators = ["gt", "lt", "eq", "gte", "lte"]
        if v not in valid_operators:
            raise ValueError(f'演算子は{valid_operators}のいずれかである必要があります')
        return v


class Alert(BaseModel):
    id: str
    tenant_id: str
    rule_id: str
    metric_type: MetricType
    current_value: float
    threshold: float
    message: str
    severity: str  # "low", "medium", "high", "critical"
    triggered_at: datetime
    resolved_at: Optional[datetime] = None
    is_resolved: bool = False
    
    @validator('message')
    def validate_message(cls, v):
        if len(v) > 500:
            raise ValueError('アラートメッセージは500文字以内である必要があります')
        return v.strip()
    
    @validator('severity')
    def validate_severity(cls, v):
        valid_severities = ["low", "medium", "high", "critical"]
        if v not in valid_severities:
            raise ValueError(f'重要度は{valid_severities}のいずれかである必要があります')
        return v


class MonitoringConfig(BaseModel):
    tenant_id: str
    enable_monitoring: bool = True
    alert_rules: List[AlertRule] = []
    notification_email: Optional[str] = None
    notification_webhook: Optional[str] = None
    check_interval_minutes: int = 5
    
    @validator('check_interval_minutes')
    def validate_check_interval(cls, v):
        if v < 1 or v > 1440:  # 1分から24時間
            raise ValueError('チェック間隔は1-1440分の範囲である必要があります')
        return v


class HealthCheck(BaseModel):
    service: str
    status: str  # "healthy", "degraded", "unhealthy"
    response_time_ms: float
    last_check: datetime
    details: Dict[str, Any] = {}
    
    @validator('status')
    def validate_status(cls, v):
        valid_statuses = ["healthy", "degraded", "unhealthy"]
        if v not in valid_statuses:
            raise ValueError(f'ステータスは{valid_statuses}のいずれかである必要があります')
        return v
    
    @validator('response_time_ms')
    def validate_response_time(cls, v):
        if v < 0:
            raise ValueError('応答時間は0以上である必要があります')
        return v


class SystemHealth(BaseModel):
    overall_status: str
    services: List[HealthCheck] = []
    timestamp: datetime
    
    @validator('overall_status')
    def validate_overall_status(cls, v):
        valid_statuses = ["healthy", "degraded", "unhealthy"]
        if v not in valid_statuses:
            raise ValueError(f'全体ステータスは{valid_statuses}のいずれかである必要があります')
        return v
