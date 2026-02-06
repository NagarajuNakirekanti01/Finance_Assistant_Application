"""
Authentication Middleware
"""

from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import logging

from app.utils.security import verify_token, is_token_expired

logger = logging.getLogger(__name__)

class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware to handle authentication for protected routes"""
    
    def __init__(self, app):
        super().__init__(app)
        self.security = HTTPBearer()
        
        # Routes that don't require authentication
        self.public_routes = {
            "/",
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/v1/auth/register",
            "/api/v1/auth/login",
            "/api/v1/auth/refresh"
        }

    async def dispatch(self, request: Request, call_next):
        """Process request and check authentication"""
        
        # Skip authentication for public routes
        if request.url.path in self.public_routes:
            response = await call_next(request)
            return response
        
        # Skip authentication for preflight requests
        if request.method == "OPTIONS":
            response = await call_next(request)
            return response
        
        # Check if route requires authentication
        if request.url.path.startswith("/api/v1/"):
            authorization = request.headers.get("Authorization")
            
            if not authorization:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Authorization header required"}
                )
            
            try:
                # Extract token from "Bearer <token>"
                scheme, token = authorization.split()
                
                if scheme.lower() != "bearer":
                    return JSONResponse(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        content={"detail": "Invalid authentication scheme"}
                    )
                
                # Verify token
                payload = verify_token(token)
                
                # Check if token is expired
                if is_token_expired(token):
                    return JSONResponse(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        content={"detail": "Token has expired"}
                    )
                
                # Add user info to request state
                request.state.user_id = payload.get("sub")
                request.state.user_role = payload.get("role", "user")
                
            except ValueError as e:
                logger.warning(f"Invalid token: {str(e)}")
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Invalid token"}
                )
            except Exception as e:
                logger.error(f"Authentication error: {str(e)}")
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Authentication failed"}
                )
        
        response = await call_next(request)
        return response