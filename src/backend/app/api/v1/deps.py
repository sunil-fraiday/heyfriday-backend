from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer
from app.core.config import settings
from app.utils.logger import get_logger

security = HTTPBearer()

logger = get_logger(__name__)


async def verify_api_key(request: Request):
    """Verify API key from Authorization header"""
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Authorization header")

    try:
        scheme, api_key = auth_header.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authorization scheme")

        if api_key != settings.ADMIN_API_KEY:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid API key")

        return api_key

    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authorization format")
