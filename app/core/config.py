from functools import lru_cache
from typing import List
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application Settings - Loaded from environment variables
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Application
    APP_NAME: str
    APP_VERSION: str
    ENVIRONMENT: str
    DEBUG: bool
    LOG_LEVEL: str

    # Server
    HOST: str
    PORT: int
    RELOAD: bool = True

    # Postgree Database
    DATABASE_URL: str
    DB_ECHO: bool
    DB_POOL_SIZE: int
    DB_MAX_OVERFLOW: int

    # Authentication
    AUTH_ENABLED: bool
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    # IAM Service
    IAM_SERVICE_URL: str
    IAM_SERVICE_VERSION: str
    IAM_SERVICE_TIMEOUT: int

    # IAM Service Authentication
    IAM_CLIENT_ID: str
    IAM_CLIENT_SECRET: str

    # LLM Configuration
    LLM_PROVIDER: str
    LLM_BASE_URL: str
    LLM_API_KEY: str
    LLM_MODEL: str
    LLM_TEMPERATURE: float
    LLM_MAX_TOKENS: int
    LLM_TIMEOUT: int

    # ChromaDB
    CHROMA_MODE: str
    CHROMA_HOST: str
    CHROMA_PORT: int
    CHROMA_PERSIST_DIRECTORY: str

    # Embeddings
    EMBEDDING_MODEL: str
    EMBEDDING_DIMENSION: int
    EMBEDDING_DEVICE: str

    # Document Processing
    DOCUMENTS_STORAGE_PATH: str
    MAX_UPLOAD_SIZE_MB: int
    ALLOWED_EXTENSIONS: str
    CHUNK_SIZE: int
    CHUNK_OVERLAP: int
    SEPARATORS: str = '["\n\n", "\n", " ", ""]'

    # Retrieval
    TOP_K_RETRIEVAL: int
    BM25_WEIGHT: float
    VECTOR_WEIGHT: float
    MIN_RELEVANCE_SCORE: float

    # Agent
    AGENT_TYPE: str
    MAX_AGENT_ITERATIONS: int
    AGENT_VERBOSE: bool
    ENABLE_STREAMING: bool

    # Chat
    MAX_HISTORY_MESSAGES: int
    SESSION_TIMEOUT_HOURS: int
    AUTO_TITLE_GENERATION: bool

    # Tools
    TOOLS_DIRECTORY: str
    ENABLE_DYNAMIC_TOOLS: bool
    TOOLS_TIMEOUT: int

    # MLflow
    MLFLOW_TRACKING_URI: str
    MLFLOW_EXPERIMENT_NAME: str
    MLFLOW_ENABLE_TRACKING: bool

    # Redis
    REDIS_URL: str
    REDIS_ENABLED: bool

    # Celery
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str
    CELERY_ENABLED: bool

    # CORS
    CORS_ORIGINS: List[str]
    CORS_ALLOW_CREDENTIALS: bool
    CORS_ALLOW_METHODS: List[str]
    CORS_ALLOW_HEADERS: List[str]

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool
    RATE_LIMIT_REQUESTS: int
    RATE_LIMIT_PERIOD: int

    # Logging
    LOG_FORMAT: str
    LOG_FILE: str
    LOG_ROTATION: str
    LOG_RETENTION: str
    LOG_PRIVACY_LEVEL: str 

    # Feature Flags
    ENABLE_RAG: bool
    ENABLE_TOOLS: bool
    ENABLE_MULTI_TURN: bool
    ENABLE_FEEDBACK: bool

    # Performance
    WORKERS: int
    BATCH_SIZE: int
    MAX_CONCURRENT_REQUESTS: int

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @property
    def allowed_extensions_list(self) -> List[str]:
        """Get allowed file extensions as list"""
        return [ext.strip() for ext in self.ALLOWED_EXTENSIONS.split(",")]

    @property
    def max_upload_size_bytes(self) -> int:
        """Get max upload size in bytes"""
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance
    """
    return Settings()


# Global settings instance
settings = get_settings()
