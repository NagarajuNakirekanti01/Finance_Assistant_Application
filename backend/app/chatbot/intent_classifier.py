"""
Chatbot Intent Classification using spaCy
"""

import spacy
import json
import os
from typing import Dict, Any, List, Tuple
import re

class IntentClassifier:
    def __init__(self):
        # Load spaCy model
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            print("spaCy model not found. Please install: python -m spacy download en_core_web_sm")
            self.nlp = None
        
        # Define intents and their patterns
        self.intents = {
            "greeting": {
                "patterns": [
                    "hello", "hi", "hey", "good morning", "good afternoon", 
                    "good evening", "greetings", "what's up", "howdy"
                ],
                "responses": [
                    "Hello! I'm your personal finance assistant. How can I help you today?",
                    "Hi there! I'm here to help you manage your finances. What would you like to know?",
                    "Greetings! I can help you with budgets, transactions, and financial insights."
                ]
            },
            "balance_inquiry": {
                "patterns": [
                    "what's my balance", "show balance", "account balance", "how much money",
                    "current balance", "balance check", "money left", "account total"
                ],
                "responses": [
                    "Let me check your account balances for you.",
                    "I'll retrieve your current account balances."
                ]
            },
            "spending_analysis": {
                "patterns": [
                    "spending analysis", "where did I spend", "spending breakdown", "expense report",
                    "spending summary", "money spent on", "spending patterns", "expense analysis"
                ],
                "responses": [
                    "I'll analyze your spending patterns for you.",
                    "Let me break down your expenses by category."
                ]
            },
            "budget_help": {
                "patterns": [
                    "budget help", "create budget", "budget advice", "budgeting tips",
                    "how to budget", "budget planning", "budget management", "budget recommendation"
                ],
                "responses": [
                    "I'd be happy to help you with budgeting!",
                    "Let me provide some budget recommendations based on your spending."
                ]
            },
            "savings_advice": {
                "patterns": [
                    "saving money", "savings advice", "how to save", "savings tips",
                    "save more money", "savings plan", "savings goal", "emergency fund"
                ],
                "responses": [
                    "I can help you create a savings plan!",
                    "Let me analyze your spending to find savings opportunities."
                ]
            },
            "transaction_search": {
                "patterns": [
                    "find transaction", "search transactions", "look for payment", "transaction history",
                    "find purchase", "search spending", "transaction details", "payment history"
                ],
                "responses": [
                    "I'll search your transaction history for you.",
                    "Let me find the transactions you're looking for."
                ]
            },
            "financial_goals": {
                "patterns": [
                    "financial goals", "set goal", "savings goal", "financial planning",
                    "goal tracking", "achieve goal", "financial targets", "money goals"
                ],
                "responses": [
                    "I can help you set and track your financial goals!",
                    "Let's work on your financial goal planning."
                ]
            },
            "investment_advice": {
                "patterns": [
                    "investment advice", "should I invest", "investment tips", "portfolio",
                    "stocks", "bonds", "investing money", "investment strategy"
                ],
                "responses": [
                    "I can provide general investment guidance based on your financial situation.",
                    "Let me help you understand your investment options."
                ]
            },
            "bill_reminders": {
                "patterns": [
                    "bill reminders", "upcoming bills", "bill due dates", "payment reminders",
                    "bill schedule", "payment due", "bill notifications", "recurring payments"
                ],
                "responses": [
                    "I'll check your upcoming bill due dates.",
                    "Let me show you your bill payment schedule."
                ]
            },
            "export_data": {
                "patterns": [
                    "export data", "download report", "export transactions", "generate report",
                    "export to excel", "pdf report", "download statements", "export csv"
                ],
                "responses": [
                    "I can help you export your financial data.",
                    "What type of report would you like to generate?"
                ]
            },
            "help": {
                "patterns": [
                    "help", "what can you do", "commands", "features", "assistance",
                    "how to use", "capabilities", "options", "support"
                ],
                "responses": [
                    "I can help you with:\n• Account balances\n• Spending analysis\n• Budget planning\n• Savings advice\n• Transaction search\n• Financial goals\n• Bill reminders\n• Export reports",
                    "I'm your financial assistant! I can analyze spending, help with budgets, track goals, and much more."
                ]
            },
            "goodbye": {
                "patterns": [
                    "goodbye", "bye", "see you later", "talk to you later", "farewell",
                    "good night", "take care", "until next time", "see ya", "adios"
                ],
                "responses": [
                    "Goodbye! Feel free to ask me anything about your finances anytime.",
                    "Take care! I'm here whenever you need financial assistance.",
                    "See you later! Remember to check your budget regularly."
                ]
            }
        }

    def classify_intent(self, message: str) -> Tuple[str, float, List[str]]:
        """
        Classify the intent of a user message
        Returns: (intent, confidence, entities)
        """
        if not self.nlp:
            return "unknown", 0.0, []
        
        message_lower = message.lower()
        
        # Extract entities using spaCy
        doc = self.nlp(message)
        entities = []
        
        for ent in doc.ents:
            entities.append({
                "text": ent.text,
                "label": ent.label_,
                "start": ent.start_char,
                "end": ent.end_char
            })
        
        # Simple pattern matching for intent classification
        best_intent = "unknown"
        best_score = 0.0
        
        for intent, data in self.intents.items():
            score = self._calculate_intent_score(message_lower, data["patterns"])
            if score > best_score:
                best_score = score
                best_intent = intent
        
        # If no good match found, classify as unknown
        if best_score < 0.3:
            best_intent = "unknown"
            best_score = 0.0
        
        return best_intent, best_score, entities

    def _calculate_intent_score(self, message: str, patterns: List[str]) -> float:
        """Calculate similarity score between message and intent patterns"""
        message_words = set(message.split())
        
        max_score = 0.0
        
        for pattern in patterns:
            pattern_words = set(pattern.split())
            
            # Calculate Jaccard similarity
            intersection = message_words.intersection(pattern_words)
            union = message_words.union(pattern_words)
            
            if union:
                score = len(intersection) / len(union)
                max_score = max(max_score, score)
            
            # Boost score if pattern is a substring of message
            if pattern in message:
                max_score = max(max_score, 0.8)
        
        return max_score

    def get_response_template(self, intent: str) -> str:
        """Get a response template for the given intent"""
        if intent in self.intents:
            responses = self.intents[intent]["responses"]
            import random
            return random.choice(responses)
        
        return "I'm not sure how to help with that. Can you please rephrase your question?"

    def extract_entities(self, message: str) -> Dict[str, Any]:
        """Extract specific entities like dates, amounts, categories"""
        if not self.nlp:
            return {}
        
        doc = self.nlp(message)
        entities = {}
        
        # Extract monetary amounts
        money_pattern = re.compile(r'\$?(\d+(?:,\d{3})*(?:\.\d{2})?)')
        amounts = money_pattern.findall(message)
        if amounts:
            entities['amounts'] = [float(amount.replace(',', '')) for amount in amounts]
        
        # Extract dates
        dates = []
        for ent in doc.ents:
            if ent.label_ in ["DATE", "TIME"]:
                dates.append(ent.text)
        if dates:
            entities['dates'] = dates
        
        # Extract categories (predefined list)
        categories = [
            "food", "dining", "restaurant", "grocery", "shopping", "gas", "transportation",
            "entertainment", "bills", "utilities", "healthcare", "insurance", "rent",
            "mortgage", "salary", "income", "investment", "savings"
        ]
        
        found_categories = []
        message_lower = message.lower()
        for category in categories:
            if category in message_lower:
                found_categories.append(category)
        
        if found_categories:
            entities['categories'] = found_categories
        
        return entities

# Global instance
intent_classifier = IntentClassifier()