#!/usr/bin/env python3
"""
Script to generate test pantry items for test_user_1
Run this to populate the pantry with realistic items for testing the LLM meal plan generator
"""

import sys
import os
from datetime import datetime, timedelta
import random

# Add the src directory to the path so we can import from it
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Import Flask app and database
from src import create_app
from src.database import get_db
import pymysql

def generate_test_pantry_items():
    """Generate realistic pantry items for test_user_1"""
    
    # Test pantry items with realistic quantities and categories
    pantry_items = [
        # Proteins
        {"name": "chicken breast", "quantity": 2, "unit": "lbs", "category": "Meat", "storage": "fridge", "days_to_expire": 3},
        {"name": "ground beef", "quantity": 1, "unit": "lb", "category": "Meat", "storage": "fridge", "days_to_expire": 2},
        {"name": "salmon fillet", "quantity": 4, "unit": "pcs", "category": "Meat", "storage": "fridge", "days_to_expire": 2},
        {"name": "eggs", "quantity": 12, "unit": "pcs", "category": "Dairy", "storage": "fridge", "days_to_expire": 14},
        {"name": "canned tuna", "quantity": 3, "unit": "cans", "category": "Canned Goods", "storage": "pantry", "days_to_expire": 365},
        {"name": "black beans", "quantity": 2, "unit": "cans", "category": "Canned Goods", "storage": "pantry", "days_to_expire": 730},
        
        # Dairy
        {"name": "milk", "quantity": 1, "unit": "gallon", "category": "Dairy", "storage": "fridge", "days_to_expire": 7},
        {"name": "cheddar cheese", "quantity": 8, "unit": "oz", "category": "Dairy", "storage": "fridge", "days_to_expire": 21},
        {"name": "greek yogurt", "quantity": 32, "unit": "oz", "category": "Dairy", "storage": "fridge", "days_to_expire": 10},
        {"name": "butter", "quantity": 1, "unit": "stick", "category": "Dairy", "storage": "fridge", "days_to_expire": 30},
        
        # Vegetables
        {"name": "broccoli", "quantity": 2, "unit": "heads", "category": "Produce", "storage": "fridge", "days_to_expire": 7},
        {"name": "carrots", "quantity": 1, "unit": "bag", "category": "Produce", "storage": "fridge", "days_to_expire": 14},
        {"name": "onions", "quantity": 3, "unit": "pcs", "category": "Produce", "storage": "pantry", "days_to_expire": 30},
        {"name": "garlic", "quantity": 1, "unit": "bulb", "category": "Produce", "storage": "pantry", "days_to_expire": 21},
        {"name": "bell peppers", "quantity": 4, "unit": "pcs", "category": "Produce", "storage": "fridge", "days_to_expire": 10},
        {"name": "spinach", "quantity": 5, "unit": "oz", "category": "Produce", "storage": "fridge", "days_to_expire": 5},
        {"name": "tomatoes", "quantity": 6, "unit": "pcs", "category": "Produce", "storage": "pantry", "days_to_expire": 7},
        {"name": "potatoes", "quantity": 5, "unit": "lbs", "category": "Produce", "storage": "pantry", "days_to_expire": 21},
        
        # Grains & Carbs
        {"name": "brown rice", "quantity": 2, "unit": "lbs", "category": "Grains", "storage": "pantry", "days_to_expire": 365},
        {"name": "quinoa", "quantity": 1, "unit": "lb", "category": "Grains", "storage": "pantry", "days_to_expire": 365},
        {"name": "whole wheat pasta", "quantity": 1, "unit": "box", "category": "Grains", "storage": "pantry", "days_to_expire": 730},
        {"name": "oatmeal", "quantity": 42, "unit": "oz", "category": "Grains", "storage": "pantry", "days_to_expire": 365},
        {"name": "bread", "quantity": 1, "unit": "loaf", "category": "Bread", "storage": "pantry", "days_to_expire": 5},
        
        # Pantry staples
        {"name": "olive oil", "quantity": 1, "unit": "bottle", "category": "Oils & Vinegars", "storage": "pantry", "days_to_expire": 365},
        {"name": "coconut oil", "quantity": 1, "unit": "jar", "category": "Oils & Vinegars", "storage": "pantry", "days_to_expire": 365},
        {"name": "balsamic vinegar", "quantity": 1, "unit": "bottle", "category": "Condiments", "storage": "pantry", "days_to_expire": 1095},
        {"name": "soy sauce", "quantity": 1, "unit": "bottle", "category": "Condiments", "storage": "pantry", "days_to_expire": 1095},
        {"name": "honey", "quantity": 1, "unit": "jar", "category": "Condiments", "storage": "pantry", "days_to_expire": 1095},
        
        # Spices & Seasonings
        {"name": "salt", "quantity": 1, "unit": "container", "category": "Spices", "storage": "pantry", "days_to_expire": 1825},
        {"name": "black pepper", "quantity": 1, "unit": "container", "category": "Spices", "storage": "pantry", "days_to_expire": 1095},
        {"name": "paprika", "quantity": 1, "unit": "container", "category": "Spices", "storage": "pantry", "days_to_expire": 1095},
        {"name": "cumin", "quantity": 1, "unit": "container", "category": "Spices", "storage": "pantry", "days_to_expire": 1095},
        {"name": "oregano", "quantity": 1, "unit": "container", "category": "Spices", "storage": "pantry", "days_to_expire": 1095},
        {"name": "basil", "quantity": 1, "unit": "container", "category": "Spices", "storage": "pantry", "days_to_expire": 1095},
        
        # Fruits
        {"name": "bananas", "quantity": 6, "unit": "pcs", "category": "Produce", "storage": "pantry", "days_to_expire": 5},
        {"name": "apples", "quantity": 4, "unit": "pcs", "category": "Produce", "storage": "fridge", "days_to_expire": 14},
        {"name": "lemons", "quantity": 3, "unit": "pcs", "category": "Produce", "storage": "fridge", "days_to_expire": 21},
        
        # Frozen items
        {"name": "frozen mixed vegetables", "quantity": 1, "unit": "bag", "category": "Frozen Foods", "storage": "freezer", "days_to_expire": 365},
        {"name": "frozen berries", "quantity": 1, "unit": "bag", "category": "Frozen Foods", "storage": "freezer", "days_to_expire": 365},
        
        # Canned/Jarred items
        {"name": "canned tomatoes", "quantity": 2, "unit": "cans", "category": "Canned Goods", "storage": "pantry", "days_to_expire": 730},
        {"name": "chicken broth", "quantity": 2, "unit": "cartons", "category": "Canned Goods", "storage": "pantry", "days_to_expire": 365},
        {"name": "coconut milk", "quantity": 1, "unit": "can", "category": "Canned Goods", "storage": "pantry", "days_to_expire": 730},
        
        # Nuts & Seeds
        {"name": "almonds", "quantity": 1, "unit": "bag", "category": "Snacks", "storage": "pantry", "days_to_expire": 180},
        {"name": "chia seeds", "quantity": 1, "unit": "bag", "category": "Baking Supplies", "storage": "pantry", "days_to_expire": 365},
        
        # Baking
        {"name": "flour", "quantity": 5, "unit": "lbs", "category": "Baking Supplies", "storage": "pantry", "days_to_expire": 365},
        {"name": "baking powder", "quantity": 1, "unit": "container", "category": "Baking Supplies", "storage": "pantry", "days_to_expire": 548},
        {"name": "vanilla extract", "quantity": 1, "unit": "bottle", "category": "Baking Supplies", "storage": "pantry", "days_to_expire": 1825},
    ]
    
    return pantry_items

def insert_pantry_items():
    """Insert test pantry items into the database"""
    user_id = "test_user_1"
    
    # Create Flask application context
    app = create_app()
    
    with app.app_context():
        try:
            # Get database connection
            db = get_db()
            cursor = db.cursor()
            
            # Check if user exists
            cursor.execute("SELECT user_ID FROM user_account WHERE user_ID = %s", (user_id,))
            if not cursor.fetchone():
                print(f"User {user_id} not found. Please create the user first.")
                return False
            
            # Clear existing pantry items for this user
            cursor.execute("DELETE FROM pantry_items WHERE user_id = %s", (user_id,))
            print(f"Cleared existing pantry items for {user_id}")
            
            # Generate test items
            items = generate_test_pantry_items()
            
            # Insert each item
            for item in items:
                # Calculate expiration date
                expiration_date = None
                if item["days_to_expire"]:
                    expiration_date = (datetime.now() + timedelta(days=item["days_to_expire"])).date()
                
                query = """
                    INSERT INTO pantry_items (
                        user_id, item_name, quantity, unit, category, storage_type,
                        expiration_date, source_type, is_ai_predicted_expiry, notes
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                
                cursor.execute(query, (
                    user_id,
                    item["name"],
                    item["quantity"],
                    item["unit"],
                    item["category"],
                    item["storage"],
                    expiration_date,
                    'manual',
                    False,
                    'Generated for testing LLM meal plans'
                ))
            
            db.commit()
            cursor.close()
            
            print(f"\n✅ Successfully added {len(items)} pantry items for {user_id}!")
            print("\nSample items added:")
            for i, item in enumerate(items[:10]):
                print(f"  • {item['name']} ({item['quantity']} {item['unit']})")
            if len(items) > 10:
                print(f"  ... and {len(items) - 10} more items")
            
            print(f"\n🧪 Now you can test the LLM meal plan generator with a well-stocked pantry!")
            print(f"📱 Visit the meal plans page and generate a plan to see the AI use these ingredients.")
            
            return True
            
        except Exception as e:
            print(f"❌ Error inserting pantry items: {str(e)}")
            return False

if __name__ == "__main__":
    print("🍽️  Generating test pantry items for LLM meal plan testing...")
    print("=" * 60)
    
    success = insert_pantry_items()
    
    if success:
        print("\n" + "=" * 60)
        print("✅ Test data generation complete!")
        print("\nNext steps:")
        print("1. Login as test_user_1")
        print("2. Go to Meal Plans page")
        print("3. Generate a weekly plan")
        print("4. Watch the AI use your pantry ingredients!")
    else:
        print("\n❌ Failed to generate test data. Check the error messages above.")