from pydantic import BaseModel, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class FileType(str, Enum):
    PDF = "PDF"
    HTML = "HTML"
    MD = "MD"
    CSV = "CSV"
    TXT = "TXT"


class FileStatus(str, Enum):
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    INDEXED = "INDEXED"
    FAILED = "FAILED"


class ContentBase(BaseModel):
    title: str
    content_type: FileType
    description: Optional[str] = None
    tags: List[str] = []
    metadata: Dict[str, Any] = {}
    
    @validator('title')
    def validate_title(cls, v):
        if len(v) < 1:
            raise ValueError('タイトルは必須です')
        if len(v) > 255:
            raise ValueError('タイトルは255文字以内である必要があります')
        return v.strip()
    
    @validator('description')
    def validate_description(cls, v):
        if v is not None and len(v) > 1000:
            raise ValueError('説明は1000文字以内である必要があります')
        return v.strip() if v else v
    
    @validator('tags')
    def validate_tags(cls, v):
        if len(v) > 10:
            raise ValueError('タグは10個以内である必要があります')
        for tag in v:
            if len(tag) > 50:
                raise ValueError('各タグは50文字以内である必要があります')
        return v


class ContentCreate(ContentBase):
    file_content: Optional[str] = None  # Base64 encoded content
    file_url: Optional[str] = None
    chunk_size: Optional[int] = None
    chunk_overlap: Optional[int] = None
    
    @validator('file_content')
    def validate_file_content(cls, v):
        if v is not None and len(v) > 50 * 1024 * 1024:  # 50MB limit
            raise ValueError('ファイルサイズは50MB以内である必要があります')
        return v
    
    @validator('chunk_size')
    def validate_chunk_size(cls, v):
        if v is not None and (v < 256 or v > 4096):
            raise ValueError('チャンクサイズは256-4096の範囲である必要があります')
        return v
    
    @validator('chunk_overlap')
    def validate_chunk_overlap(cls, v):
        if v is not None and (v < 0 or v > 512):
            raise ValueError('チャンクオーバーラップは0-512の範囲である必要があります')
        return v


class ContentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    
    @validator('title')
    def validate_title(cls, v):
        if v is not None:
            if len(v) < 1:
                raise ValueError('タイトルは必須です')
            if len(v) > 255:
                raise ValueError('タイトルは255文字以内である必要があります')
        return v.strip() if v else v
    
    @validator('description')
    def validate_description(cls, v):
        if v is not None and len(v) > 1000:
            raise ValueError('説明は1000文字以内である必要があります')
        return v.strip() if v else v
    
    @validator('tags')
    def validate_tags(cls, v):
        if v is not None:
            if len(v) > 10:
                raise ValueError('タグは10個以内である必要があります')
            for tag in v:
                if len(tag) > 50:
                    raise ValueError('各タグは50文字以内である必要があります')
        return v


class ContentInDB(ContentBase):
    id: str
    tenant_id: str
    file_name: str
    file_size: int
    status: FileStatus
    uploaded_at: datetime
    indexed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class Content(ContentInDB):
    pass


class ContentWithChunks(Content):
    chunks: List[Dict[str, Any]] = []
    chunk_count: int = 0
    
    class Config:
        from_attributes = True


class ChunkBase(BaseModel):
    content: str
    metadata: Dict[str, Any] = {}
    
    @validator('content')
    def validate_content(cls, v):
        if len(v) < 10:
            raise ValueError('チャンク内容は10文字以上である必要があります')
        if len(v) > 10000:
            raise ValueError('チャンク内容は10000文字以内である必要があります')
        return v.strip()


class ChunkCreate(ChunkBase):
    file_id: str
    chunk_index: int
    
    @validator('chunk_index')
    def validate_chunk_index(cls, v):
        if v < 0:
            raise ValueError('チャンクインデックスは0以上である必要があります')
        return v


class ChunkUpdate(BaseModel):
    content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    @validator('content')
    def validate_content(cls, v):
        if v is not None:
            if len(v) < 10:
                raise ValueError('チャンク内容は10文字以上である必要があります')
            if len(v) > 10000:
                raise ValueError('チャンク内容は10000文字以内である必要があります')
        return v.strip() if v else v


class ChunkInDB(ChunkBase):
    id: str
    file_id: str
    tenant_id: str
    chunk_index: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class Chunk(ChunkInDB):
    pass


class IndexingJobBase(BaseModel):
    file_id: str
    status: str = "QUEUED"
    progress: int = 0
    error_message: Optional[str] = None


class IndexingJobCreate(IndexingJobBase):
    pass


class IndexingJobUpdate(BaseModel):
    status: Optional[str] = None
    progress: Optional[int] = None
    error_message: Optional[str] = None
    
    @validator('progress')
    def validate_progress(cls, v):
        if v is not None and (v < 0 or v > 100):
            raise ValueError('進捗は0-100の範囲である必要があります')
        return v


class IndexingJobInDB(IndexingJobBase):
    id: str
    tenant_id: str
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class IndexingJob(IndexingJobInDB):
    pass


class ContentSearchParams(BaseModel):
    query: str
    file_types: Optional[List[FileType]] = None
    tags: Optional[List[str]] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    limit: int = 20
    offset: int = 0
    
    @validator('query')
    def validate_query(cls, v):
        if len(v) < 1:
            raise ValueError('検索クエリは必須です')
        if len(v) > 500:
            raise ValueError('検索クエリは500文字以内である必要があります')
        return v.strip()
    
    @validator('limit')
    def validate_limit(cls, v):
        if v < 1 or v > 100:
            raise ValueError('取得件数は1-100の範囲である必要があります')
        return v
    
    @validator('offset')
    def validate_offset(cls, v):
        if v < 0:
            raise ValueError('オフセットは0以上である必要があります')
        return v


class ContentSearchResult(BaseModel):
    id: str
    title: str
    content_type: FileType
    description: Optional[str]
    tags: List[str]
    relevance_score: float
    snippet: str
    created_at: datetime
    
    class Config:
        from_attributes = True
