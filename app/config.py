import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings"""
    
    # Database settings
    DATABASE_URL: str = "sqlite:///./meeting_summarizer.db"
    POSTGRES_HOST: Optional[str] = None
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: Optional[str] = None
    POSTGRES_PASSWORD: Optional[str] = None
    POSTGRES_DB: Optional[str] = None
    
    # NLP Model settings
    SUMMARIZATION_MODEL: str = "facebook/bart-large-cnn"
    SENTIMENT_MODEL: str = "cardiffnlp/twitter-roberta-base-sentiment-latest"
    NER_MODEL: str = "dbmdz/bert-large-cased-finetuned-conll03-english"
    
    # API settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = True
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    
    # Optional integrations
    SLACK_WEBHOOK_URL: Optional[str] = None
    EMAIL_SMTP_HOST: Optional[str] = None
    EMAIL_SMTP_PORT: int = 587
    EMAIL_USERNAME: Optional[str] = None
    EMAIL_PASSWORD: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True

    def get_database_url(self) -> str:
        """Get the appropriate database URL based on configuration"""
        if self.POSTGRES_HOST:
            return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        return self.DATABASE_URL

# Create settings instance
settings = Settings()
