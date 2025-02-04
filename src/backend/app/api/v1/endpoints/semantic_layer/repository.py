from typing import Optional, List

from fastapi import APIRouter, HTTPException, status, Query, Depends
from app.schemas.client.semantic_layer.repository import RepositoryCreate, RepositoryResponse
from app.services.client.semantic_layer.repository import ClientRepositoryService
from app.api.v1.deps import verify_api_key

router = APIRouter(prefix="/admin/repositories", tags=["repository"])


@router.post("", response_model=RepositoryResponse)
async def create_repository(data: RepositoryCreate, api_key=Depends(verify_api_key)):
    """Create a new repository configuration"""
    try:
        repository_service = ClientRepositoryService()
        repository = repository_service.create_repository(
            repository_config=data.repository_config, client_id=data.client_id, is_default=data.is_default
        )
        return RepositoryResponse.model_validate(repository.to_serializable_dict())
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException as e:
        raise e


@router.get("", response_model=List[RepositoryResponse])
async def list_repositories(
    client_id: Optional[str] = None,
    include_inactive: bool = False,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, le=100),
    api_key=Depends(verify_api_key),
):
    """List repositories with optional filtering"""
    try:
        repository_service = ClientRepositoryService()
        repositories = repository_service.list_repositories(
            client_id=client_id, skip=skip, limit=limit, include_inactive=include_inactive
        )

        return [RepositoryResponse.model_validate(repository.to_serializable_dict()) for repository in repositories]
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{repository_id}", response_model=RepositoryResponse)
async def get_repository(repository_id: str, api_key=Depends(verify_api_key)):
    """Get repository configuration by ID"""
    try:
        repository_service = ClientRepositoryService()
        repository = repository_service.get_repository(repository_id)
        if not repository:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found")
        return RepositoryResponse.model_validate(repository.to_serializable_dict())
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
