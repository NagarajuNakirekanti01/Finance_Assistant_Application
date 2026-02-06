"""
Chatbot Service
"""

import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.models.transaction import Transaction, TransactionType, TransactionCategory
from app.models.account import Account
from app.models.budget import Budget
from app.chatbot.intent_classifier import intent_classifier
from app.services.transaction_service import TransactionService

class ChatbotService:
    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id
        self.transaction_service = TransactionService(db)

    async def process_message(
        self, 
        message: str, 
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process user message and generate response"""
        
        # Generate conversation ID if not provided
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
        
        # Classify intent
        intent, confidence, entities = intent_classifier.classify_intent(message)
        
        # Extract additional entities
        extracted_entities = intent_classifier.extract_entities(message)
        
        # Generate response based on intent
        response_data = await self._generate_response(intent, message, extracted_entities)
        
        # Store conversation (in a real app, you'd save to database)
        await self._store_conversation_message(
            conversation_id, message, response_data["response"], intent
        )
        
        return {
            "response": response_data["response"],
            "intent": intent,
            "confidence": confidence,
            "entities": entities,
            "conversation_id": conversation_id,
            "chart_data": response_data.get("chart_data"),
            "actions": response_data.get("actions")
        }

    async def _generate_response(
        self, 
        intent: str, 
        message: str, 
        entities: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate response based on intent and entities"""
        
        response_data = {"response": "", "chart_data": None, "actions": None}
        
        if intent == "greeting":
            response_data["response"] = intent_classifier.get_response_template(intent)
            
        elif intent == "balance_inquiry":
            balance_info = await self._get_account_balances()
            response_data["response"] = f"Here are your current account balances:\n{balance_info}"
            response_data["chart_data"] = await self._get_balance_chart_data()
            
        elif intent == "spending_analysis":
            spending_analysis = await self._get_spending_analysis(entities)
            response_data["response"] = spending_analysis["text"]
            response_data["chart_data"] = spending_analysis["chart_data"]
            
        elif intent == "budget_help":
            budget_advice = await self._get_budget_advice()
            response_data["response"] = budget_advice
            
        elif intent == "savings_advice":
            savings_advice = await self._get_savings_advice()
            response_data["response"] = savings_advice
            
        elif intent == "transaction_search":
            transactions = await self._search_transactions(entities)
            response_data["response"] = transactions["text"]
            response_data["actions"] = transactions.get("actions")
            
        elif intent == "financial_goals":
            goals_info = await self._get_financial_goals_info()
            response_data["response"] = goals_info
            
        elif intent == "bill_reminders":
            bill_reminders = await self._get_bill_reminders()
            response_data["response"] = bill_reminders
            
        elif intent == "export_data":
            export_info = await self._get_export_options()
            response_data["response"] = export_info
            response_data["actions"] = [
                {"type": "export", "format": "pdf", "label": "Download PDF Report"},
                {"type": "export", "format": "excel", "label": "Download Excel Report"}
            ]
            
        elif intent == "help":
            response_data["response"] = intent_classifier.get_response_template(intent)
            
        elif intent == "goodbye":
            response_data["response"] = intent_classifier.get_response_template(intent)
            
        else:
            response_data["response"] = "I'm not sure how to help with that. Try asking about your balance, spending, or budget!"
        
        return response_data

    async def _get_account_balances(self) -> str:
        """Get user's account balances"""
        accounts = self.db.query(Account).filter(
            Account.user_id == self.user_id,
            Account.is_active == True
        ).all()
        
        if not accounts:
            return "You don't have any active accounts."
        
        balance_text = ""
        total_balance = 0
        
        for account in accounts:
            balance_text += f"• {account.name}: ${account.current_balance:,.2f}\n"
            if account.account_type.value != "credit_card":
                total_balance += float(account.current_balance)
        
        balance_text += f"\nTotal Balance: ${total_balance:,.2f}"
        
        return balance_text

    async def _get_balance_chart_data(self) -> Dict[str, Any]:
        """Get chart data for account balances"""
        accounts = self.db.query(Account).filter(
            Account.user_id == self.user_id,
            Account.is_active == True
        ).all()
        
        chart_data = {
            "type": "pie",
            "title": "Account Balances",
            "data": {
                "labels": [account.name for account in accounts],
                "values": [float(account.current_balance) for account in accounts]
            }
        }
        
        return chart_data

    async def _get_spending_analysis(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Get spending analysis based on entities"""
        # Default to last 30 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        # Check if user specified a date range
        if "dates" in entities:
            # Parse dates (simplified - would need proper date parsing)
            pass
        
        # Get transactions
        transactions = self.db.query(Transaction).join(Account).filter(
            Account.user_id == self.user_id,
            Transaction.transaction_type == TransactionType.EXPENSE,
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date <= end_date
        ).all()
        
        if not transactions:
            return {
                "text": "No expenses found for the specified period.",
                "chart_data": None
            }
        
        # Calculate category totals
        category_totals = {}
        total_spent = 0
        
        for transaction in transactions:
            category = transaction.category.value
            amount = float(transaction.amount)
            category_totals[category] = category_totals.get(category, 0) + amount
            total_spent += amount
        
        # Generate response text
        response_text = f"Spending Analysis (Last 30 Days):\n"
        response_text += f"Total Spent: ${total_spent:,.2f}\n\n"
        response_text += "Top Categories:\n"
        
        sorted_categories = sorted(category_totals.items(), key=lambda x: x[1], reverse=True)
        for category, amount in sorted_categories[:5]:
            percentage = (amount / total_spent) * 100
            response_text += f"• {category.replace('_', ' ').title()}: ${amount:,.2f} ({percentage:.1f}%)\n"
        
        # Generate chart data
        chart_data = {
            "type": "doughnut",
            "title": "Spending by Category",
            "data": {
                "labels": [cat.replace('_', ' ').title() for cat, _ in sorted_categories],
                "values": [amount for _, amount in sorted_categories]
            }
        }
        
        return {
            "text": response_text,
            "chart_data": chart_data
        }

    async def _get_budget_advice(self) -> str:
        """Get budget advice based on user's spending patterns"""
        # Get recent spending
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        transactions = self.db.query(Transaction).join(Account).filter(
            Account.user_id == self.user_id,
            Transaction.transaction_type == TransactionType.EXPENSE,
            Transaction.transaction_date >= start_date
        ).all()
        
        if not transactions:
            return "I need some transaction data to provide budget advice. Start by adding some expenses!"
        
        total_spent = sum(float(t.amount) for t in transactions)
        monthly_average = total_spent  # Simplified - would calculate proper average
        
        advice = f"Budget Advice:\n\n"
        advice += f"Your monthly spending: ${monthly_average:,.2f}\n\n"
        
        advice += "Recommendations:\n"
        advice += f"• Emergency fund goal: ${monthly_average * 3:,.2f} (3 months expenses)\n"
        advice += f"• Suggested monthly savings: ${monthly_average * 0.2:,.2f} (20% of expenses)\n"
        advice += "• Consider the 50/30/20 rule: 50% needs, 30% wants, 20% savings\n"
        advice += "• Review your largest expense categories for potential savings"
        
        return advice

    async def _get_savings_advice(self) -> str:
        """Get personalized savings advice"""
        # Analyze income vs expenses
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        income_total = self.db.query(func.sum(Transaction.amount)).join(Account).filter(
            Account.user_id == self.user_id,
            Transaction.transaction_type == TransactionType.INCOME,
            Transaction.transaction_date >= start_date
        ).scalar() or 0
        
        expense_total = self.db.query(func.sum(Transaction.amount)).join(Account).filter(
            Account.user_id == self.user_id,
            Transaction.transaction_type == TransactionType.EXPENSE,
            Transaction.transaction_date >= start_date
        ).scalar() or 0
        
        net_income = float(income_total) - float(expense_total)
        
        advice = f"Savings Analysis:\n\n"
        advice += f"Monthly Income: ${income_total:,.2f}\n"
        advice += f"Monthly Expenses: ${expense_total:,.2f}\n"
        advice += f"Net Income: ${net_income:,.2f}\n\n"
        
        if net_income > 0:
            advice += f"Great! You have ${net_income:,.2f} left over each month.\n\n"
            advice += "Savings Suggestions:\n"
            advice += f"• Emergency fund: Save ${net_income * 0.5:,.2f}/month\n"
            advice += f"• Long-term goals: Save ${net_income * 0.3:,.2f}/month\n"
            advice += f"• Fun money: Keep ${net_income * 0.2:,.2f}/month flexible"
        else:
            advice += "You're spending more than you earn. Consider:\n"
            advice += "• Review your largest expenses\n"
            advice += "• Look for subscription services to cancel\n"
            advice += "• Find ways to increase your income"
        
        return advice

    async def _search_transactions(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Search transactions based on entities"""
        query = self.db.query(Transaction).join(Account).filter(
            Account.user_id == self.user_id
        )
        
        # Apply filters based on entities
        if "amounts" in entities:
            # Search for transactions near specified amounts
            amounts = entities["amounts"]
            amount_conditions = []
            for amount in amounts:
                # Search within 10% of the amount
                lower_bound = amount * 0.9
                upper_bound = amount * 1.1
                amount_conditions.append(
                    Transaction.amount.between(lower_bound, upper_bound)
                )
            if amount_conditions:
                from sqlalchemy import or_
                query = query.filter(or_(*amount_conditions))
        
        if "categories" in entities:
            # Search for specific categories
            category_keywords = entities["categories"]
            # This would map keywords to TransactionCategory enums
            pass
        
        # Limit results
        transactions = query.order_by(desc(Transaction.transaction_date)).limit(10).all()
        
        if not transactions:
            return {
                "text": "No transactions found matching your criteria.",
                "actions": None
            }
        
        response_text = f"Found {len(transactions)} recent transactions:\n\n"
        for transaction in transactions:
            response_text += f"• {transaction.transaction_date.strftime('%m/%d')} - "
            response_text += f"{transaction.description}: ${transaction.amount:,.2f}\n"
        
        return {
            "text": response_text,
            "actions": [
                {"type": "view_transaction", "id": t.id, "label": f"View ${t.amount}"}
                for t in transactions[:3]
            ]
        }

    async def _get_financial_goals_info(self) -> str:
        """Get information about financial goals"""
        # This would query the goals table
        return ("Financial Goals Help:\n\n"
                "I can help you set and track goals like:\n"
                "• Emergency fund (3-6 months expenses)\n"
                "• Vacation savings\n"
                "• Home down payment\n"
                "• Debt payoff\n"
                "• Retirement savings\n\n"
                "Would you like to create a new goal or check progress on existing ones?")

    async def _get_bill_reminders(self) -> str:
        """Get upcoming bill reminders"""
        # This would query recurring transactions or bill reminders
        return ("Upcoming Bills (Mock Data):\n\n"
                "• Electric Bill - Due in 5 days - $89.45\n"
                "• Credit Card - Due in 8 days - $234.67\n"
                "• Internet Service - Due in 12 days - $79.99\n"
                "• Phone Bill - Due in 15 days - $65.00\n\n"
                "Would you like me to set up automatic reminders?")

    async def _get_export_options(self) -> str:
        """Get export options information"""
        return ("Export Options:\n\n"
                "I can generate reports in these formats:\n"
                "• PDF - Detailed financial summary with charts\n"
                "• Excel - Transaction data for analysis\n"
                "• CSV - Raw transaction data\n\n"
                "What type of report would you like?")

    async def _store_conversation_message(
        self, 
        conversation_id: str, 
        user_message: str, 
        bot_response: str, 
        intent: str
    ):
        """Store conversation message (placeholder - would save to database)"""
        # In a real app, you'd save to a conversations table
        pass

    async def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get user's conversation history"""
        # Placeholder - would query conversation database
        return [
            {
                "conversation_id": "conv-1",
                "started_at": "2024-01-15T10:30:00Z",
                "last_message": "What's my balance?",
                "message_count": 5
            }
        ]

    async def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation"""
        # Placeholder - would delete from database
        return True

    async def get_personalized_suggestions(self) -> List[str]:
        """Get personalized chat suggestions"""
        suggestions = [
            "What's my spending this month?",
            "Show me my account balances",
            "Help me create a budget",
            "What are my upcoming bills?",
            "How can I save more money?"
        ]
        
        # Could make these more personalized based on user data
        return suggestions

    async def record_feedback(self, feedback_data: Dict[str, Any]):
        """Record user feedback on chatbot responses"""
        # Would save feedback to database for model improvement
        pass