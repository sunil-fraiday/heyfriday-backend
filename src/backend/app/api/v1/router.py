from fastapi import APIRouter

from ga_sql import router as ga_sql_router

v1_router = APIRouter(prefix="/api/v1")

v1_router.include_router(ga_sql_router)
