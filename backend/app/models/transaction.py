"""
Transaction Model
"""

from sqlalchemy import Column, Integer, String, Decimal, DateTime, ForeignKey, Enum, Text, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.database import Base
import enum

class TransactionType(enum.Enum):
    INCOME = "income"
    EXPENSE = "expense"
    TRANSFER = "transfer"

class TransactionCategory(enum.Enum):
    # Income categories
    SALARY = "salary"
    FREELANCE = "freelance"
    INVESTMENT_INCOME = "investment_income"
    OTHER_INCOME = "other_income"
    
    # Expense categories
    FOOD_DINING = "food_dining"
    SHOPPING = "shopping"
    TRANSPORTATION = "transportation"
    ENTERTAINMENT = "entertainment"
    BILLS_UTILITIES = "bills_utilities"
    HEALTHCARE = "healthcare"
    EDUCATION = "education"
    TRAVEL = "travel"
    INSURANCE = "insurance"
    TAXES = "taxes"
    OTHER_EXPENSE = "other_expense"
    
    # Transfer
    TRANSFER_IN = "transfer_in"
    TRANSFER_OUT = "transfer_out"

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    
    # Transaction details
    amount = Column(Decimal(15, 2), nullable=False)
    transaction_type = Column(Enum(TransactionType), nullable=False)
    category = Column(Enum(TransactionCategory), nullable=False)
    subcategory = Column(String(100), nullable=True)
    
    # Description and metadata
    description = Column(String(500), nullable=False)
    merchant_name = Column(String(255), nullable=True)
    location = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    
    # Transaction status
    is_pending = Column(Boolean, default=False)
    is_recurring = Column(Boolean, default=False)
    confidence_score = Column(Decimal(3, 2), nullable=True)  # ML categorization confidence
    
    # Dates
    transaction_date = Column(DateTime(timezone=True), nullable=False)
    posted_date = Column(DateTime(timezone=True), nullable=True)
    
    # External integration
    plaid_transaction_id = Column(String(255), nullable=True)
    external_account_id = Column(String(255), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    account = relationship("Account", back_populates="transactions")
    
    def __repr__(self):
        return f"<Transaction(id={self.id}, amount={self.amount}, type='{self.transaction_type.value}')>"