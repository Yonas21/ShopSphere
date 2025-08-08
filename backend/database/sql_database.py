from sqlalchemy import create_engine, event, pool
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
import os
import logging
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from typing import Optional

load_dotenv()
logger = logging.getLogger("app.database")

class DatabaseSettings(BaseSettings):
    # Primary database URL
    database_url: str = "sqlite:///./app.db"
    
    # PostgreSQL specific settings
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "fastapi_user"
    postgres_password: str = "your_password"
    postgres_db: str = "fastapi_ecommerce"
    
    # Connection pool settings
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 3600  # 1 hour
    
    # Performance settings
    echo_sql: bool = False  # Set to True for SQL debugging
    
    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        extra = 'ignore'

settings = DatabaseSettings()

def get_database_url() -> str:
    """
    Get the appropriate database URL based on environment
    """
    # If DATABASE_URL is explicitly set, use it
    if settings.database_url != "sqlite:///./app.db":
        return settings.database_url
    
    # Check if PostgreSQL connection details are provided
    if (settings.postgres_password != "your_password" and 
        settings.postgres_user != "fastapi_user"):
        postgres_url = (
            f"postgresql://{settings.postgres_user}:{settings.postgres_password}"
            f"@{settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}"
        )
        logger.info(f"Using PostgreSQL database: {settings.postgres_host}:{settings.postgres_port}")
        return postgres_url
    
    # Fallback to SQLite
    logger.info("Using SQLite database (development mode)")
    return settings.database_url

SQLALCHEMY_DATABASE_URL = get_database_url()

def create_database_engine():
    """
    Create database engine with appropriate configuration
    """
    if "postgresql" in SQLALCHEMY_DATABASE_URL:
        # PostgreSQL configuration
        engine = create_engine(
            SQLALCHEMY_DATABASE_URL,
            poolclass=QueuePool,
            pool_size=settings.pool_size,
            max_overflow=settings.max_overflow,
            pool_timeout=settings.pool_timeout,
            pool_recycle=settings.pool_recycle,
            pool_pre_ping=True,  # Verify connections before use
            echo=settings.echo_sql,
            future=True,
        )
        logger.info("PostgreSQL engine created with connection pooling")
        
    elif "mysql" in SQLALCHEMY_DATABASE_URL:
        # MySQL configuration
        engine = create_engine(
            SQLALCHEMY_DATABASE_URL,
            poolclass=QueuePool,
            pool_size=settings.pool_size,
            max_overflow=settings.max_overflow,
            pool_timeout=settings.pool_timeout,
            pool_recycle=settings.pool_recycle,
            pool_pre_ping=True,
            echo=settings.echo_sql,
            future=True,
        )
        logger.info("MySQL engine created with connection pooling")
        
    else:
        # SQLite configuration
        engine = create_engine(
            SQLALCHEMY_DATABASE_URL,
            connect_args={"check_same_thread": False},
            echo=settings.echo_sql,
            future=True,
        )
        logger.info("SQLite engine created (development mode)")
    
    return engine

# Create the engine
engine = create_database_engine()

# Add connection event listeners for logging
@event.listens_for(engine, "connect")
def receive_connect(dbapi_connection, connection_record):
    logger.info("Database connection established")

@event.listens_for(engine, "checkout")
def receive_checkout(dbapi_connection, connection_record, connection_proxy):
    logger.debug("Database connection checked out from pool")

@event.listens_for(engine, "checkin")
def receive_checkin(dbapi_connection, connection_record):
    logger.debug("Database connection returned to pool")

# Session configuration
SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine,
    expire_on_commit=False  # Keep objects accessible after commit
)

Base = declarative_base()

def get_db():
    """
    Database dependency with proper connection handling
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def get_db_info():
    """
    Get database connection information
    """
    info = {
        "database_url": SQLALCHEMY_DATABASE_URL.split("://")[0] + "://***",  # Hide credentials
        "pool_size": settings.pool_size if "postgresql" in SQLALCHEMY_DATABASE_URL else None,
        "max_overflow": settings.max_overflow if "postgresql" in SQLALCHEMY_DATABASE_URL else None,
    }
    
    if "postgresql" in SQLALCHEMY_DATABASE_URL:
        pool = engine.pool
        info.update({
            "pool_checked_in": pool.checkedin(),
            "pool_checked_out": pool.checkedout(),
            "pool_overflow": pool.overflow(),
        })
    
    return info
