import jwt
import requests
from typing import Optional, Dict, Any
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from core.config import get_settings
from core.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)

security = HTTPBearer()


class MicrosoftAuthError(Exception):
    """Custom exception for Microsoft Auth errors"""
    pass


class MicrosoftAuth:
    """Microsoft Azure AD JWT token validation"""
    
    def __init__(self):
        self.tenant_id = settings.microsoft_tenant_id
        self.client_id = settings.microsoft_client_id
        self.audience = settings.microsoft_audience or settings.microsoft_client_id
        self.jwks_uri = f"https://login.microsoftonline.com/{self.tenant_id}/discovery/v2.0/keys"
        self.issuer = f"https://login.microsoftonline.com/{self.tenant_id}/v2.0"
        self._jwks_cache = None
    
    def get_jwks(self) -> Dict[str, Any]:
        """Fetch JSON Web Key Set from Microsoft"""
        if self._jwks_cache is None:
            try:
                response = requests.get(self.jwks_uri, timeout=10)
                response.raise_for_status()
                self._jwks_cache = response.json()
            except requests.RequestException as e:
                logger.error(f"Failed to fetch JWKS: {e}")
                raise MicrosoftAuthError("Failed to fetch signing keys")
        
        return self._jwks_cache
    
    def get_signing_key(self, token_header: Dict[str, Any]) -> str:
        """Get the signing key for token validation"""
        jwks = self.get_jwks()
        
        for key in jwks.get("keys", []):
            if key.get("kid") == token_header.get("kid"):
                return jwt.algorithms.RSAAlgorithm.from_jwk(key)
        
        raise MicrosoftAuthError("Unable to find appropriate signing key")
    
    def validate_token(self, token: str) -> Dict[str, Any]:
        """Validate Microsoft JWT token"""
        try:
            # Decode header without verification to get kid
            unverified_header = jwt.get_unverified_header(token)
            
            # Get signing key
            signing_key = self.get_signing_key(unverified_header)
            
            # Decode and validate token
            payload = jwt.decode(
                token,
                signing_key,
                algorithms=["RS256"],
                audience=self.audience,
                issuer=self.issuer,
                options={"verify_exp": True}
            )
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        except MicrosoftAuthError as e:
            logger.error(f"Microsoft Auth error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed"
            )


# Global instance
microsoft_auth = MicrosoftAuth()


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    Dependency to get current user from Microsoft JWT token
    Returns the token payload containing user information
    """
    token = credentials.credentials
    user_data = microsoft_auth.validate_token(token)
    
    # Log successful authentication
    logger.info(
        "User authenticated",
        user_id=user_data.get("sub"),
        email=user_data.get("email"),
        name=user_data.get("name")
    )
    
    return user_data


def get_current_user_optional(credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))) -> Optional[Dict[str, Any]]:
    """
    Optional authentication dependency
    Returns None if no token is provided, validates if token is present
    """
    if not credentials:
        return None
    
    return get_current_user(credentials)
