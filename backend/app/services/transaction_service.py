"""
Transaction Service
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal

from app.models.transaction import Transaction, TransactionType, TransactionCategory
from app.models.account import Account
from app.schemas.transaction_schemas import (
    TransactionCreate, TransactionUpdate, TransactionFilter,
    TransactionSummary, CategorizeTransactionRequest, CategorizeTransactionResponse
)
from app.ml_models.transaction_categorizer import TransactionCategorizer

class TransactionService:
    def __init__(self, db: Session):
        self.db = db
        self.categorizer = TransactionCategorizer()

    async def create_transaction(self, transaction_data: TransactionCreate) -> Transaction:
        """Create a new transaction"""
        # Auto-categorize if not provided or confidence is low
        if not hasattr(transaction_data, 'category') or not transaction_data.category:
            categorization = await self.categorize_transaction(
                CategorizeTransactionRequest(
                    description=transaction_data.description,
                    amount=transaction_data.amount,
                    merchant_name=transaction_data.merchant_name
                )
            )
            transaction_data.category = categorization.category
            transaction_data.subcategory = categorization.subcategory
        
        # Create transaction
        transaction = Transaction(**transaction_data.dict())
        self.db.add(transaction)
        self.db.commit()
        self.db.refresh(transaction)
        
        # Update account balance
        await self._update_account_balance(transaction.account_id, transaction)
        
        return transaction

    async def get_user_transactions(
        self,
        user_id: int,
        filters: TransactionFilter,
        page: int = 1,
        size: int = 20
    ) -> List[Transaction]:
        """Get user's transactions with filtering"""
        query = self.db.query(Transaction).join(Account).filter(
            Account.user_id == user_id
        )
        
        # Apply filters
        if filters.account_id:
            query = query.filter(Transaction.account_id == filters.account_id)
        
        if filters.transaction_type:
            query = query.filter(Transaction.transaction_type == filters.transaction_type)
        
        if filters.category:
            query = query.filter(Transaction.category == filters.category)
        
        if filters.min_amount:
            query = query.filter(Transaction.amount >= filters.min_amount)
        
        if filters.max_amount:
            query = query.filter(Transaction.amount <= filters.max_amount)
        
        if filters.start_date:
            query = query.filter(Transaction.transaction_date >= filters.start_date)
        
        if filters.end_date:
            query = query.filter(Transaction.transaction_date <= filters.end_date)
        
        if filters.merchant_name:
            query = query.filter(Transaction.merchant_name.ilike(f"%{filters.merchant_name}%"))
        
        if filters.is_pending is not None:
            query = query.filter(Transaction.is_pending == filters.is_pending)
        
        # Order by date (newest first) and paginate
        query = query.order_by(desc(Transaction.transaction_date))
        offset = (page - 1) * size
        
        return query.offset(offset).limit(size).all()

    async def get_transaction_by_id(self, transaction_id: int, user_id: int) -> Optional[Transaction]:
        """Get a specific transaction"""
        return self.db.query(Transaction).join(Account).filter(
            and_(
                Transaction.id == transaction_id,
                Account.user_id == user_id
            )
        ).first()

    async def update_transaction(
        self,
        transaction_id: int,
        user_id: int,
        update_data: TransactionUpdate
    ) -> Optional[Transaction]:
        """Update a transaction"""
        transaction = await self.get_transaction_by_id(transaction_id, user_id)
        
        if not transaction:
            return None
        
        # Store old amount for balance update
        old_amount = transaction.amount
        old_type = transaction.transaction_type
        
        # Update fields
        for field, value in update_data.dict(exclude_unset=True).items():
            setattr(transaction, field, value)
        
        self.db.commit()
        self.db.refresh(transaction)
        
        # Update account balance if amount or type changed
        if old_amount != transaction.amount or old_type != transaction.transaction_type:
            await self._recalculate_account_balance(transaction.account_id)
        
        return transaction

    async def delete_transaction(self, transaction_id: int, user_id: int) -> bool:
        """Delete a transaction"""
        transaction = await self.get_transaction_by_id(transaction_id, user_id)
        
        if not transaction:
            return False
        
        account_id = transaction.account_id
        
        self.db.delete(transaction)
        self.db.commit()
        
        # Recalculate account balance
        await self._recalculate_account_balance(account_id)
        
        return True

    async def get_transaction_summary(
        self,
        user_id: int,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> TransactionSummary:
        """Get transaction summary and statistics"""
        query = self.db.query(Transaction).join(Account).filter(
            Account.user_id == user_id
        )
        
        if start_date:
            query = query.filter(Transaction.transaction_date >= start_date)
        
        if end_date:
            query = query.filter(Transaction.transaction_date <= end_date)
        
        transactions = query.all()
        
        # Calculate totals
        total_income = sum(
            t.amount for t in transactions
            if t.transaction_type == TransactionType.INCOME
        )
        
        total_expenses = sum(
            t.amount for t in transactions
            if t.transaction_type == TransactionType.EXPENSE
        )
        
        net_income = total_income - total_expenses
        
        # Top categories
        category_totals = {}
        for transaction in transactions:
            if transaction.transaction_type == TransactionType.EXPENSE:
                category = transaction.category.value
                category_totals[category] = category_totals.get(category, 0) + float(transaction.amount)
        
        top_categories = [
            {"category": k, "amount": v}
            for k, v in sorted(category_totals.items(), key=lambda x: x[1], reverse=True)[:5]
        ]
        
        # Monthly trend (last 6 months)
        monthly_trend = await self._get_monthly_trend(user_id)
        
        return TransactionSummary(
            total_income=total_income,
            total_expenses=total_expenses,
            net_income=net_income,
            transaction_count=len(transactions),
            top_categories=top_categories,
            monthly_trend=monthly_trend
        )

    async def categorize_transaction(
        self,
        request: CategorizeTransactionRequest
    ) -> CategorizeTransactionResponse:
        """Categorize transaction using ML"""
        result = self.categorizer.predict_category(
            description=request.description,
            amount=float(request.amount),
            merchant_name=request.merchant_name
        )
        
        return CategorizeTransactionResponse(
            category=result["category"],
            subcategory=result.get("subcategory"),
            confidence_score=result["confidence"]
        )

    async def verify_account_ownership(self, account_id: int, user_id: int) -> bool:
        """Verify that account belongs to user"""
        account = self.db.query(Account).filter(
            and_(Account.id == account_id, Account.user_id == user_id)
        ).first()
        
        return account is not None

    async def sync_transactions_from_bank(self, account_id: int) -> Dict[str, int]:
        """Sync transactions from external bank API (mock implementation)"""
        # This would integrate with bank APIs like Plaid
        # For now, return mock data
        
        return {
            "new_count": 5,
            "updated_count": 2,
            "error_count": 0
        }

    async def _update_account_balance(self, account_id: int, transaction: Transaction):
        """Update account balance after transaction"""
        account = self.db.query(Account).filter(Account.id == account_id).first()
        
        if account:
            if transaction.transaction_type == TransactionType.INCOME:
                account.current_balance += transaction.amount
            elif transaction.transaction_type == TransactionType.EXPENSE:
                account.current_balance -= transaction.amount
            
            self.db.commit()

    async def _recalculate_account_balance(self, account_id: int):
        """Recalculate account balance from all transactions"""
        account = self.db.query(Account).filter(Account.id == account_id).first()
        
        if account:
            # Get all transactions for this account
            transactions = self.db.query(Transaction).filter(
                Transaction.account_id == account_id
            ).all()
            
            # Calculate balance
            balance = Decimal('0.00')
            for transaction in transactions:
                if transaction.transaction_type == TransactionType.INCOME:
                    balance += transaction.amount
                elif transaction.transaction_type == TransactionType.EXPENSE:
                    balance -= transaction.amount
            
            account.current_balance = balance
            self.db.commit()

    async def _get_monthly_trend(self, user_id: int) -> List[Dict[str, Any]]:
        """Get monthly transaction trend for the last 6 months"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=180)  # 6 months
        
        # Query monthly aggregates
        monthly_data = self.db.query(
            func.date_format(Transaction.transaction_date, '%Y-%m').label('month'),
            func.sum(
                func.case(
                    (Transaction.transaction_type == TransactionType.INCOME, Transaction.amount),
                    else_=0
                )
            ).label('income'),
            func.sum(
                func.case(
                    (Transaction.transaction_type == TransactionType.EXPENSE, Transaction.amount),
                    else_=0
                )
            ).label('expenses')
        ).join(Account).filter(
            and_(
                Account.user_id == user_id,
                Transaction.transaction_date >= start_date,
                Transaction.transaction_date <= end_date
            )
        ).group_by(
            func.date_format(Transaction.transaction_date, '%Y-%m')
        ).order_by(
            func.date_format(Transaction.transaction_date, '%Y-%m')
        ).all()
        
        return [
            {
                "month": row.month,
                "income": float(row.income or 0),
                "expenses": float(row.expenses or 0),
                "net": float((row.income or 0) - (row.expenses or 0))
            }
            for row in monthly_data
        ]