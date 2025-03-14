import time
import requests
import json
from utils.logger import logger

class TokenManager:
    """Handles authentication and token refreshing."""
    def __init__(self, auth_config):
        self.auth_url = auth_config["url"]
        self.credentials = auth_config["credentials"]
        self.token = None
        self.expiry = 0

    def fetch_token(self):
        response = requests.post(self.auth_url, json=self.credentials)
        if response.status_code == 200:
            data = response.json()
            self.token = data["access_token"]
            self.expiry = time.time() + data.get("expires_in", 3600) - 60  # Refresh 1 min early
            logger.info("Token refreshed successfully.")
        else:
            logger.error("Failed to fetch token: %s", response.text)
            raise Exception("Authentication failed")

    def get_token(self):
        if not self.token or time.time() >= self.expiry:
            logger.info("Issuing a new Token")
            self.fetch_token()
        return self.token
