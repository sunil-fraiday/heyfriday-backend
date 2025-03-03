import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

from azure.storage.blob import BlobServiceClient, BlobSasPermissions, generate_blob_sas


class AzureBlobStorage:
    """Handles interactions with Azure Blob Storage"""

    def __init__(self, connection_string: str, container_name: str):
        """Initialize Azure Blob Storage client"""
        self.connection_string = connection_string
        self.container_name = container_name
        self.blob_service_client = BlobServiceClient.from_connection_string(connection_string)

        # Ensure container exists
        self._ensure_container_exists()

    def _ensure_container_exists(self):
        """Create the container if it doesn't exist"""
        try:
            container_client = self.blob_service_client.get_container_client(self.container_name)
            container_client.get_container_properties()
        except Exception:
            self.blob_service_client.create_container(self.container_name)

    def upload_chart(self, chart_bytes: bytes, filename: Optional[str] = None) -> str:
        """Upload a chart to blob storage"""
        if not filename:
            filename = f"chart_{uuid.uuid4()}.png"

        blob_client = self.blob_service_client.get_blob_client(container=self.container_name, blob=filename)

        blob_client.upload_blob(chart_bytes, overwrite=True)

        return filename

    def get_presigned_url(self, blob_name: str, expiry_hours: int = 24) -> Tuple[str, datetime]:
        """Generate a presigned URL for a blob"""
        account_name = None
        account_key = None

        for part in self.connection_string.split(";"):
            if "AccountName=" in part:
                account_name = part.split("=", 1)[1]
            elif "AccountKey=" in part:
                account_key = part.split("=", 1)[1]

        if not account_name or not account_key:
            raise ValueError("Connection string must contain AccountName and AccountKey")

        # Calculate expiry time
        expiry = datetime.now(tz=timezone.utc) + timedelta(hours=expiry_hours)

        sas_token = generate_blob_sas(
            account_name=account_name,
            container_name=self.container_name,
            blob_name=blob_name,
            account_key=account_key,
            permission=BlobSasPermissions(read=True),
            expiry=expiry,
        )

        blob_url = f"https://{account_name}.blob.core.windows.net/{self.container_name}/{blob_name}?{sas_token}"

        return blob_url, expiry

    def read_blob(self, blob_name: str) -> bytes:
        """Read a blob's content as bytes"""
        blob_client = self.blob_service_client.get_blob_client(container=self.container_name, blob=blob_name)

        # Download blob content
        blob_data = blob_client.download_blob()
        content = blob_data.readall()

        return content
