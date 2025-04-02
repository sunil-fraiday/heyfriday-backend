from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
import time

from app.core.config import settings
from app.api.v1.router import api_v1_router
from app.db.mongodb_utils import connect_to_db, disconnect_from_db
from app.services.metrics import init_app_info, MetricsService

app = FastAPI(title=settings.PROJECT_NAME, version=settings.VERSION, openapi_url=f"/openapi.json")

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """Middleware to track request metrics"""
    path = request.url.path
    method = request.method
    
    # Start tracking request
    start_time = MetricsService.track_request_start(method, path)
    
    # Process the request
    response = await call_next(request)
    
    # End tracking request
    MetricsService.track_request_end(start_time, method, path, response.status_code)
    
    return response

async def startup_event():
    """Initialize application on startup"""
    # Connect to database
    connect_to_db()
    
    # Initialize metrics
    init_app_info(settings.VERSION, settings.PROJECT_NAME)


app.add_event_handler("startup", startup_event)
app.add_event_handler("shutdown", disconnect_from_db)

app.include_router(api_v1_router)
