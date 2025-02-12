from typing import Dict
import traceback
from celery import shared_task

from app.services.client.semantic_layer.data_store_sync import DataStoreSyncJobService
from app.services.client.semantic_layer.github import GitHubService
from app.services.client.semantic_layer.schema.generator import get_schema_generator
from app.utils.logger import get_logger

logger = get_logger(__name__)


@shared_task(bind=True)
def trigger_sync_job(self, job_id: str):
    """Process data store sync job"""
    try:
        # Start the job
        sync_job_service = DataStoreSyncJobService()
        github_service = GitHubService()

        job = sync_job_service.start_job(job_id)
        semantic_layer_data_store = job.client_semantic_layer_data_store
        data_store = semantic_layer_data_store.client_data_store
        semantic_layer = semantic_layer_data_store.client_semantic_layer

        job.add_log(f"Reading schema from {data_store.engine_type} data store")

        # Get schema generator
        generator = get_schema_generator(data_store)

        # Generate schema files
        try:
            generated_files = generator.generate_schema_files()

            # Create schema directory in repository
            base_path = f"{semantic_layer.repository_folder}/data_stores/{str(data_store.id)}/schema"
            github_service.create_folder(repository=semantic_layer.client_repository, folder_path=base_path)

            # Write files to repository
            for file_name, content in generated_files.items():
                file_path = f"{base_path}/{file_name}"
                github_service.write_file(
                    repository=semantic_layer.client_repository,
                    file_path=file_path,
                    content=content,
                    commit_message=f"Add cube schema for {file_name}",
                )

                job.add_log(f"Generated and committed schema for: {file_name}")

            # Mark job as completed
            sync_job_service.complete_job(job_id)

        except Exception as e:
            logger.error(f"Error processing sync job {job_id}", exc_info=True)
            error_message = f"Error generating schemas: {str(e)}" + traceback.format_exc()
            job.add_log(error_message)
            raise

    except Exception as e:
        logger.error(f"Error processing sync job {job_id}", exc_info=True)
        sync_job_service.fail_job(job_id, str(e))
        raise
