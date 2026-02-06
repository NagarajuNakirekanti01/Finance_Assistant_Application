"""
Budget and Goal Models
"""

from sqlalchemy import Column, Integer, String, Decimal, DateTime, ForeignKey, Enum, Boolean, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.database import Base
import enum

class BudgetPeriod(enum.Enum):
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"

class Budget(Base):
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Budget details
    name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False)
    amount = Column(Decimal(15, 2), nullable=False)
    period = Column(Enum(BudgetPeriod), nullable=False)
    
    # Status and tracking
    is_active = Column(Boolean, default=True)
    alert_threshold = Column(Decimal(5, 2), default=80.0)  # Alert at 80% of budget
    current_spent = Column(Decimal(15, 2), default=0.00)
    
    # Dates
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="budgets")
    
    def __repr__(self):
        return f"<Budget(id={self.id}, name='{self.name}', amount={self.amount})>"

class GoalType(enum.Enum):
    SAVINGS = "savings"
    DEBT_PAYOFF = "debt_payoff"
    INVESTMENT = "investment"
    EMERGENCY_FUND = "emergency_fund"
    VACATION = "vacation"
    HOUSE_DOWN_PAYMENT = "house_down_payment"
    OTHER = "other"

class Goal(Base):
    __tablename__ = "goals"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Goal details
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    goal_type = Column(Enum(GoalType), nullable=False)
    target_amount = Column(Decimal(15, 2), nullable=False)
    current_amount = Column(Decimal(15, 2), default=0.00)
    
    # Timeline
    target_date = Column(DateTime(timezone=True), nullable=True)
    monthly_contribution = Column(Decimal(15, 2), default=0.00)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_achieved = Column(Boolean, default=False)
    priority = Column(Integer, default=1)  # 1=high, 2=medium, 3=low
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    achieved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="goals")
    
    def __repr__(self):
        return f"<Goal(id={self.id}, name='{self.name}', target_amount={self.target_amount})>"