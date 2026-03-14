"""
VikasGPT Backend API
Rural AI Assistant for Health, Agriculture, and Livelihood

AI for Bharat Hackathon 2026
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import get_settings
from app.routers import household, mandi, health, pest, voice, whatsapp, chat
from app.db.memory import init_demo_data

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown"""
    # Startup
    print("🌿 Starting VikasGPT Backend...")
    init_demo_data()
    print("✅ Demo data initialized")
    yield
    # Shutdown
    print("👋 Shutting down VikasGPT Backend...")


# Create FastAPI app
app = FastAPI(
    title="VikasGPT API",
    description="""
    ## 🌿 VikasGPT: Rural AI Assistant
    
    AI-powered conversational OS for rural Indian households.
    
    ### Features:
    - **Health Triage**: Symptom assessment with ICMR guidelines
    - **Mandi Advisor**: Compare crop prices across markets
    - **Pest Vision**: AI-powered crop disease detection
    - **Household Management**: Family profile and context
    
    ### Tech Stack:
    - Amazon Bedrock (Claude Sonnet + Haiku)
    - Sarvam API (Indian-language speech)
    - FastAPI + SSE Streaming
    
    ### AI for Bharat Hackathon 2026
    """,
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
origins = settings.cors_origins.split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers under /api/v1
app.include_router(household.router, prefix="/api/v1")
app.include_router(mandi.router, prefix="/api/v1")
app.include_router(health.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(pest.router, prefix="/api/v1")
app.include_router(voice.router, prefix="/api/v1")
app.include_router(whatsapp.router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "app": "VikasGPT",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.get("/api/v1")
async def api_root():
    """API v1 root"""
    return {
        "version": "v1",
        "endpoints": {
            "household": "/api/v1/household",
            "mandi": "/api/v1/mandi",
            "health": "/api/v1/health",
            "chat": "/api/v1/chat",
            "pest": "/api/v1/pest",
        },
    }


# Run with: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
