"""
Authentication Service
"""

from sqlalchemy.orm import Session
from typing import Dict, Any, Optional, List
import pyotp
import qrcode
import io
import base64
import json
import secrets

from app.models.user import User
from app.utils.security import verify_password, get_password_hash, create_access_token, create_refresh_token
from app.utils.encryption import encrypt_data, decrypt_data

class AuthService:
    def __init__(self, db: Session):
        self.db = db

    async def authenticate_user(
        self, 
        email: str, 
        password: str, 
        ip_address: str = None
    ) -> Dict[str, Any]:
        """Authenticate user credentials"""
        user = self.db.query(User).filter(User.email == email).first()
        
        if not user or not verify_password(password, user.hashed_password):
            raise ValueError("Invalid email or password")
        
        if not user.is_active:
            raise ValueError("Account is deactivated")
        
        # Check if MFA is enabled
        if user.mfa_enabled:
            # Return temporary token for MFA verification
            temp_token = create_access_token(
                data={"sub": str(user.id), "mfa_pending": True},
                expires_delta_minutes=5  # Short expiry for MFA
            )
            
            return {
                "mfa_required": True,
                "temp_token": temp_token,
                "message": "MFA verification required"
            }
        
        # Generate tokens for successful login
        access_token = create_access_token(data={"sub": str(user.id)})
        refresh_token = create_refresh_token(data={"sub": str(user.id)})
        
        # Update last login
        user.last_login = func.now()
        self.db.commit()
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.role.value
            }
        }

    async def verify_mfa_and_complete_login(
        self, 
        mfa_token: str, 
        ip_address: str = None
    ) -> Dict[str, Any]:
        """Verify MFA token and complete login"""
        # This would require storing temporary session data
        # For now, this is a placeholder implementation
        
        # In a real implementation, you'd:
        # 1. Verify the temporary token
        # 2. Get user from temporary session
        # 3. Verify MFA token
        # 4. Generate final tokens
        
        return {
            "access_token": "final_access_token",
            "refresh_token": "final_refresh_token",
            "token_type": "bearer"
        }

    async def setup_mfa(self, user_id: int) -> Dict[str, str]:
        """Setup MFA for user"""
        user = self.db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise ValueError("User not found")
        
        if user.mfa_enabled:
            raise ValueError("MFA is already enabled")
        
        # Generate secret
        secret = pyotp.random_base32()
        
        # Create TOTP URI
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=user.email,
            issuer_name="Finance Assistant"
        )
        
        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        # Store encrypted secret (temporarily, until verification)
        user.mfa_secret = encrypt_data(secret)
        self.db.commit()
        
        return {
            "secret": secret,
            "qr_code": f"data:image/png;base64,{qr_code_base64}"
        }

    async def verify_and_enable_mfa(
        self, 
        user_id: int, 
        token: str
    ) -> List[str]:
        """Verify MFA setup and enable it"""
        user = self.db.query(User).filter(User.id == user_id).first()
        
        if not user or not user.mfa_secret:
            raise ValueError("MFA setup not found")
        
        # Decrypt secret
        secret = decrypt_data(user.mfa_secret)
        
        # Verify token
        totp = pyotp.TOTP(secret)
        if not totp.verify(token):
            raise ValueError("Invalid MFA token")
        
        # Generate backup codes
        backup_codes = [secrets.token_hex(4).upper() for _ in range(10)]
        
        # Enable MFA
        user.mfa_enabled = True
        user.backup_codes = encrypt_data(json.dumps(backup_codes))
        self.db.commit()
        
        return backup_codes

    async def disable_mfa(self, user_id: int):
        """Disable MFA for user"""
        user = self.db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise ValueError("User not found")
        
        user.mfa_enabled = False
        user.mfa_secret = None
        user.backup_codes = None
        self.db.commit()

    async def refresh_tokens(self, refresh_token: str) -> Dict[str, str]:
        """Refresh access token"""
        try:
            # Verify refresh token
            payload = verify_token(refresh_token)
            user_id = payload.get("sub")
            
            if not user_id:
                raise ValueError("Invalid refresh token")
            
            # Generate new tokens
            access_token = create_access_token(data={"sub": user_id})
            new_refresh_token = create_refresh_token(data={"sub": user_id})
            
            return {
                "access_token": access_token,
                "refresh_token": new_refresh_token,
                "token_type": "bearer"
            }
            
        except Exception:
            raise ValueError("Invalid refresh token")

    async def logout_user(self, token: str):
        """Logout user (in a real implementation, you'd invalidate the token)"""
        # In a production system, you'd add the token to a blacklist
        # or use a token store like Redis to track invalid tokens
        pass