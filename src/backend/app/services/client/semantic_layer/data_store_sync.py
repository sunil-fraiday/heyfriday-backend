from typing import Optional
from fastapi import HTTPException

from app.models.mongodb.semantic_layer.client_semantic_layer_data_store import (
    ClientSemanticLayerDataStore,
    RelationshipStatus,
)
from app.models.mongodb.semantic_layer.data_store_sync_job import DataStoreSyncJob, SyncJobStatus
from app.models.mongodb.semantic_layer.client_semantic_layer import ClientSemanticLayer
from app.models.mongodb.client_data_store import ClientDataStore
from app.utils.logger import get_logger

logger = get_logger(__name__)


class DataStoreSyncJobService:
    """Service for managing data store sync jobs"""

    def create_sync_job(self, semantic_layer_id: str, data_store_id: str) -> DataStoreSyncJob:
        """Create a new sync job"""
        try:
            relationship = ClientSemanticLayerDataStore.objects.get(
                client_semantic_layer=semantic_layer_id, client_data_store=data_store_id
            )

            # Check for existing pending or in-progress jobs
            existing_job = DataStoreSyncJob.objects(
                client_semantic_layer_data_store=relationship,
                status__in=[SyncJobStatus.PENDING, SyncJobStatus.IN_PROGRESS],
            ).first()

            if existing_job:
                raise ValueError(f"A sync job already exists with status: {existing_job.status}")

            job = DataStoreSyncJob(client_semantic_layer_data_store=relationship, status=SyncJobStatus.PENDING)
            job.save()

            logger.info(f"Created sync job for semantic layer data store: {relationship.client_data_store}")
            return job

        except ClientSemanticLayerDataStore.DoesNotExist:
            logger.error(f"Semantic layer data store not found: {data_store_id}", exc_info=True)
            raise ValueError(f"Relationship not found: {data_store_id}")
        except Exception as e:
            logger.error("Error creating sync job", exc_info=True)
            raise ValueError(str(e))

    def start_job(self, job_id: str) -> DataStoreSyncJob:
        """Start processing a sync job"""
        try:
            job = DataStoreSyncJob.objects.get(id=job_id)

            if job.status != SyncJobStatus.PENDING:
                raise ValueError(f"Job is in {job.status} state, cannot start")

            job.status = SyncJobStatus.IN_PROGRESS
            job.add_log("Starting sync job")
            job.save()

            logger.info(f"Started sync job {job_id}")
            return job

        except DataStoreSyncJob.DoesNotExist:
            logger.error(f"Job not found: {job_id}", exc_info=True)
            raise ValueError(f"Job not found: {job_id}")
        except Exception as e:
            logger.error(f"Error starting job", exc_info=True)
            raise ValueError(str(e))

    def complete_job(self, job_id: str) -> DataStoreSyncJob:
        """Mark a job as completed"""
        try:
            job = DataStoreSyncJob.objects.get(id=job_id)

            if job.status != SyncJobStatus.IN_PROGRESS:
                raise ValueError(f"Job is in {job.status} state, cannot complete")

            job.status = SyncJobStatus.COMPLETED
            job.add_log("Sync job completed successfully")
            job.save()

            # Update relationship last sync time
            relationship = job.client_semantic_layer_data_store
            relationship.last_sync_at = job.updated_at
            relationship.status = RelationshipStatus.ACTIVE
            relationship.save()

            logger.info(f"Completed sync job {job_id}")
            return job

        except DataStoreSyncJob.DoesNotExist:
            logger.error(f"Job not found: {job_id}", exc_info=True)
            raise ValueError(f"Job not found: {job_id}")
        except Exception as e:
            logger.error(f"Error completing job", exc_info=True)
            raise ValueError(str(e))

    def fail_job(self, job_id: str, error_message: str) -> DataStoreSyncJob:
        """Mark a job as failed"""
        try:
            job = DataStoreSyncJob.objects.get(id=job_id)

            job.status = SyncJobStatus.FAILED
            job.error_message = error_message
            job.add_log(f"Job failed: {error_message}")
            job.save()

            # Update relationship error status
            relationship = job.client_semantic_layer_data_store
            relationship.error_message = error_message
            relationship.status = RelationshipStatus.FAILED
            relationship.save()

            logger.error(f"Failed sync job {job_id}: {error_message}")
            return job

        except DataStoreSyncJob.DoesNotExist:
            logger.error(f"Job not found: {job_id}", exc_info=True)
            raise ValueError(f"Job not found: {job_id}")
        except Exception as e:
            logger.error(f"Error marking job as failed", exc_info=True)
            raise ValueError(str(e))

    def get_latest_job(self, semantic_layer_data_store_id: str) -> DataStoreSyncJob:
        """Get the latest sync job for a relationship"""
        try:
            return (
                DataStoreSyncJob.objects(client_semantic_layer_data_store=semantic_layer_data_store_id)
                .order_by("-created_at")
                .first()
            )

        except Exception as e:
            logger.error("Error fetching latest job", exc_info=True)
            raise ValueError(str(e))

    def can_requeue_job(self, semantic_layer_id: str, data_store_id: str) -> bool:
        """Check if data store can be requeued for sync"""
        try:
            # Get the relationship first
            relationship = ClientSemanticLayerDataStore.objects.get(
                client_semantic_layer=semantic_layer_id, client_data_store=data_store_id
            )

            # Get latest job for this relationship
            latest_job = self.get_latest_job(relationship.id)

            # Can requeue if latest job failed and no pending/in-progress jobs exist
            if not latest_job or latest_job.status != SyncJobStatus.FAILED:
                return False

            # Check no pending or in-progress jobs
            existing_job = DataStoreSyncJob.objects(
                client_semantic_layer_data_store=relationship.id,
                status__in=[SyncJobStatus.PENDING, SyncJobStatus.IN_PROGRESS],
            ).first()

            return not existing_job

        except ClientSemanticLayerDataStore.DoesNotExist:
            logger.error(
                f"Relationship not found for semantic layer {semantic_layer_id} and data store {data_store_id}",
                exc_info=True,
            )
            return False
        except Exception as e:
            logger.error("Error checking job requeue status", exc_info=True)
            return False

    def requeue_failed_job(self, semantic_layer_id: str, data_store_id: str) -> Optional[DataStoreSyncJob]:
        """Requeue a failed sync job"""
        try:
            if not self.can_requeue_job(semantic_layer_id, data_store_id):
                raise ValueError("Cannot requeue job. Latest job must be in failed state.")

            # Get the relationship
            relationship = ClientSemanticLayerDataStore.objects.get(
                client_semantic_layer=semantic_layer_id, client_data_store=data_store_id
            )

            # Create new job
            return self.create_sync_job(semantic_layer_data_store_id=relationship.id)

        except ClientSemanticLayerDataStore.DoesNotExist:
            logger.error(
                f"Relationship not found for semantic layer {semantic_layer_id} and data store {data_store_id}",
                exc_info=True,
            )
            raise ValueError("Relationship not found")
        except Exception as e:
            logger.error("Error requeuing job", exc_info=True)
            raise ValueError(str(e))

    def get_latest_job_for_pair(self, semantic_layer_id: str, data_store_id: str) -> Optional[DataStoreSyncJob]:
        """Get the latest sync job for a semantic layer and data store pair"""
        try:
            # Get the relationship first
            relationship = ClientSemanticLayerDataStore.objects.get(
                client_semantic_layer=semantic_layer_id, client_data_store=data_store_id
            )

            return self.get_latest_job(relationship.id)

        except ClientSemanticLayerDataStore.DoesNotExist:
            logger.error(
                f"Relationship not found for semantic layer {semantic_layer_id} and data store {data_store_id}",
                exc_info=True,
            )
            raise ValueError("Relationship not found")
        except Exception as e:
            logger.error("Error fetching latest job", exc_info=True)
            raise ValueError(str(e))
