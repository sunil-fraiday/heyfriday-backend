from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api.v1.router import api_v1_router
from app.db.mongodb_utils import connect_to_db, disconnect_from_db

app = FastAPI(title=settings.APP_NAME, openapi_url=f"/openapi.json")

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_event_handler("startup", connect_to_db)
app.add_event_handler("shutdown", disconnect_from_db)

app.include_router(api_v1_router)
