from fastapi import FastAPI, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from typing import Optional
import uvicorn

from config import settings
from models.database import connect_to_mongo, close_mongo_connection
from services.docker_sandbox import docker_sandbox
from services.question_service import question_service
from routes import aptitude, code


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    # Startup
    print("Starting up...")
    await connect_to_mongo()
    await docker_sandbox.start_cleanup_task()
    print("Application ready!")

    yield

    # Shutdown
    print("Shutting down...")
    await docker_sandbox.shutdown()
    await close_mongo_connection()
    print("Shutdown complete!")


app = FastAPI(title=settings.API_TITLE, version=settings.API_VERSION, lifespan=lifespan)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(aptitude.router, prefix="/api/v1")
app.include_router(code.router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Sandbox Environment API",
        "version": settings.API_VERSION,
        "modes": ["aptitude", "code"],
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": "now"}


@app.get("/debug/database")
async def debug_database():
    """Debug endpoint to check database connection and contents"""
    from models.database import get_database
    
    try:
        db = get_database()
        
        # Get collection names
        collections = await db.list_collection_names()
        
        # Count documents in dsa_questions
        total_questions = await db.dsa_questions.count_documents({})
        code_questions = await db.dsa_questions.count_documents({"question_type": "code"})
        apti_questions = await db.dsa_questions.count_documents({"question_type": "apti"})
        
        # Sample documents
        sample_code = await db.dsa_questions.find_one({"question_type": "code"})
        sample_apti = await db.dsa_questions.find_one({"question_type": "apti"})
        
        # Get distinct job_ids
        job_ids = await db.dsa_questions.distinct("job_id")
        
        return {
            "database": settings.DATABASE_NAME,
            "mongodb_url": settings.MONGODB_URL[:50] + "...",
            "collections": collections,
            "total_questions": total_questions,
            "code_questions": code_questions,
            "apti_questions": apti_questions,
            "job_ids": job_ids,
            "sample_code_question": {
                "_id": str(sample_code["_id"]) if sample_code and "_id" in sample_code else None,
                "title": sample_code.get("title") if sample_code else None,
                "difficulty": sample_code.get("difficulty") if sample_code else None,
                "job_id": sample_code.get("job_id") if sample_code else None,
            } if sample_code else None,
            "sample_apti_question": {
                "_id": str(sample_apti["_id"]) if sample_apti and "_id" in sample_apti else None,
                "title": sample_apti.get("title") if sample_apti else None,
                "difficulty": sample_apti.get("difficulty") if sample_apti else None,
                "job_id": sample_apti.get("job_id") if sample_apti else None,
            } if sample_apti else None
        }
    except Exception as e:
        return {
            "error": str(e),
            "database": settings.DATABASE_NAME,
            "mongodb_url": settings.MONGODB_URL[:50] + "..."
        }


@app.get("/api/v1/questions/stats")
async def get_question_stats(job_id: Optional[str] = Query(None, description="Filter by job ID")):
    """Get statistics about available questions, optionally filtered by job ID"""
    code_count = await question_service.get_question_count(question_type="code", job_id=job_id)
    apti_count = await question_service.get_question_count(question_type="apti", job_id=job_id)
    
    code_easy = await question_service.get_question_count(question_type="code", difficulty="easy", job_id=job_id)
    code_medium = await question_service.get_question_count(question_type="code", difficulty="medium", job_id=job_id)
    code_hard = await question_service.get_question_count(question_type="code", difficulty="hard", job_id=job_id)
    
    apti_easy = await question_service.get_question_count(question_type="apti", difficulty="easy", job_id=job_id)
    apti_medium = await question_service.get_question_count(question_type="apti", difficulty="medium", job_id=job_id)
    apti_hard = await question_service.get_question_count(question_type="apti", difficulty="hard", job_id=job_id)
    
    result = {
        "total_questions": code_count + apti_count,
        "code_questions": {
            "total": code_count,
            "easy": code_easy,
            "medium": code_medium,
            "hard": code_hard
        },
        "aptitude_questions": {
            "total": apti_count,
            "easy": apti_easy,
            "medium": apti_medium,
            "hard": apti_hard
        }
    }
    
    if job_id:
        result["job_id"] = job_id
    
    return result


@app.get("/api/v1/questions/job-ids")
async def get_available_job_ids():
    """Get list of all available job IDs that have questions"""
    job_ids = await question_service.get_available_job_ids()
    
    # Get count for each job ID
    job_id_stats = []
    for job_id in job_ids:
        code_count = await question_service.get_question_count(question_type="code", job_id=job_id)
        apti_count = await question_service.get_question_count(question_type="apti", job_id=job_id)
        job_id_stats.append({
            "job_id": job_id,
            "total_questions": code_count + apti_count,
            "code_questions": code_count,
            "aptitude_questions": apti_count
        })
    
    return {
        "total_job_ids": len(job_ids),
        "job_ids": job_id_stats
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.DEBUG else "An error occurred",
        },
    )


if __name__ == "__main__":
    import os
    port = int(os.getenv("PORT", 8082))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=settings.DEBUG)
