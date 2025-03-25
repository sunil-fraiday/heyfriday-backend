from typing import Dict, Any
import time
from app.utils.logger import get_logger
from app.core.config import settings

logger = get_logger(__name__)


class HealthService:
    """Service for health and readiness checks of system components"""

    @staticmethod
    async def check_health() -> Dict[str, Any]:
        """
        Performs a basic health check to determine if the service is running.

        Returns:
            Dictionary with status and timestamp
        """
        return {"status": "healthy", "timestamp": time.time(), "version": settings.VERSION}

    @staticmethod
    async def check_database() -> Dict[str, Any]:
        """
        Checks if the MongoDB connection is working properly.
        Uses the existing connection rather than creating a new one.

        Returns:
            Dictionary with database status and connection info
        """
        try:
            from mongoengine.connection import get_connection

            # Get the existing connection established during startup
            connection = get_connection()

            # Execute a simple admin command to verify the connection works
            server_info = connection.server_info()

            return {
                "status": "connected",
                "version": server_info.get("version", "unknown"),
                "connection": (
                    settings.MONGODB_URI.split("@")[-1].split("/")[0] if settings.MONGODB_URI else "unknown"
                ),  # Only show host:port, not credentials
            }
        except Exception as e:
            logger.error(f"Database health check failed", exc_info=True)
            return {
                "status": "disconnected",
                "error": str(e),
            }

    @staticmethod
    async def check_celery() -> Dict[str, Any]:
        """
        Checks if the Celery broker connection is working.

        Returns:
            Dictionary with celery status
        """
        try:
            from app.core.celery_config import celery_app

            # Ping the broker to check connection
            response = celery_app.control.ping(timeout=1.0)

            if response:
                return {
                    "status": "connected",
                    "workers": len(response),
                }
            else:
                return {
                    "status": "no_workers",
                }
        except Exception as e:
            logger.error(f"Celery health check failed", exc_info=True)
            return {
                "status": "disconnected",
                "error": str(e),
            }

    @classmethod
    async def get_readiness(cls) -> Dict[str, Any]:
        """
        Performs a comprehensive readiness check for all required services.

        Returns:
            Dictionary with overall readiness status and component checks
        """
        db_status = await cls.check_database()
        # celery_status = await cls.check_celery()

        components = {
            "database": db_status,
            # "celery": celery_status,
        }

        # Determine overall readiness based on component checks
        all_ready = all(component.get("status") in ["connected", "healthy"] for component in components.values())

        return {"status": "ready" if all_ready else "not_ready", "timestamp": time.time(), "components": components}

    @classmethod
    async def get_full_health(cls) -> Dict[str, Any]:
        """
        Performs an extensive health check of all system components.

        Returns:
            Dictionary with detailed health information
        """
        basic_health = await cls.check_health()
        readiness = await cls.get_readiness()

        return {**basic_health, "components": readiness["components"], "ready": readiness["status"] == "ready"}
