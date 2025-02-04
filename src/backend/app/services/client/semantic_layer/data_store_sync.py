from fastapi.exceptions import HTTPException
from fastapi import status

from app.models.mongodb.semantic_layer.data_store_sync_job import DataStoreSyncJob, JobStatus
from app.models.mongodb.semantic_layer.client_semantic_layer import ClientSemanticLayer
from app.models.mongodb.client_data_store import ClientDataStore
from app.utils.logger import get_logger
from app.services.client.semantic_layer.github import GitHubService

logger = get_logger(__name__)


class DataStoreSyncJobService:
    """Service for managing data store sync jobs"""

    def create_sync_job(self, semantic_layer_id: str, data_store_id: str) -> DataStoreSyncJob:
        """Create a new sync job for a data store"""
        try:
            semantic_layer = ClientSemanticLayer.objects.get(id=semantic_layer_id)
            data_store = ClientDataStore.objects.get(id=data_store_id)

            # Validate data store belongs to semantic layer
            if data_store not in semantic_layer.data_stores:
                raise ValueError("Data store is not associated with this semantic layer")

            # Check for existing pending or in-progress jobs
            existing_job = DataStoreSyncJob.objects(
                semantic_layer=semantic_layer,
                data_store=data_store,
                status__in=[JobStatus.PENDING, JobStatus.IN_PROGRESS],
            ).first()

            if existing_job:
                raise ValueError(f"A sync job already exists with status: {existing_job.status}")

            # Create new job
            job = DataStoreSyncJob(
                semantic_layer=semantic_layer,
                data_store=data_store,
                status=JobStatus.PENDING,
            )
            job.save()

            logger.info(f"Created sync job for semantic layer {semantic_layer_id} " f"and data store {data_store_id}")
            return job

        except (ClientSemanticLayer.DoesNotExist, ClientDataStore.DoesNotExist) as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except Exception as e:
            logger.error("Error creating sync job", exc_info=True)
            raise ValueError(str(e))

    def start_job(self, job_id: str) -> DataStoreSyncJob:
        """Start processing a sync job"""
        try:
            job = DataStoreSyncJob.objects.get(id=job_id)

            if job.status != JobStatus.PENDING:
                raise ValueError(f"Job is in {job.status} state, cannot start")

            job.status = JobStatus.IN_PROGRESS
            job.add_log("Starting sync job")
            job.save()

            logger.info(f"Started sync job {job_id}")
            return job

        except DataStoreSyncJob.DoesNotExist:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except Exception as e:
            logger.error(f"Error starting job", exc_info=True)
            raise RuntimeError(str(e))

    def complete_job(self, job_id: str) -> DataStoreSyncJob:
        """Mark a job as completed"""
        try:
            job = DataStoreSyncJob.objects.get(id=job_id)

            if job.status != JobStatus.IN_PROGRESS:
                raise ValueError(f"Job is in {job.status} state, cannot complete")

            job.status = JobStatus.COMPLETED
            job.add_log("Sync job completed successfully")
            job.save()

            logger.info(f"Completed sync job {job_id}")
            return job

        except DataStoreSyncJob.DoesNotExist:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except Exception as e:
            logger.error(f"Error completing job", exc_info=True)
            raise ValueError(str(e))

    def fail_job(self, job_id: str, error_message: str) -> DataStoreSyncJob:
        """Mark a job as failed"""
        try:
            job = DataStoreSyncJob.objects.get(id=job_id)

            job.status = JobStatus.FAILED
            job.add_log(f"Job failed: {error_message}")
            job.save()

            logger.error(f"Failed sync job {job_id}: {error_message}")
            return job

        except DataStoreSyncJob.DoesNotExist:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except Exception as e:
            logger.error(f"Error marking job as failed", exc_info=True)
            raise ValueError(str(e))

    def get_latest_job(self, semantic_layer_id: str, data_store_id: str) -> DataStoreSyncJob:
        """Get the latest sync job for a semantic layer and data store"""
        try:
            return (
                DataStoreSyncJob.objects(semantic_layer=semantic_layer_id, data_store=data_store_id)
                .order_by("-created_at")
                .first()
            )

        except Exception as e:
            logger.error("Error fetching latest job", exc_info=True)
            raise ValueError(str(e))
