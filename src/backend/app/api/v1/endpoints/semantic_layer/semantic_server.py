from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Query, Depends

from app.api.v1.deps import verify_api_key
from app.schemas.client.semantic_layer.semantic_server import SemanticServerCreate, SemanticServerResponse
from app.services.client.semantic_layer.semantic_server import ClientSemanticServerService

router = APIRouter(prefix="/admin/semantic-servers", tags=["semantic-server"])


@router.post("", response_model=SemanticServerResponse)
async def create_semantic_server(data: SemanticServerCreate, api_key=Depends(verify_api_key)):
    """Create a new semantic server configuration"""
    try:
        semantic_server_service = ClientSemanticServerService()
        server = semantic_server_service.create_semantic_server(
            server_name=data.server_name,
            engine_type=data.engine_type,
            semantic_config=data.semantic_config,
            client_id=data.client_id,
            is_default=data.is_default,
        )
        return SemanticServerResponse.model_validate(server.to_serializable_dict())
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("", response_model=List[SemanticServerResponse])
async def list_semantic_servers(
    client_id: Optional[str] = None,
    include_inactive: bool = False,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, le=100),
    api_key=Depends(verify_api_key),
):
    """List semantic servers with optional filtering"""
    try:
        semantic_server_service = ClientSemanticServerService()
        servers = semantic_server_service.list_semantic_servers(
            client_id=client_id, skip=skip, limit=limit, include_inactive=include_inactive
        )

        return [SemanticServerResponse.model_validate(server.to_serializable_dict()) for server in servers]
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{server_id}", response_model=SemanticServerResponse)
async def get_semantic_server(
    server_id: str,
    api_key=Depends(verify_api_key),
):
    """Get semantic server configuration by ID"""
    try:
        semantic_server_service = ClientSemanticServerService()
        server = semantic_server_service.get_semantic_server(server_id)
        if not server:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Semantic server not found")
        return SemanticServerResponse.model_validate(server.to_serializable_dict())
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
