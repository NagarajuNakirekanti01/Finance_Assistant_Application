"""
Transaction Categorization ML Model
"""

import pickle
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from typing import Dict, Any, List
import re
import os

from app.models.transaction import TransactionCategory

class TransactionCategorizer:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            ngram_range=(1, 2),
            stop_words='english'
        )
        self.classifier = RandomForestClassifier(
            n_estimators=100,
            random_state=42,
            max_depth=10
        )
        self.is_trained = False
        self.model_path = "app/ml_models/categorizer_model.pkl"
        
        # Load model if exists
        self._load_model()

    def preprocess_text(self, description: str, merchant_name: str = None) -> str:
        """Preprocess transaction description and merchant name"""
        text = description.lower()
        
        if merchant_name:
            text += " " + merchant_name.lower()
        
        # Remove special characters and numbers
        text = re.sub(r'[^a-zA-Z\s]', ' ', text)
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        return text

    def extract_features(self, descriptions: List[str], amounts: List[float] = None) -> np.ndarray:
        """Extract features from transaction descriptions"""
        # Text features using TF-IDF
        text_features = self.vectorizer.fit_transform(descriptions)
        
        if amounts is not None:
            # Amount features
            amount_features = np.array(amounts).reshape(-1, 1)
            
            # Combine text and amount features
            from scipy.sparse import hstack
            features = hstack([text_features, amount_features])
            return features
        
        return text_features

    def train_model(self, training_data: List[Dict[str, Any]]):
        """Train the categorization model"""
        if not training_data:
            # Use mock training data for demonstration
            training_data = self._get_mock_training_data()
        
        # Prepare data
        descriptions = []
        amounts = []
        categories = []
        
        for item in training_data:
            processed_desc = self.preprocess_text(
                item['description'],
                item.get('merchant_name')
            )
            descriptions.append(processed_desc)
            amounts.append(item['amount'])
            categories.append(item['category'])
        
        # Extract features
        X = self.extract_features(descriptions, amounts)
        y = categories
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Train model
        self.classifier.fit(X_train, y_train)
        
        # Evaluate
        y_pred = self.classifier.predict(X_test)
        print("Model Performance:")
        print(classification_report(y_test, y_pred))
        
        self.is_trained = True
        self._save_model()

    def predict_category(
        self,
        description: str,
        amount: float,
        merchant_name: str = None
    ) -> Dict[str, Any]:
        """Predict transaction category"""
        if not self.is_trained:
            # Return default category with low confidence
            return {
                "category": TransactionCategory.OTHER_EXPENSE,
                "subcategory": None,
                "confidence": 0.1
            }
        
        # Preprocess
        processed_desc = self.preprocess_text(description, merchant_name)
        
        # Extract features
        text_features = self.vectorizer.transform([processed_desc])
        amount_features = np.array([[amount]])
        
        from scipy.sparse import hstack
        features = hstack([text_features, amount_features])
        
        # Predict
        prediction = self.classifier.predict(features)[0]
        probabilities = self.classifier.predict_proba(features)[0]
        confidence = max(probabilities)
        
        # Determine subcategory based on keywords
        subcategory = self._determine_subcategory(description, merchant_name, prediction)
        
        return {
            "category": TransactionCategory(prediction),
            "subcategory": subcategory,
            "confidence": float(confidence)
        }

    def _determine_subcategory(
        self,
        description: str,
        merchant_name: str,
        category: str
    ) -> str:
        """Determine subcategory based on keywords"""
        text = (description + " " + (merchant_name or "")).lower()
        
        subcategory_keywords = {
            "food_dining": {
                "restaurant": ["restaurant", "cafe", "bistro", "grill"],
                "fast_food": ["mcdonalds", "burger", "pizza", "subway"],
                "grocery": ["grocery", "supermarket", "walmart", "target"],
                "coffee": ["starbucks", "coffee", "dunkin"]
            },
            "shopping": {
                "clothing": ["clothing", "apparel", "fashion", "shoes"],
                "electronics": ["electronics", "apple", "best buy", "amazon"],
                "household": ["home", "furniture", "kitchen", "bath"]
            },
            "transportation": {
                "gas": ["gas", "fuel", "exxon", "shell", "bp"],
                "public_transit": ["metro", "bus", "train", "uber", "lyft"],
                "parking": ["parking", "toll"]
            }
        }
        
        category_map = subcategory_keywords.get(category, {})
        
        for subcategory, keywords in category_map.items():
            if any(keyword in text for keyword in keywords):
                return subcategory
        
        return None

    def _get_mock_training_data(self) -> List[Dict[str, Any]]:
        """Generate mock training data for demonstration"""
        return [
            # Food & Dining
            {"description": "MCDONALD'S #123", "merchant_name": "McDonald's", "amount": 8.50, "category": "food_dining"},
            {"description": "STARBUCKS COFFEE", "merchant_name": "Starbucks", "amount": 5.25, "category": "food_dining"},
            {"description": "WHOLE FOODS MARKET", "merchant_name": "Whole Foods", "amount": 67.89, "category": "food_dining"},
            {"description": "RESTAURANT PAYMENT", "merchant_name": "Local Bistro", "amount": 45.00, "category": "food_dining"},
            
            # Shopping
            {"description": "AMAZON PURCHASE", "merchant_name": "Amazon", "amount": 29.99, "category": "shopping"},
            {"description": "TARGET STORE", "merchant_name": "Target", "amount": 56.78, "category": "shopping"},
            {"description": "APPLE STORE ONLINE", "merchant_name": "Apple", "amount": 199.00, "category": "shopping"},
            
            # Transportation
            {"description": "SHELL GAS STATION", "merchant_name": "Shell", "amount": 35.00, "category": "transportation"},
            {"description": "UBER RIDE", "merchant_name": "Uber", "amount": 12.50, "category": "transportation"},
            {"description": "METRO TRANSIT", "merchant_name": "Metro", "amount": 2.75, "category": "transportation"},
            
            # Bills & Utilities
            {"description": "ELECTRIC BILL PAYMENT", "merchant_name": "Electric Company", "amount": 89.45, "category": "bills_utilities"},
            {"description": "INTERNET SERVICE", "merchant_name": "Comcast", "amount": 79.99, "category": "bills_utilities"},
            {"description": "PHONE BILL", "merchant_name": "Verizon", "amount": 65.00, "category": "bills_utilities"},
            
            # Entertainment
            {"description": "NETFLIX SUBSCRIPTION", "merchant_name": "Netflix", "amount": 15.99, "category": "entertainment"},
            {"description": "MOVIE THEATER", "merchant_name": "AMC", "amount": 24.00, "category": "entertainment"},
            {"description": "SPOTIFY PREMIUM", "merchant_name": "Spotify", "amount": 9.99, "category": "entertainment"},
            
            # Healthcare
            {"description": "PHARMACY PRESCRIPTION", "merchant_name": "CVS", "amount": 25.50, "category": "healthcare"},
            {"description": "DOCTOR VISIT COPAY", "merchant_name": "Medical Center", "amount": 30.00, "category": "healthcare"},
            
            # Income
            {"description": "SALARY DEPOSIT", "merchant_name": "Employer", "amount": 3500.00, "category": "salary"},
            {"description": "FREELANCE PAYMENT", "merchant_name": "Client", "amount": 500.00, "category": "freelance"},
            
        ] * 10  # Multiply to have more training data

    def _save_model(self):
        """Save trained model to disk"""
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        
        model_data = {
            'vectorizer': self.vectorizer,
            'classifier': self.classifier,
            'is_trained': self.is_trained
        }
        
        with open(self.model_path, 'wb') as f:
            pickle.dump(model_data, f)

    def _load_model(self):
        """Load trained model from disk"""
        if os.path.exists(self.model_path):
            try:
                with open(self.model_path, 'rb') as f:
                    model_data = pickle.load(f)
                
                self.vectorizer = model_data['vectorizer']
                self.classifier = model_data['classifier']
                self.is_trained = model_data['is_trained']
                
                print("Loaded existing transaction categorization model")
            except Exception as e:
                print(f"Error loading model: {e}")
                # Train a new model
                self.train_model([])
        else:
            # Train a new model
            print("No existing model found, training new model...")
            self.train_model([])

# Initialize global instance
categorizer = TransactionCategorizer()