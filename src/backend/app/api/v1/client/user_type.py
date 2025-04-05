from fastapi import APIRouter, Depends, HTTPException, status

from app.api.v1.deps import verify_api_key
from app.schemas.client.user_type import (
    ClientUserTypeCreate,
    ClientUserTypeUpdate,
    ClientUserTypeResponse,
    ClientUserTypesResponse
)
from app.services.client.user_type import ClientUserTypeService

router = APIRouter(prefix="/clients", tags=["Client User Types"])


@router.post("/{client_id}/user-types", response_model=ClientUserTypeResponse)
def create_user_type(
    client_id: str,
    user_type_data: ClientUserTypeCreate,
    api_key: dict = Depends(verify_api_key)
):
    """Create a new user type for a client"""
    try:
        user_type = ClientUserTypeService.create_user_type(client_id, user_type_data)
        return ClientUserTypeResponse.from_db_model(user_type)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user type: {str(e)}"
        )


@router.get("/{client_id}/user-types", response_model=ClientUserTypesResponse)
def get_user_types(
    client_id: str,
    include_inactive: bool = False,
    api_key: dict = Depends(verify_api_key)
):
    """Get all user types for a client"""
    try:
        user_types = ClientUserTypeService.get_user_types(client_id, include_inactive)
        return ClientUserTypesResponse(
            items=[ClientUserTypeResponse.from_db_model(ut) for ut in user_types],
            total=len(user_types)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user types: {str(e)}"
        )


@router.get("/{client_id}/user-types/{type_id}", response_model=ClientUserTypeResponse)
def get_user_type(
    client_id: str,
    type_id: str,
    api_key: dict = Depends(verify_api_key)
):
    """Get a specific user type by ID"""
    try:
        user_type = ClientUserTypeService.get_user_type(client_id, type_id)
        if not user_type:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User type with ID {type_id} not found"
            )
        return ClientUserTypeResponse.from_db_model(user_type)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user type: {str(e)}"
        )


@router.put("/{client_id}/user-types/{type_id}", response_model=ClientUserTypeResponse)
def update_user_type(
    client_id: str,
    type_id: str,
    update_data: ClientUserTypeUpdate,
    api_key: dict = Depends(verify_api_key)
):
    """Update an existing user type"""
    try:
        user_type = ClientUserTypeService.update_user_type(client_id, type_id, update_data)
        if not user_type:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User type with ID {type_id} not found"
            )
        return ClientUserTypeResponse.from_db_model(user_type)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user type: {str(e)}"
        )


@router.delete("/{client_id}/user-types/{type_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_type(
    client_id: str,
    type_id: str,
    api_key: dict = Depends(verify_api_key)
):
    """Delete a user type"""
    try:
        success = ClientUserTypeService.delete_user_type(client_id, type_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User type with ID {type_id} not found"
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user type: {str(e)}"
        )
