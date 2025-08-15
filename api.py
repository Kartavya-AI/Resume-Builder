import os
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any
import time
from datetime import datetime
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
import uvicorn

from tool import generate_resume

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class HealthCheck(BaseModel):
    """Response model for health check."""
    status: str = "healthy"
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    version: str = "1.0.0"

class ResumeRequest(BaseModel):
    """Request model for resume generation."""
    user_input: str = Field(
        ...,
        min_length=50,
        max_length=10000,
        description="Raw resume information to be processed",
        example="John Doe, Software Engineer with 5 years experience at Google working on cloud infrastructure..."
    )
    
    @validator('user_input')
    def validate_user_input(cls, v):
        if not v.strip():
            raise ValueError('User input cannot be empty')
        return v.strip()

class ResumeResponse(BaseModel):
    """Response model for resume generation."""
    resume: str = Field(..., description="Generated resume in markdown format")
    processing_time: float = Field(..., description="Time taken to generate resume in seconds")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class ErrorResponse(BaseModel):
    """Response model for errors."""
    error: str = Field(..., description="Error message")
    detail: str = Field(default="", description="Detailed error information")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Resume Generator API...")
    
    # Validate environment variables
    required_env_vars = ["OPENAI_API_KEY"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        raise RuntimeError(f"Missing required environment variables: {missing_vars}")
    
    logger.info("Environment variables validated successfully")
    logger.info("Resume Generator API started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Resume Generator API...")

# Initialize FastAPI app
app = FastAPI(
    title="Resume Generator API",
    description="Professional resume generator using AI to transform raw resume information into polished markdown format",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="Internal server error",
            detail=str(exc)
        ).dict()
    )

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Log request
    logger.info(f"Request: {request.method} {request.url}")
    
    response = await call_next(request)
    
    # Log response
    process_time = time.time() - start_time
    logger.info(f"Response: {response.status_code} - {process_time:.4f}s")
    
    return response

@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Resume Generator API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint."""
    try:
        # Basic environment check
        if not os.getenv("OPENAI_API_KEY"):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="OPENAI_API_KEY environment variable not found"
            )
        
        return HealthCheck()
    
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service unhealthy: {str(e)}"
        )

@app.post("/generate-resume", response_model=ResumeResponse)
async def generate_resume_endpoint(request: ResumeRequest):
    """
    Generate a professional resume from raw user input.
    
    Takes unstructured resume information and transforms it into a polished,
    professional resume in Markdown format using AI.
    """
    start_time = time.time()
    
    try:
        logger.info(f"Generating resume for input of length: {len(request.user_input)}")
        
        # Generate resume using the tool
        resume = generate_resume(request.user_input)
        
        if not resume:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate resume - empty response"
            )
        
        processing_time = time.time() - start_time
        
        logger.info(f"Resume generated successfully in {processing_time:.4f}s")
        
        return ResumeResponse(
            resume=resume,
            processing_time=processing_time
        )
    
    except ValueError as ve:
        logger.error(f"Validation error: {ve}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    
    except Exception as e:
        logger.error(f"Error generating resume: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate resume: {str(e)}"
        )

@app.post("/generate-resume/batch", response_model=Dict[str, Any])
async def generate_resume_batch(requests: list[ResumeRequest]):
    """
    Generate multiple resumes in batch.
    
    Processes multiple resume requests and returns results with individual
    processing times and success/failure status.
    """
    if len(requests) > 10:  # Limit batch size
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Batch size cannot exceed 10 requests"
        )
    
    start_time = time.time()
    results = []
    
    for i, req in enumerate(requests):
        try:
            req_start_time = time.time()
            resume = generate_resume(req.user_input)
            processing_time = time.time() - req_start_time
            
            results.append({
                "index": i,
                "success": True,
                "resume": resume,
                "processing_time": processing_time,
                "error": None
            })
            
        except Exception as e:
            logger.error(f"Error processing batch request {i}: {e}")
            results.append({
                "index": i,
                "success": False,
                "resume": None,
                "processing_time": time.time() - req_start_time,
                "error": str(e)
            })
    
    total_processing_time = time.time() - start_time
    successful_count = sum(1 for r in results if r["success"])
    
    return {
        "total_requests": len(requests),
        "successful_count": successful_count,
        "failed_count": len(requests) - successful_count,
        "total_processing_time": total_processing_time,
        "results": results,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/stats", response_model=Dict[str, Any])
async def get_api_stats():
    """Get basic API statistics."""
    return {
        "status": "operational",
        "uptime": "Available since startup",
        "version": "1.0.0",
        "environment_variables": {
            "OPENAI_API_KEY": "configured" if os.getenv("OPENAI_API_KEY") else "missing",
            "PORT": os.getenv("PORT", "8080")
        },
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info"
    )