from flask import Blueprint, request, jsonify, session, current_app
import requests
from src.database import get_db
from src import helper

meal_plan_bp = Blueprint("meal_plan", __name__, url_prefix="/api")


@meal_plan_bp.route("/generate-meal-plan", methods=["POST"])
def generate_meal_plan():
    """Generate a weekly meal plan using AI based on user inputs"""
    if "user_ID" not in session:
        return jsonify({"success": False, "message": "Not authenticated"})

    data = request.get_json()
    user_id = session["user_ID"]

    # Required fields
    days = data.get("days", 7)

    # Optional fields with defaults
    ingredients = data.get("ingredients", [])  # Available pantry ingredients
    dietary_preference = data.get("dietary_preference", "none")
    budget = data.get("budget")  # Budget limit per week
    cooking_time = data.get("cooking_time", 60)  # Max cooking time per day in minutes

    try:
        days = int(days)
        if days < 1 or days > 14:
            return jsonify(
                {"success": False, "message": "Days must be between 1 and 14"}
            )
    except (ValueError, TypeError):
        return jsonify({"success": False, "message": "Invalid number of days"})

    try:
        cooking_time = int(cooking_time)
        if cooking_time < 10 or cooking_time > 300:
            return jsonify(
                {
                    "success": False,
                    "message": "Cooking time must be between 10 and 300 minutes",
                }
            )
    except (ValueError, TypeError):
        return jsonify({"success": False, "message": "Invalid cooking time"})

    if budget:
        try:
            budget = float(budget)
            if budget < 10 or budget > 1000:
                return jsonify(
                    {
                        "success": False,
                        "message": "Budget must be between $10 and $1000",
                    }
                )
        except (ValueError, TypeError):
            return jsonify({"success": False, "message": "Invalid budget amount"})

    db = get_db()
    cursor = db.cursor()

    try:
        # Get user's pantry items for ingredient context
        if not ingredients:
            pantry_query = """
                SELECT item_name, quantity, unit, storage_type, expiration_date
                FROM pantry_items 
                WHERE user_id = %s AND is_consumed = FALSE
                ORDER BY expiration_date ASC
            """
            cursor.execute(pantry_query, (user_id,))
            pantry_items = cursor.fetchall()
            ingredients = [
                f"{item['item_name']} ({item['quantity']} {item['unit']})"
                for item in pantry_items[:20]
            ]  # Limit to 20 items

        # Generate meal plan using Gemini AI
        meal_plan_data = generate_meal_plan_with_ai(
            days=days,
            ingredients=ingredients,
            dietary_preference=dietary_preference,
            budget=budget,
            cooking_time=cooking_time,
        )

        if not meal_plan_data:
            return jsonify(
                {
                    "success": False,
                    "message": "Failed to generate meal plan. Please try again.",
                }
            )

        # Save meal plan to database
        from datetime import datetime, timedelta

        start_date = datetime.now().date()
        end_date = start_date + timedelta(days=days - 1)

        plan_name = f"AI Meal Plan - {start_date.strftime('%b %d')}"

        # Insert meal plan
        plan_query = """
            INSERT INTO meal_plans (
                user_id, plan_name, start_date, end_date, total_days,
                dietary_preference, budget_limit, max_cooking_time, generation_prompt
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        generation_prompt = f"Generated plan for {days} days with {len(ingredients)} ingredients, {dietary_preference} diet, ${budget} budget, {cooking_time}min cooking time"

        cursor.execute(
            plan_query,
            (
                user_id,
                plan_name,
                start_date,
                end_date,
                days,
                dietary_preference,
                budget,
                cooking_time,
                generation_prompt,
            ),
        )
        plan_id = cursor.lastrowid

        # Insert recipes and ingredients
        for day_num, day_data in enumerate(meal_plan_data.get("days", []), 1):
            for meal_type in ["breakfast", "lunch", "dinner"]:
                if meal_type in day_data:
                    recipe_data = day_data[meal_type]

                    # Insert recipe
                    recipe_query = """
                        INSERT INTO recipes (
                            plan_id, meal_type, day_number, recipe_name, description,
                            prep_time, cook_time, servings, estimated_cost, difficulty,
                            calories_per_serving, instructions, notes
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    cursor.execute(
                        recipe_query,
                        (
                            plan_id,
                            meal_type,
                            day_num,
                            recipe_data.get("name", ""),
                            recipe_data.get("description", ""),
                            recipe_data.get("prep_time", 0),
                            recipe_data.get("cook_time", 0),
                            recipe_data.get("servings", 1),
                            recipe_data.get("cost", 0),
                            recipe_data.get("difficulty", "medium"),
                            recipe_data.get("calories", 0),
                            recipe_data.get("instructions", ""),
                            recipe_data.get("notes", ""),
                        ),
                    )
                    recipe_id = cursor.lastrowid

                    # Insert recipe ingredients
                    for ingredient in recipe_data.get("ingredients", []):
                        ingredient_query = """
                            INSERT INTO recipe_ingredients (
                                recipe_id, ingredient_name, quantity, unit, notes, estimated_cost
                            ) VALUES (%s, %s, %s, %s, %s, %s)
                        """
                        cursor.execute(
                            ingredient_query,
                            (
                                recipe_id,
                                ingredient.get("name", ""),
                                ingredient.get("quantity", 1),
                                ingredient.get("unit", ""),
                                ingredient.get("notes", ""),
                                ingredient.get("cost", 0),
                            ),
                        )

        # Insert batch prep steps
        for step_data in meal_plan_data.get("batch_prep", []):
            step_query = """
                INSERT INTO batch_prep_steps (
                    plan_id, prep_session_name, step_order, description,
                    estimated_time, recipes_involved, equipment_needed, tips
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(
                step_query,
                (
                    plan_id,
                    step_data.get("session_name", "Prep Session"),
                    step_data.get("order", 1),
                    step_data.get("description", ""),
                    step_data.get("time", 30),
                    step_data.get("recipes", ""),
                    step_data.get("equipment", ""),
                    step_data.get("tips", ""),
                ),
            )

        # Generate shopping list from recipes
        generate_shopping_list_from_plan(cursor, plan_id)

        db.commit()

        # Return the generated plan with ID
        meal_plan_data["plan_id"] = plan_id
        meal_plan_data["plan_name"] = plan_name
        meal_plan_data["start_date"] = start_date.strftime("%Y-%m-%d")
        meal_plan_data["end_date"] = end_date.strftime("%Y-%m-%d")

        return jsonify(
            {
                "success": True,
                "meal_plan": meal_plan_data,
                "message": f"Successfully generated {days}-day meal plan",
            }
        )

    except Exception as e:
        db.rollback()
        return jsonify(
            {"success": False, "message": f"Failed to generate meal plan: {str(e)}"}
        )
    finally:
        cursor.close()


def generate_meal_plan_with_ai(
    days, ingredients, dietary_preference, budget, cooking_time
):
    """Use Gemini AI to generate a structured meal plan"""
    import os
    import google.generativeai as genai
    import json

    try:
        # Configure Gemini
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("WARNING: GEMINI_API_KEY not found")
            return None

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash-latest")

        # Format ingredients list
        ingredients_text = (
            ", ".join(ingredients)
            if ingredients
            else "No specific ingredients provided"
        )

        # Create detailed prompt for meal planning
        prompt = f"""You are a professional meal prep consultant. Create a detailed {days}-day meal plan with the following requirements:

REQUIREMENTS:
- Days: {days}
- Available ingredients: {ingredients_text}
- Dietary preference: {dietary_preference}
- Budget limit: ${budget if budget else 'No limit'}
- Max cooking time per day: {cooking_time} minutes
- Include breakfast, lunch, and dinner for each day
- Focus on meal prep efficiency and batch cooking
- Prioritize using available ingredients first

IMPORTANT: Respond with a valid JSON object in exactly this format:

{{
  "days": [
    {{
      "day": 1,
      "breakfast": {{
        "name": "Recipe Name",
        "description": "Brief description",
        "prep_time": 15,
        "cook_time": 20,
        "servings": 2,
        "cost": 4.50,
        "difficulty": "easy",
        "calories": 350,
        "instructions": "Step-by-step cooking instructions",
        "ingredients": [
          {{"name": "eggs", "quantity": 2, "unit": "pcs", "notes": "", "cost": 1.00}},
          {{"name": "bread", "quantity": 2, "unit": "slices", "notes": "whole wheat", "cost": 0.50}}
        ],
        "notes": "Can be prepped night before"
      }},
      "lunch": {{ ... }},
      "dinner": {{ ... }}
    }},
    {{ "day": 2, ... }}
  ],
  "batch_prep": [
    {{
      "session_name": "Sunday Prep Session",
      "order": 1,
      "description": "Wash and chop all vegetables",
      "time": 30,
      "recipes": "Day 1-3 meals",
      "equipment": "Sharp knife, cutting board",
      "tips": "Store in airtight containers"
    }}
  ],
  "summary": {{
    "total_estimated_cost": 45.00,
    "total_prep_time": 120,
    "key_ingredients": ["eggs", "chicken", "rice"],
    "tips": "Batch cook grains on Sunday"
  }}
}}

Requirements for recipes:
- Use available ingredients when possible
- Keep costs realistic
- Include prep and cooking times
- Provide clear instructions
- Consider {dietary_preference} dietary restrictions
- Ensure nutritional balance
- Focus on meal prep efficiency

Generate the complete meal plan now:"""

        # Generate the meal plan
        response = model.generate_content(prompt)
        response_text = response.text.strip()

        # Clean the response to extract just the JSON
        if "```json" in response_text:
            json_start = response_text.find("```json") + 7
            json_end = response_text.find("```", json_start)
            response_text = response_text[json_start:json_end]
        elif "```" in response_text:
            json_start = response_text.find("```") + 3
            json_end = response_text.find("```", json_start)
            response_text = response_text[json_start:json_end]

        # Parse JSON response
        try:
            meal_plan = json.loads(response_text)
            print(
                f"DEBUG: Successfully parsed meal plan with {len(meal_plan.get('days', []))} days"
            )
            return meal_plan
        except json.JSONDecodeError as e:
            print(f"DEBUG: JSON parse error: {str(e)}")
            print(f"DEBUG: Response text: {response_text[:500]}...")
            return None

    except Exception as e:
        print(f"ERROR: Meal plan generation failed: {str(e)}")
        return None


def generate_shopping_list_from_plan(cursor, plan_id):
    """Generate a consolidated shopping list from meal plan recipes"""
    try:
        # Get all ingredients from recipes in this plan
        ingredient_query = """
            SELECT ri.ingredient_name, ri.quantity, ri.unit, ri.estimated_cost
            FROM recipe_ingredients ri
            JOIN recipes r ON ri.recipe_id = r.recipe_id
            WHERE r.plan_id = %s
        """
        cursor.execute(ingredient_query, (plan_id,))
        ingredients = cursor.fetchall()

        # Consolidate ingredients by name
        consolidated = {}
        for ingredient in ingredients:
            name = ingredient["ingredient_name"].lower()
            if name not in consolidated:
                consolidated[name] = {
                    "name": ingredient["ingredient_name"],
                    "total_quantity": 0,
                    "unit": ingredient["unit"],
                    "total_cost": 0,
                    "recipes": [],
                }

            consolidated[name]["total_quantity"] += ingredient["quantity"]
            consolidated[name]["total_cost"] += ingredient["estimated_cost"] or 0

        # Insert consolidated shopping list items
        for item_data in consolidated.values():
            # Simple categorization
            category = categorize_ingredient(item_data["name"])

            shopping_query = """
                INSERT INTO meal_plan_shopping_list (
                    plan_id, ingredient_name, total_quantity, unit,
                    estimated_cost, category, is_pantry_available
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(
                shopping_query,
                (
                    plan_id,
                    item_data["name"],
                    item_data["total_quantity"],
                    item_data["unit"],
                    item_data["total_cost"],
                    category,
                    False,
                ),
            )

    except Exception as e:
        print(f"ERROR: Failed to generate shopping list: {str(e)}")


def categorize_ingredient(ingredient_name):
    """Simple ingredient categorization"""
    name = ingredient_name.lower()

    if any(
        word in name
        for word in [
            "apple",
            "banana",
            "orange",
            "lettuce",
            "tomato",
            "potato",
            "carrot",
            "onion",
        ]
    ):
        return "Produce"
    elif any(word in name for word in ["chicken", "beef", "pork", "fish", "meat"]):
        return "Meat & Seafood"
    elif any(word in name for word in ["milk", "cheese", "yogurt", "butter", "egg"]):
        return "Dairy"
    elif any(word in name for word in ["rice", "pasta", "bread", "flour"]):
        return "Grains"
    elif any(word in name for word in ["oil", "salt", "pepper", "spice"]):
        return "Condiments"
    else:
        return "Other"


@meal_plan_bp.route("/meal-plans", methods=["GET"])
def get_meal_plans():
    """Get all meal plans for the current user"""
    if "user_ID" not in session:
        return jsonify({"success": False, "message": "Not authenticated"})

    user_id = session["user_ID"]
    db = get_db()
    cursor = db.cursor()
    
    try:
        # Get meal plans
        query = """
            SELECT plan_id, plan_name, start_date, end_date, total_days,
                   dietary_preference, budget_limit, max_cooking_time,
                   generated_at, status
            FROM meal_plans 
            WHERE user_id = %s
            ORDER BY generated_at DESC
        """
        cursor.execute(query, (user_id,))
        plans = cursor.fetchall()

        return jsonify({"success": True, "plans": plans})

    except Exception as e:
        return jsonify(
            {"success": False, "message": f"Failed to get meal plans: {str(e)}"}
        )
    finally:
        cursor.close()


@meal_plan_bp.route("/meal-plans/<int:plan_id>", methods=["GET"])
def get_meal_plan_details(plan_id):
    """Get detailed meal plan with recipes and batch prep steps"""
    if "user_ID" not in session:
        return jsonify({"success": False, "message": "Not authenticated"})

    user_id = session["user_ID"]
    db = get_db()
    cursor = db.cursor()

    try:
        # Verify plan belongs to user
        verify_query = "SELECT * FROM meal_plans WHERE plan_id = %s AND user_id = %s"
        cursor.execute(verify_query, (plan_id, user_id))
        plan = cursor.fetchone()

        if not plan:
            return jsonify({"success": False, "message": "Meal plan not found"})

        # Get recipes grouped by day
        recipes_query = """
            SELECT r.*, ri.ingredient_name, ri.quantity, ri.unit, ri.notes as ingredient_notes
            FROM recipes r
            LEFT JOIN recipe_ingredients ri ON r.recipe_id = ri.recipe_id
            WHERE r.plan_id = %s
            ORDER BY r.day_number, r.meal_type, ri.ingredient_id
        """
        cursor.execute(recipes_query, (plan_id,))
        recipe_data = cursor.fetchall()

        # Get batch prep steps
        steps_query = """
            SELECT * FROM batch_prep_steps 
            WHERE plan_id = %s
            ORDER BY prep_session_name, step_order
        """
        cursor.execute(steps_query, (plan_id,))
        prep_steps = cursor.fetchall()

        # Get shopping list
        shopping_query = """
            SELECT * FROM meal_plan_shopping_list 
            WHERE plan_id = %s
            ORDER BY category, ingredient_name
        """
        cursor.execute(shopping_query, (plan_id,))
        shopping_items = cursor.fetchall()

        # Structure the response
        structured_plan = {
            "plan_info": plan,
            "recipes": organize_recipes_by_day(recipe_data),
            "batch_prep": prep_steps,
            "shopping_list": shopping_items,
        }

        return jsonify({"success": True, "meal_plan": structured_plan})

    except Exception as e:
        return jsonify(
            {"success": False, "message": f"Failed to get meal plan: {str(e)}"}
        )
    finally:
        cursor.close()


def organize_recipes_by_day(recipe_data):
    """Organize recipe data by day and meal type"""
    organized = {}

    for row in recipe_data:
        day = row["day_number"]
        meal_type = row["meal_type"]

        if day not in organized:
            organized[day] = {}

        if meal_type not in organized[day]:
            organized[day][meal_type] = {
                "recipe_id": row["recipe_id"],
                "name": row["recipe_name"],
                "description": row["description"],
                "prep_time": row["prep_time"],
                "cook_time": row["cook_time"],
                "servings": row["servings"],
                "estimated_cost": row["estimated_cost"],
                "difficulty": row["difficulty"],
                "calories_per_serving": row["calories_per_serving"],
                "instructions": row["instructions"],
                "notes": row["notes"],
                "ingredients": [],
            }

        # Add ingredient if present
        if row["ingredient_name"]:
            organized[day][meal_type]["ingredients"].append(
                {
                    "name": row["ingredient_name"],
                    "quantity": row["quantity"],
                    "unit": row["unit"],
                    "notes": row["ingredient_notes"],
                }
            )

    return organized