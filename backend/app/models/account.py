"""
Account Model
"""

from sqlalchemy import Column, Integer, String, Decimal, DateTime, ForeignKey, Enum, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.database import Base
import enum

class AccountType(enum.Enum):
    CHECKING = "checking"
    SAVINGS = "savings"
    CREDIT_CARD = "credit_card"
    INVESTMENT = "investment"
    LOAN = "loan"

class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Account details
    name = Column(String(255), nullable=False)
    account_type = Column(Enum(AccountType), nullable=False)
    institution_name = Column(String(255), nullable=False)
    account_number = Column(String(255), nullable=True)  # Encrypted
    routing_number = Column(String(255), nullable=True)  # Encrypted
    
    # Balance information
    current_balance = Column(Decimal(15, 2), default=0.00)
    available_balance = Column(Decimal(15, 2), default=0.00)
    credit_limit = Column(Decimal(15, 2), nullable=True)
    
    # Account status
    is_active = Column(Boolean, default=True)
    is_primary = Column(Boolean, default=False)
    
    # External integration
    plaid_account_id = Column(String(255), nullable=True)
    plaid_access_token = Column(String(500), nullable=True)  # Encrypted
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_synced = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="accounts")
    transactions = relationship("Transaction", back_populates="account", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Account(id={self.id}, name='{self.name}', type='{self.account_type.value}')>"