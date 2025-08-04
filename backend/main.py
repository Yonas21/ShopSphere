from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic_settings import BaseSettings
from database.sql_database import engine, Base
from database.mongodb import connect_to_mongo, close_mongo_connection
from api import users, items, cart, upload, payments
from models import user, item, payment

class Settings(BaseSettings):
    database_url: str
    mongodb_url: str
    mongodb_database: str
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int
    allowed_origins: list
    
    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

settings = Settings()

app = FastAPI(
    title="FastAPI with MongoDB and SQLAlchemy",
    description="A full-stack application with React frontend",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create SQLAlchemy tables
Base.metadata.create_all(bind=engine)

# Include routers
app.include_router(users.router, prefix="/api")
app.include_router(items.router, prefix="/api")
app.include_router(cart.router, prefix="/api")
app.include_router(upload.router, prefix="/api")
app.include_router(payments.router)

@app.on_event("startup")
async def startup_event():
    await connect_to_mongo()

@app.on_event("shutdown")
async def shutdown_event():
    await close_mongo_connection()

@app.get("/")
async def root():
    return {"message": "Hello, FastAPI with MongoDB and SQLAlchemy"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
