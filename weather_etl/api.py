from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.security import HTTPBearer
import asyncio
from datetime import datetime
from pydantic import BaseModel
from .pipeline import run_etl_async
from .security import rate_limiter, security_manager
from .monitoring import api_requests
import structlog

logger = structlog.get_logger()
app = FastAPI(title="Weather ETL API", version="1.0.0")
security = HTTPBearer()

class ETLRequest(BaseModel):
    cities: list[str] = None
    start_date: str = None
    end_date: str = None

class ETLResponse(BaseModel):
    job_id: str
    status: str
    message: str

@app.middleware("http")
async def rate_limit_middleware(request, call_next):
    client_ip = request.client.host
    if not rate_limiter.is_allowed(client_ip):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    api_requests.labels(endpoint=request.url.path, method=request.method).inc()
    response = await call_next(request)
    return response

@app.post("/etl/run", response_model=ETLResponse)
async def trigger_etl(
    request: ETLRequest,
    background_tasks: BackgroundTasks,
    token: str = Depends(security)
):
    """Trigger ETL pipeline execution"""
    job_id = f"job_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    
    security_manager.audit_log("etl_trigger", "api_user", f"job_{job_id}")
    
    background_tasks.add_task(run_etl_async, job_id, request.cities)
    
    logger.info("etl_job_triggered", job_id=job_id)
    
    return ETLResponse(
        job_id=job_id,
        status="started",
        message="ETL pipeline execution started"
    )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow()}

@app.get("/metrics")
async def get_metrics():
    """Get pipeline metrics"""
    # This should return Prometheus Metrics
    return {"message": "Metrics available at /metrics endpoint"}

if __name__ == "__main__":
    import uvicorn
    from .config import settings
    uvicorn.run(app, host=settings.API_HOST, port=settings.API_PORT)