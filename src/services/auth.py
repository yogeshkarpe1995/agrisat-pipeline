"""
Authentication module for Copernicus Dataspace services.
"""

import requests
import logging
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)

class CopernicusAuth:
    """Handle authentication with Copernicus Dataspace."""
    
    def __init__(self, config):
        self.config = config
        self.access_token = None
        self.token_expires_at = None
        
    def get_access_token(self) -> str:
        """Get a valid access token, refreshing if necessary."""
        if self._is_token_valid():
            return self.access_token
            
        return self._refresh_token()
    
    def _is_token_valid(self) -> bool:
        """Check if current token is still valid."""
        if not self.access_token or not self.token_expires_at:
            return False
            
        # Check if token expires in the next 5 minutes
        buffer_time = timedelta(minutes=5)
        return datetime.now() < (self.token_expires_at - buffer_time)
    
    def _refresh_token(self) -> str:
        """Refresh the access token from Copernicus."""
        logger.info("Refreshing Copernicus access token")
        
        data = {
            "grant_type": "password",
            "username": self.config.COPERNICUS_USERNAME,
            "password": self.config.COPERNICUS_PASSWORD,
            "client_id": self.config.COPERNICUS_CLIENT_ID,
        }
        
        if self.config.COPERNICUS_CLIENT_SECRET:
            data["client_secret"] = self.config.COPERNICUS_CLIENT_SECRET
        
        try:
            response = requests.post(
                self.config.COPERNICUS_TOKEN_URL,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data["access_token"]
            
            # Calculate token expiration time
            expires_in = token_data.get("expires_in", 3600)  # Default 1 hour
            self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
            
            logger.info(f"Token refreshed successfully, expires at {self.token_expires_at}")
            return self.access_token
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to refresh access token: {str(e)}")
            raise Exception(f"Authentication failed: {str(e)}")
    
    def get_headers(self) -> dict:
        """Get authentication headers for API requests."""
        token = self.get_access_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
