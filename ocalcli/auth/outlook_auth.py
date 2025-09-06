"""Microsoft Graph authentication using MSAL device code flow."""

import json
import os
import sys
from pathlib import Path
from typing import Optional

import msal
from platformdirs import user_config_dir

from ..exceptions import AuthenticationError


class OutlookAuth:
    """Handles Microsoft Graph authentication using MSAL."""
    
    # Microsoft Graph scopes
    SCOPES = ["Calendars.ReadWrite"]
    
    # Default client ID for public client (can be overridden)
    # Note: Users should create their own Azure app registration for production use
    DEFAULT_CLIENT_ID = None  # No default - users must provide their own
    
    def __init__(self, client_id: Optional[str] = None, tenant: str = "organizations"):
        """Initialize authentication.
        
        Args:
            client_id: Azure app registration client ID (uses default if None)
            tenant: Azure tenant ID or "organizations" for multi-tenant
        """
        self.client_id = client_id or os.getenv("OCALCLI_CLIENT_ID", self.DEFAULT_CLIENT_ID)
        self.tenant = tenant or os.getenv("OCALCLI_TENANT", "organizations")
        self.config_dir = Path(user_config_dir("ocalcli", "ocalcli"))
        self.token_cache_path = self.config_dir / "msal_token_cache.bin"
        
        # Ensure config directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize MSAL app
        if self.tenant == "organizations":
            authority = "https://login.microsoftonline.com/common"
        else:
            authority = f"https://login.microsoftonline.com/{self.tenant}"
            
        self.app = msal.PublicClientApplication(
            client_id=self.client_id,
            authority=authority,
            token_cache=self._load_token_cache()
        )
    
    def _load_token_cache(self) -> msal.SerializableTokenCache:
        """Load token cache from file."""
        cache = msal.SerializableTokenCache()
        if self.token_cache_path.exists():
            try:
                with open(self.token_cache_path, "r", encoding="utf-8") as f:
                    cache.deserialize(f.read())
            except (json.JSONDecodeError, OSError) as e:
                print(f"Warning: Could not load token cache: {e}", file=sys.stderr)
        return cache
    
    def _save_token_cache(self) -> None:
        """Save token cache to file."""
        if self.app.token_cache.has_state_changed:
            try:
                with open(self.token_cache_path, "w", encoding="utf-8") as f:
                    f.write(self.app.token_cache.serialize())
            except OSError as e:
                print(f"Warning: Could not save token cache: {e}", file=sys.stderr)
    
    def get_access_token(self) -> str:
        """Get a valid access token, performing device code flow if needed.
        
        Returns:
            Valid access token
            
        Raises:
            AuthenticationError: If authentication fails
        """
        # Try to get token silently first
        accounts = self.app.get_accounts()
        if accounts:
            result = self.app.acquire_token_silent(self.SCOPES, account=accounts[0])
            if result and "access_token" in result:
                self._save_token_cache()
                return result["access_token"]
        
        # Perform device code flow
        try:
            flow = self.app.initiate_device_flow(scopes=self.SCOPES)
            if "user_code" not in flow:
                raise AuthenticationError(f"Failed to initiate device flow: {flow}")
            
            print(f"To sign in, use a web browser to open the page {flow['verification_uri']}")
            print(f"and enter the code {flow['user_code']} to authenticate.")
            print("Waiting for authentication...")
            
            result = self.app.acquire_token_by_device_flow(flow)
            
            if "access_token" in result:
                self._save_token_cache()
                return result["access_token"]
            else:
                error = result.get("error", "unknown")
                description = result.get("error_description", "No description")
                raise AuthenticationError(f"Authentication failed: {error} - {description}")
                
        except Exception as e:
            if isinstance(e, AuthenticationError):
                raise
            raise AuthenticationError(f"Authentication error: {e}")
    
    def sign_out(self) -> None:
        """Sign out and clear token cache."""
        accounts = self.app.get_accounts()
        for account in accounts:
            self.app.remove_account(account)
        
        # Clear token cache file
        if self.token_cache_path.exists():
            try:
                self.token_cache_path.unlink()
            except OSError:
                pass
        
        print("Signed out successfully.")
    
    def is_authenticated(self) -> bool:
        """Check if user is currently authenticated.
        
        Returns:
            True if authenticated, False otherwise
        """
        try:
            token = self.get_access_token()
            return bool(token)
        except AuthenticationError:
            return False
