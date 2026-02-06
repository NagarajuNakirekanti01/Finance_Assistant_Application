"""
Transaction Pydantic Schemas
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from app.models.transaction import TransactionType, TransactionCategory

class TransactionBase(BaseModel):
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    transaction_type: TransactionType
    category: TransactionCategory
    subcategory: Optional[str] = Field(None, max_length=100)
    description: str = Field(..., min_length=1, max_length=500)
    merchant_name: Optional[str] = Field(None, max_length=255)
    location: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = None
    transaction_date: datetime

class TransactionCreate(TransactionBase):
    account_id: int

class TransactionUpdate(BaseModel):
    amount: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    category: Optional[TransactionCategory] = None
    subcategory: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, min_length=1, max_length=500)
    merchant_name: Optional[str] = Field(None, max_length=255)
    location: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = None

class TransactionResponse(TransactionBase):
    id: int
    account_id: int
    is_pending: bool
    is_recurring: bool
    confidence_score: Optional[Decimal] = None
    posted_date: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class TransactionFilter(BaseModel):
    account_id: Optional[int] = None
    transaction_type: Optional[TransactionType] = None
    category: Optional[TransactionCategory] = None
    min_amount: Optional[Decimal] = Field(None, ge=0)
    max_amount: Optional[Decimal] = Field(None, ge=0)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    merchant_name: Optional[str] = None
    is_pending: Optional[bool] = None

class TransactionSummary(BaseModel):
    total_income: Decimal
    total_expenses: Decimal
    net_income: Decimal
    transaction_count: int
    top_categories: List[dict]
    monthly_trend: List[dict]

class CategorizeTransactionRequest(BaseModel):
    description: str = Field(..., min_length=1, max_length=500)
    amount: Decimal = Field(..., gt=0)
    merchant_name: Optional[str] = None

class CategorizeTransactionResponse(BaseModel):
    category: TransactionCategory
    subcategory: Optional[str] = None
    confidence_score: float = Field(..., ge=0.0, le=1.0)