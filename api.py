"""
Gematria REST API
Provides endpoints for Hebrew gematria calculations and lookups.
"""
from contextlib import asynccontextmanager
from typing import List
from urllib.parse import quote_plus
import os

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator, ConfigDict
from sqlalchemy import create_engine, Column, BigInteger, Text, Integer, Index
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import gematria calculation functions
from backend import get_gematria, _normalize

# ============================================================================
# Configuration
# ============================================================================
def get_database_url() -> str:
    """Construct database URL from environment variables."""
    db_username = os.getenv("DB_USERNAME", "user")
    db_password = os.getenv("DB_PASSWORD", "password")
    db_endpoint = os.getenv("DB_ENDPOINT", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "gematria_db")

    # URL-encode password to handle special characters
    encoded_password = quote_plus(db_password)

    return f"postgresql://{db_username}:{encoded_password}@{db_endpoint}:{db_port}/{db_name}"

DATABASE_URL = get_database_url()

# ============================================================================
# Database Models
# ============================================================================
Base = declarative_base()

class GematriaWord(Base):
    __tablename__ = "gematria_words"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    text = Column(Text, nullable=False)
    normalized = Column(Text, nullable=False, unique=True)
    gematria = Column(Integer, nullable=False)
    created_at = Column(Text, nullable=False)

    __table_args__ = (
        Index('idx_gematria_words_gematria_desc', 'gematria'),
        Index('idx_gematria_words_created_at_desc', 'created_at'),
    )

# ============================================================================
# Database Setup
# ============================================================================
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Dependency for database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ============================================================================
# Pydantic Models (Request/Response)
# ============================================================================
class WordRequest(BaseModel):
    word: str = Field(..., min_length=1, description="Hebrew word to calculate gematria for")

    @field_validator('word')
    @classmethod
    def validate_hebrew(cls, v: str) -> str:
        """Ensure the word contains Hebrew characters."""
        normalized = _normalize(v)
        if not normalized:
            raise ValueError("Word must contain at least one Hebrew character")
        return v

class GematriaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    word: str
    normalized: str
    gematria: int

class TopWordsRequest(BaseModel):
    gematria: int = Field(..., ge=0, description="Gematria value to search for")
    limit: int = Field(10, ge=1, le=100, description="Number of results to return (max 100)")

class TopWordsResponse(BaseModel):
    gematria: int
    count: int
    words: List[GematriaResponse]

# ============================================================================
# Lifespan Event Handler
# ============================================================================
@asynccontextmanager
async def lifespan(application: FastAPI):
    """Manage application lifespan events."""
    # Startup
    print(f"🔗 Connecting to database...")
    print(f"   Endpoint: {os.getenv('DB_ENDPOINT', 'NOT SET')}")
    print(f"   Database: {os.getenv('DB_NAME', 'NOT SET')}")

    try:
        Base.metadata.create_all(bind=engine)
        print("✓ Database tables initialized")
        print("✓ Gematria API ready (Mispar Gadol method)")
    except Exception as e:
        print(f"✗ Database initialization failed: {e}")
        print("⚠️  API will start but database operations will fail")

    yield

    # Shutdown (if needed)
    print("Shutting down...")

# ============================================================================
# FastAPI Application
# ============================================================================
app = FastAPI(
    title="Hebrew Gematria API",
    description="Calculate and query Hebrew gematria values using Mispar Gadol method",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for web app access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# API Endpoints
# ============================================================================
@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Hebrew Gematria API",
        "version": "1.0.0",
        "method": "Mispar Gadol"
    }

@app.post("/gematria/calculate", response_model=GematriaResponse, tags=["Gematria"])
async def calculate_gematria(request: WordRequest):
    """
    Calculate gematria for a Hebrew word.

    - **word**: Hebrew word to calculate (nikud will be removed)

    Returns the word, its normalized form, and gematria value.
    Does not store the word in the database.
    """
    normalized = _normalize(request.word)
    gematria_value = get_gematria(request.word)

    return GematriaResponse(
        word=request.word,
        normalized=normalized,
        gematria=gematria_value
    )

@app.post("/gematria/top", response_model=TopWordsResponse, tags=["Gematria"])
async def get_top_words(request: TopWordsRequest, db: Session = Depends(get_db)):
    """
    Get top N words with a specific gematria value.

    - **gematria**: The gematria value to search for
    - **limit**: Number of results to return (1-100, default 10)

    Returns words ordered by creation date (most recent first).
    """
    words = db.query(GematriaWord).filter(
        GematriaWord.gematria == request.gematria
    ).order_by(
        GematriaWord.created_at.desc()
    ).limit(request.limit).all()

    total_count = db.query(GematriaWord).filter(
        GematriaWord.gematria == request.gematria
    ).count()

    return TopWordsResponse(
        gematria=request.gematria,
        count=total_count,
        words=[
            GematriaResponse(
                word=w.text,
                normalized=w.normalized,
                gematria=w.gematria
            )
            for w in words
        ]
    )

@app.get("/gematria/word/{word}", response_model=GematriaResponse, tags=["Gematria"])
async def get_word_gematria(word: str):
    """
    Get gematria for a specific word (GET alternative to POST /calculate).

    - **word**: Hebrew word to look up
    """
    request = WordRequest(word=word)
    normalized = _normalize(request.word)
    gematria_value = get_gematria(request.word)

    return GematriaResponse(
        word=request.word,
        normalized=normalized,
        gematria=gematria_value
    )

# ============================================================================
# Main Entry Point
# ============================================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)