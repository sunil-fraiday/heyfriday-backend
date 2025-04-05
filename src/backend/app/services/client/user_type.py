from typing import List, Optional, Dict
from bson import ObjectId
from mongoengine import Q

from app.models.mongodb.client import Client
from app.models.mongodb.client_user_type import ClientUserType
from app.schemas.client.user_type import ClientUserTypeCreate, ClientUserTypeUpdate
from app.utils.logger import get_logger

logger = get_logger(__name__)


def get_client_filter(client_id: str) -> Dict:
    """
    Create a filter that works with both ObjectId and client_id.
    This allows API endpoints to use client_id in URLs while still
    supporting internal references that might use ObjectId.
    """
    if ObjectId.is_valid(client_id):
        return {"id": client_id}
    else:
        return {"client_id": client_id}


class ClientUserTypeService:
    """Service for managing client user types"""
    
    @staticmethod
    def create_user_type(client_id: str, user_type_data: ClientUserTypeCreate) -> ClientUserType:
        """Create a new user type for a client"""
        try:
            # Get the client
            client = Client.objects(**get_client_filter(client_id)).first()
            if not client:
                raise ValueError(f"Client with ID {client_id} not found")
            
            # Check if a user type with the same type_id already exists for this client
            existing = ClientUserType.objects(client=client, type_id=user_type_data.type_id).first()
            if existing:
                raise ValueError(f"User type with ID {user_type_data.type_id} already exists for this client")
            
            # Create the new user type
            user_type = ClientUserType(
                client=client,
                type_id=user_type_data.type_id,
                name=user_type_data.name,
                description=user_type_data.description,
                metadata=user_type_data.metadata
            )
            user_type.save()
            
            return user_type
        except Exception as e:
            logger.error(f"Error creating client user type: {str(e)}")
            raise
    
    @staticmethod
    def update_user_type(client_id: str, type_id: str, update_data: ClientUserTypeUpdate) -> Optional[ClientUserType]:
        """Update an existing user type"""
        try:
            # Get the client
            client = Client.objects(**get_client_filter(client_id)).first()
            if not client:
                raise ValueError(f"Client with ID {client_id} not found")
            
            # Find the user type
            user_type = ClientUserType.objects(client=client, type_id=type_id).first()
            if not user_type:
                return None
            
            # Update fields
            if update_data.name is not None:
                user_type.name = update_data.name
            if update_data.description is not None:
                user_type.description = update_data.description
            if update_data.metadata is not None:
                user_type.metadata = update_data.metadata
            if update_data.is_active is not None:
                user_type.is_active = update_data.is_active
                
            user_type.save()
            return user_type
        except Exception as e:
            logger.error(f"Error updating client user type: {str(e)}")
            raise
    
    @staticmethod
    def get_user_type(client_id: str, type_id: str) -> Optional[ClientUserType]:
        """Get a specific user type by client_id and type_id"""
        try:
            client = Client.objects(**get_client_filter(client_id)).first()
            if not client:
                raise ValueError(f"Client with ID {client_id} not found")
                
            return ClientUserType.objects(client=client, type_id=type_id).first()
        except Exception as e:
            logger.error(f"Error getting client user type: {str(e)}")
            raise
    
    @staticmethod
    def get_user_types(client_id: str, include_inactive: bool = False) -> List[ClientUserType]:
        """Get all user types for a client"""
        try:
            client = Client.objects(**get_client_filter(client_id)).first()
            if not client:
                raise ValueError(f"Client with ID {client_id} not found")
            
            query = {"client": client}
            if not include_inactive:
                query["is_active"] = True
                
            return list(ClientUserType.objects(**query))
        except Exception as e:
            logger.error(f"Error getting client user types: {str(e)}")
            raise
    
    @staticmethod
    def delete_user_type(client_id: str, type_id: str) -> bool:
        """Delete a user type"""
        try:
            client = Client.objects(**get_client_filter(client_id)).first()
            if not client:
                raise ValueError(f"Client with ID {client_id} not found")
                
            user_type = ClientUserType.objects(client=client, type_id=type_id).first()
            if not user_type:
                return False
                
            user_type.delete()
            return True
        except Exception as e:
            logger.error(f"Error deleting client user type: {str(e)}")
            raise
    
    @staticmethod
    def get_sender_type_id(client_id: str, type_id: str) -> str:
        """
        Generate the full sender_type ID for a client user type.
        This is used in the sender_type field of chat messages.
        """
        return f"client:{client_id}:{type_id}"
    
    @staticmethod
    def parse_sender_type(sender_type: str) -> Optional[tuple]:
        """
        Parse a sender_type string to extract client_id and type_id.
        Returns (client_id, type_id) tuple if it's a valid client user type,
        or None if it's not a client user type.
        """
        if not sender_type or not isinstance(sender_type, str) or not sender_type.startswith("client:"):
            return None
            
        parts = sender_type.split(":", 2)
        if len(parts) != 3:
            return None
            
        return (parts[1], parts[2])  # client_id, type_id
