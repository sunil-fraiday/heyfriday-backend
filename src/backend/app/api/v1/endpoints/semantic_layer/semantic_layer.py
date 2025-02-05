from fastapi import APIRouter, HTTPException, status, Query
from typing import Optional, List
from app.schemas.client.semantic_layer.semantic_layer import (
    SemanticLayerCreate,
    SemanticLayerResponse,
)
from app.services.client.semantic_layer.semantic_layer import ClientSemanticLayerService

router = APIRouter(prefix="/clients/{client_id}/semantic-layers", tags=["semantic-layer"])


@router.post("", response_model=SemanticLayerResponse)
async def create_semantic_layer(client_id: str):
    """Create a new semantic layer"""
    try:
        semantic_layer_service = ClientSemanticLayerService()
        layer = semantic_layer_service.create_semantic_layer(client_id=client_id)
        return SemanticLayerResponse.from_db_model(layer)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("", response_model=List[SemanticLayerResponse])
async def list_semantic_layers(
    client_id: str, skip: int = Query(default=0, ge=0), limit: int = Query(default=50, le=100)
):
    """List semantic layers with optional filtering"""
    try:
        semantic_layer_service = ClientSemanticLayerService()
        layers = semantic_layer_service.list_semantic_layers(client_id=client_id, skip=skip, limit=limit)

        return [SemanticLayerResponse.from_db_model(layer) for layer in layers]
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{layer_id}", response_model=SemanticLayerResponse)
async def get_semantic_layer(layer_id: str):
    """Get semantic layer by ID"""
    try:
        semantic_layer_service = ClientSemanticLayerService()
        layer = semantic_layer_service.get_semantic_layer(layer_id)
        if not layer:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Semantic layer not found")
        return SemanticLayerResponse.from_db_model(layer)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{layer_id}/data-stores")
async def add_data_store(layer_id: str, data_store_id: str):
    """Add a data store to semantic layer"""
    try:
        semantic_layer_service = ClientSemanticLayerService()
        layer = semantic_layer_service.add_data_store(semantic_layer_id=layer_id, data_store_id=data_store_id)
        return {"message": "Data store added successfully"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/{layer_id}/data-stores")
async def remove_data_store(layer_id: str, data_store_id: str):
    """Remove a data store from semantic layer"""
    try:
        semantic_layer_service = ClientSemanticLayerService()
        layer = semantic_layer_service.remove_data_store(semantic_layer_id=layer_id, data_store_id=data_store_id)
        return {"message": "Data store removed successfully"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{layer_id}/deactivate")
async def deactivate_semantic_layer(layer_id: str):
    """Deactivate a semantic layer"""
    try:
        semantic_layer_service = ClientSemanticLayerService()
        semantic_layer_service.deactivate_semantic_layer(layer_id)
        return {"message": "Semantic layer deactivated successfully"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
