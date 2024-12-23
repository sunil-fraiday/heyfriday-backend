import os
import requests
from typing import Optional

from app.utils.logger import get_logger

logger = get_logger(__name__)


class KeycloakAuthorizationService:
    def __init__(self, server_url: str, realm: str, client_id: str, client_secret: Optional[str] = None):
        self.server_url = server_url
        self.realm = realm
        self.client_id = client_id
        self.client_secret = client_secret

    def get_admin_access_token(self, admin_username: str, admin_password: str) -> Optional[str]:
        """
        Obtain an access token for the Keycloak admin user.
        """
        url = f"{self.server_url}/realms/{self.realm}/protocol/openid-connect/token"
        data = {
            "grant_type": "password",
            "client_id": "admin-cli",
            "username": admin_username,
            "password": admin_password,
        }

        response = requests.post(url, data=data)
        if response.status_code == 200:
            return response.json().get("access_token")
        else:
            raise Exception(f"Failed to obtain admin access token: {response.json()}")

    def exchange_token(self, admin_token: str, subject_id: str) -> dict:
        """
        Perform token exchange using Keycloak admin credentials.
        """
        url = f"{self.server_url}/realms/{self.realm}/protocol/openid-connect/token"
        data = {
            "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "requested_subject": subject_id,
            "requested_token_type": "urn:ietf:params:oauth:token-type:access_token",
        }

        headers = {"Authorization": f"Bearer {admin_token}"}

        response = requests.post(url, data=data, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to exchange token: {response.json()}")

    def validate_user_authorization(self, user_token: str, resource: str, scope: str) -> bool:
        """
        Validate if the user token has access to the given resource and scope.
        """
        introspect_url = f"{self.server_url}/realms/{self.realm}/protocol/openid-connect/token/introspect"
        data = {"token": user_token, "client_id": self.client_id, "client_secret": self.client_secret}

        # Step 1: Introspect the token to ensure it's valid
        introspect_response = requests.post(introspect_url, data=data)
        if introspect_response.status_code != 200 or not introspect_response.json().get("active", False):
            raise Exception("Token is invalid or inactive.")

        auth_url = f"{self.server_url}/realms/{self.realm}/protocol/openid-connect/token"
        auth_data = {
            "grant_type": "urn:ietf:params:oauth:grant-type:uma-ticket",
            "audience": self.client_id,
            "response_mode": "decision",
            "permission": f"{resource}#{scope}",
        }
        headers = {"Authorization": f"Bearer {user_token}"}

        auth_response = requests.post(auth_url, data=auth_data, headers=headers)
        logger.info(f"Auth response: {auth_response.json()}, Status code: {auth_response.status_code}")
        if auth_response.status_code == 200:
            return auth_response.json().get("result", False)  # True if authorized, False otherwise
        if auth_response.status_code == 403:
            return False
        else:
            raise Exception(f"Failed to validate authorization: {auth_response.json()}")
