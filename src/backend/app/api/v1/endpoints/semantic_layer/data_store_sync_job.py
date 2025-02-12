from typing import List
from fastapi import APIRouter, HTTPException, status, Query

from app.services.client.semantic_layer.data_store_sync import DataStoreSyncJobService
from app.services.client.semantic_layer.semantic_layer import ClientSemanticLayerService
from app.schemas.client.semantic_layer.data_store_sync import DataStoreResponse, DataStoreSyncStatus
from app.utils.logger import get_logger
from app.tasks.semantic_layer import trigger_sync_job

logger = get_logger(__name__)

router = APIRouter(prefix="/clients/{client_id}/semantic-layers/{layer_id}/data-stores", tags=["sync-jobs"])


@router.get("", response_model=List[DataStoreResponse])
async def list_data_stores(
    client_id: str, layer_id: str, skip: int = Query(default=0, ge=0), limit: int = Query(default=50, le=100)
):
    """
    List data stores associated with a semantic layer
    Returns data stores with their sync status
    """
    try:
        # Get semantic layer data stores
        semantic_layer_service = ClientSemanticLayerService()
        sync_job_service = DataStoreSyncJobService()
        data_stores = semantic_layer_service.list_data_stores(semantic_layer_id=layer_id, skip=skip, limit=limit)

        # Enhance with sync status
        data_store_responses = []
        for data_store in data_stores:
            # Get latest sync job
            latest_job = sync_job_service.get_latest_job_for_pair(
                semantic_layer_id=layer_id, data_store_id=str(data_store.id)
            )

            # Check if can requeue
            can_requeue = sync_job_service.can_requeue_job(
                semantic_layer_id=layer_id, data_store_id=str(data_store.id)
            )

            # Create sync status
            sync_status = DataStoreSyncStatus(
                latest_job_id=str(latest_job.id) if latest_job else None,
                latest_sync_status=latest_job.status if latest_job else None,
                latest_sync_at=latest_job.created_at if latest_job else None,
                can_requeue=can_requeue,
                logs=latest_job.logs if latest_job else [],
            )

            # Create response
            response = DataStoreResponse(
                id=str(data_store.id),
                engine_type=data_store.engine_type,
                is_active=data_store.is_active,
                created_at=data_store.created_at,
                updated_at=data_store.updated_at,
                sync_status=sync_status,
            )
            data_store_responses.append(response)

        return data_store_responses

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error("Error listing data stores", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{data_store_id}/sync")
async def sync_data_store(client_id: str, layer_id: str, data_store_id: str):
    """
    Sync data store schema with semantic layer.
    Creates new sync job and triggers the sync process.
    """
    try:
        # Create sync job
        sync_job_service = DataStoreSyncJobService()
        job = sync_job_service.create_sync_job(semantic_layer_id=layer_id, data_store_id=data_store_id)

        # Trigger async job
        trigger_sync_job.delay(str(job.id))

        return {"message": "Sync job created and triggered successfully", "job_id": str(job.id)}

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error("Error triggering sync job", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{data_store_id}", response_model=DataStoreResponse)
async def get_data_store(client_id: str, layer_id: str, data_store_id: str):
    """
    List data stores associated with a semantic layer
    Returns data stores with their sync status
    """
    try:
        # Get semantic layer data stores
        semantic_layer_service = ClientSemanticLayerService()
        sync_job_service = DataStoreSyncJobService()
        data_store = semantic_layer_service.get_data_store(semantic_layer_id=layer_id, data_store_id=data_store_id)

        # Get latest sync job
        latest_job = sync_job_service.get_latest_job_for_pair(
            semantic_layer_id=layer_id, data_store_id=str(data_store.id)
        )

        # Check if can requeue
        can_requeue = sync_job_service.can_requeue_job(semantic_layer_id=layer_id, data_store_id=str(data_store.id))

        # Create sync status
        sync_status = DataStoreSyncStatus(
            latest_job_id=str(latest_job.id) if latest_job else None,
            latest_sync_status=latest_job.status if latest_job else None,
            latest_sync_at=latest_job.created_at if latest_job else None,
            can_requeue=can_requeue,
            logs=latest_job.logs if latest_job else [],
        )

        # Create response
        response = DataStoreResponse(
            id=str(data_store.id),
            engine_type=data_store.engine_type,
            is_active=data_store.is_active,
            created_at=data_store.created_at,
            updated_at=data_store.updated_at,
            sync_status=sync_status,
        )

        return response

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error("Error listing data stores", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
