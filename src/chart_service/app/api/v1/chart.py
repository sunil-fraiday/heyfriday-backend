from datetime import datetime, timezone
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Depends, Query, Path
from fastapi.responses import StreamingResponse
import io
import logging

from app.models.mongodb.chart import Chart, Identifiers, EntityIdentifier
from app.services.chart.types import get_chart_generator
from app.services.storage.azure import AzureBlobStorage
from app.schemas.chart import ChartRequestSchema, ChartResponseSchema, ChartDetailSchema, ChartListResponseSchema
from app.config import settings

router = APIRouter()

logger = logging.getLogger(__name__)


def get_storage_client():
    return AzureBlobStorage(
        connection_string=settings.AZURE_STORAGE_CONNECTION_STRING, container_name=settings.AZURE_CONTAINER_NAME
    )


@router.post("/charts", response_model=ChartResponseSchema, status_code=201)
async def create_chart(chart_data: ChartRequestSchema):
    """Create a new chart and store it in Azure Blob Storage"""
    try:

        # Extract parameters
        chart_type = chart_data.chart_type
        chart_data_dict = chart_data.data
        options = chart_data.options.model_dump() if chart_data.options else {}
        identifiers = chart_data.identifiers
        expiry_hours = chart_data.expiry_hours or settings.DEFAULT_CHART_EXPIRY_HOURS

        # Generate chart
        chart_generator = get_chart_generator(chart_type)
        chart_bytes = chart_generator.generate(chart_data_dict, options)

        # Upload to Azure Blob Storage
        storage_client = get_storage_client()
        title = options.get("title", "chart").replace(" ", "_")
        filename = f"{chart_type}_{title}_{datetime.now(tz=timezone.utc).strftime('%Y%m%d%H%M%S')}.png"
        blob_name = storage_client.upload_chart(chart_bytes, filename)

        # Generate presigned URL
        presigned_url, expiry_time = storage_client.get_presigned_url(blob_name, expiry_hours)

        # Create chart record in MongoDB
        chart = Chart(
            identifiers=Identifiers(
                service_name=identifiers.service_name,
                entities=[EntityIdentifier(type=entity.type, id=entity.id) for entity in identifiers.entities],
            ),
            chart_type=chart_type,
            blob_name=blob_name,
            presigned_url=presigned_url,
            title=options.get("title"),
            description=options.get("description"),
        )
        chart.save()

        return {"chart_id": str(chart.id), "url": presigned_url, "expiry_date": expiry_time.isoformat()}
    except Exception as e:
        logger.error(f"Error creating chart: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create chart: {str(e)}")


@router.get("/charts", response_model=ChartListResponseSchema)
async def list_charts(
    service_name: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None),
    entity_id: Optional[str] = Query(None),
    chart_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    """List charts with optional filtering"""
    try:
        # Build query
        query = {}

        if service_name:
            query["identifiers.service_name"] = service_name

        if entity_type and entity_id:
            query["identifiers.entities"] = {"$elemMatch": {"type": entity_type, "id": entity_id}}

        if chart_type:
            query["chart_type"] = chart_type

        # Calculate pagination
        skip = (page - 1) * per_page

        # Execute query
        charts = Chart.objects(__raw__=query).order_by("-created_at").skip(skip).limit(per_page)
        total = Chart.objects(__raw__=query).count()

        # Return results
        return {
            "charts": [ChartDetailSchema(**chart.to_dict()) for chart in charts],
            "page": page,
            "per_page": per_page,
            "total": total,
        }

    except Exception as e:
        logger.error(f"Error listing charts: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list charts: {str(e)}")


@router.get("/charts/{chart_id}", response_model=ChartDetailSchema)
async def get_chart(chart_id: str = Path(...)):
    """Get a specific chart by ID with a fresh presigned URL"""
    try:
        # Get the chart by ID
        try:
            chart: Chart = Chart.objects.get(id=chart_id)
        except:
            raise HTTPException(status_code=404, detail="Chart not found")

        storage_client = get_storage_client()
        presigned_url, _ = storage_client.get_presigned_url(chart.blob_name, settings.DEFAULT_CHART_EXPIRY_HOURS)
        chart.presigned_url = presigned_url
        chart.save()

        return chart.to_serializable_dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting chart: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get chart: {str(e)}")


@router.get("/charts/{chart_id}/content")
async def get_chart_content(chart_id: str = Path(...)):
    """Get the actual chart image (as bytes)"""
    try:
        try:
            chart = Chart.objects.get(id=chart_id)
        except:
            raise HTTPException(status_code=404, detail="Chart not found")

        storage_client = get_storage_client()
        chart_bytes = storage_client.read_blob(chart.blob_name)

        return StreamingResponse(io.BytesIO(chart_bytes), media_type="image/png")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting chart content: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get chart content: {str(e)}")
