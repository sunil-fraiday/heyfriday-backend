from fastapi import APIRouter


from app.api.v1.chart import router as chart_router

api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(chart_router)