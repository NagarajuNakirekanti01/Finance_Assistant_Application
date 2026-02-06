"""
Transaction Routes
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List, Optional

from app.models.database import get_db
from app.schemas.transaction_schemas import (
    TransactionCreate, TransactionUpdate, TransactionResponse,
    TransactionFilter, TransactionSummary, CategorizeTransactionRequest,
    CategorizeTransactionResponse
)
from app.services.transaction_service import TransactionService
from app.utils.security import verify_token
from app.utils.pagination import paginate

router = APIRouter()
security = HTTPBearer()

def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> int:
    """Get current user ID from token"""
    try:
        payload = verify_token(credentials.credentials)
        return int(payload.get("sub"))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

@router.post("/", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    transaction_data: TransactionCreate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Create a new transaction"""
    transaction_service = TransactionService(db)
    
    # Verify account belongs to user
    if not await transaction_service.verify_account_ownership(
        account_id=transaction_data.account_id,
        user_id=user_id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account not found or access denied"
        )
    
    transaction = await transaction_service.create_transaction(transaction_data)
    return transaction

@router.get("/", response_model=List[TransactionResponse])
async def get_transactions(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
    account_id: Optional[int] = Query(None),
    category: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100)
):
    """Get user's transactions with filtering and pagination"""
    transaction_service = TransactionService(db)
    
    # Build filter
    filter_params = TransactionFilter(
        account_id=account_id,
        category=category,
        start_date=start_date,
        end_date=end_date
    )
    
    transactions = await transaction_service.get_user_transactions(
        user_id=user_id,
        filters=filter_params,
        page=page,
        size=size
    )
    
    return transactions

@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get a specific transaction"""
    transaction_service = TransactionService(db)
    
    transaction = await transaction_service.get_transaction_by_id(
        transaction_id=transaction_id,
        user_id=user_id
    )
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    return transaction

@router.put("/{transaction_id}", response_model=TransactionResponse)
async def update_transaction(
    transaction_id: int,
    transaction_data: TransactionUpdate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Update a transaction"""
    transaction_service = TransactionService(db)
    
    transaction = await transaction_service.update_transaction(
        transaction_id=transaction_id,
        user_id=user_id,
        update_data=transaction_data
    )
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    return transaction

@router.delete("/{transaction_id}")
async def delete_transaction(
    transaction_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Delete a transaction"""
    transaction_service = TransactionService(db)
    
    success = await transaction_service.delete_transaction(
        transaction_id=transaction_id,
        user_id=user_id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    return {"message": "Transaction deleted successfully"}

@router.get("/summary/stats", response_model=TransactionSummary)
async def get_transaction_summary(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    """Get transaction summary and statistics"""
    transaction_service = TransactionService(db)
    
    summary = await transaction_service.get_transaction_summary(
        user_id=user_id,
        start_date=start_date,
        end_date=end_date
    )
    
    return summary

@router.post("/categorize", response_model=CategorizeTransactionResponse)
async def categorize_transaction(
    categorize_data: CategorizeTransactionRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Automatically categorize a transaction using ML"""
    transaction_service = TransactionService(db)
    
    result = await transaction_service.categorize_transaction(categorize_data)
    return result

@router.post("/import/csv")
async def import_transactions_csv(
    account_id: int,
    # file: UploadFile = File(...),  # Would handle CSV file upload
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Import transactions from CSV file"""
    transaction_service = TransactionService(db)
    
    # Verify account ownership
    if not await transaction_service.verify_account_ownership(account_id, user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account not found or access denied"
        )
    
    # Mock implementation - would process CSV file
    return {
        "message": "CSV import functionality would be implemented here",
        "imported_count": 0,
        "errors": []
    }

@router.post("/sync/{account_id}")
async def sync_account_transactions(
    account_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Sync transactions from external bank API"""
    transaction_service = TransactionService(db)
    
    # Verify account ownership
    if not await transaction_service.verify_account_ownership(account_id, user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account not found or access denied"
        )
    
    # Mock implementation - would sync with bank API
    result = await transaction_service.sync_transactions_from_bank(account_id)
    
    return {
        "message": "Account transactions synced successfully",
        "new_transactions": result.get("new_count", 0),
        "updated_transactions": result.get("updated_count", 0)
    }