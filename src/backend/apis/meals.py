from flask import Blueprint, request, jsonify, session, current_app
import requests
from src.database import get_db
from src import helper
import json
from datetime import datetime, timedelta

meals_bp = Blueprint("meals", __name__, url_prefix="/api")


@meals_bp.route("/generate-meal-plan", methods=["POST"])
def generate_meal_plan():
    """Generate a meal plan and store as individual meals"""
    if "user_ID" not in session:
        return jsonify({"success": False, "message": "Not authenticated"})

    data = request.get_json()
    user_id = session["user_ID"]

    # Required fields
    days = data.get("days", 7)
    start_date = data.get("start_date")  # Optional - defaults to today

    # Optional fields with defaults
    ingredients = data.get("ingredients", [])
    dietary_preference = data.get("dietary_preference", "none")
    budget = data.get("budget")
    cooking_time = data.get("cooking_time", 60)

    try:
        days = int(days)
        if days < 1 or days > 7:
            return jsonify({"success": False, "message": "Days must be between 1 and 7"})
    except (ValueError, TypeError):
        return jsonify({"success": False, "message": "Invalid number of days"})

    # Parse start date or use today
    if start_date:
        try:
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"success": False, "message": "Invalid start date format. Use YYYY-MM-DD"})
    else:
        start_date = datetime.now().date()

    end_date = start_date + timedelta(days=days - 1)

    try:
        cooking_time = int(cooking_time)
        if cooking_time < 10 or cooking_time > 300:
            return jsonify({"success": False, "message": "Cooking time must be between 10 and 300 minutes"})
    except (ValueError, TypeError):
        return jsonify({"success": False, "message": "Invalid cooking time"})

    if budget:
        try:
            budget = float(budget)
            if budget < 10 or budget > 1000:
                return jsonify({"success": False, "message": "Budget must be between $10 and $1000"})
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
            ]

        # Check for existing meals in date range and respect locked meals
        existing_meals_query = """
            SELECT meal_date, meal_type, is_locked 
            FROM meals 
            WHERE user_id = %s AND meal_date BETWEEN %s AND %s
        """
        cursor.execute(existing_meals_query, (user_id, start_date, end_date))
        existing_meals = cursor.fetchall()
        
        # Create set of locked/existing meal slots
        blocked_slots = set()
        for meal in existing_meals:
            if meal['is_locked']:
                blocked_slots.add((meal['meal_date'], meal['meal_type']))

        # Generate meal plan using AI
        meal_plan_data = generate_meal_plan_with_ai(
            days=days,
            start_date=start_date,
            ingredients=ingredients,
            dietary_preference=dietary_preference,
            budget=budget,
            cooking_time=cooking_time,
            blocked_slots=blocked_slots
        )

        if not meal_plan_data:
            return jsonify({"success": False, "message": "Failed to generate meal plan. Please try again."})

        # Create meal plan session
        session_name = f"AI Meal Plan - {start_date.strftime('%b %d')}"
        generation_prompt = f"Generated plan for {days} days with {len(ingredients)} ingredients, {dietary_preference} diet, ${budget} budget, {cooking_time}min cooking time"

        session_query = """
            INSERT INTO meal_plan_sessions (
                user_id, session_name, start_date, end_date, total_days,
                dietary_preference, budget_limit, max_cooking_time, generation_prompt
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(session_query, (
            user_id, session_name, start_date, end_date, days,
            dietary_preference, budget, cooking_time, generation_prompt
        ))
        session_id = cursor.lastrowid

        # Process each day and create individual meals
        created_meals = []
        recipe_template_map = {}

        for day_data in meal_plan_data.get("days", []):
            meal_date = start_date + timedelta(days=day_data.get("day", 1) - 1)
            
            for meal_type in ["breakfast", "lunch", "dinner"]:
                if meal_type in day_data:
                    # Skip if this slot is blocked by existing locked meal
                    if (meal_date, meal_type) in blocked_slots:
                        continue

                    recipe_data = day_data[meal_type]
                    recipe_name = recipe_data.get("name", "")

                    # Get or create recipe template
                    template_id = get_or_create_recipe_template(cursor, recipe_data, meal_type)
                    recipe_template_map[template_id] = recipe_data

                    # Delete existing meal in this slot (if not locked)
                    cursor.execute("""
                        DELETE FROM meals 
                        WHERE user_id = %s AND meal_date = %s AND meal_type = %s AND is_locked = FALSE
                    """, (user_id, meal_date, meal_type))

                    # Create individual meal
                    meal_query = """
                        INSERT INTO meals (
                            user_id, meal_date, meal_type, recipe_template_id, session_id
                        ) VALUES (%s, %s, %s, %s, %s)
                    """
                    cursor.execute(meal_query, (user_id, meal_date, meal_type, template_id, session_id))
                    meal_id = cursor.lastrowid
                    
                    created_meals.append({
                        "meal_id": meal_id,
                        "date": meal_date.strftime("%Y-%m-%d"),
                        "type": meal_type,
                        "recipe_name": recipe_name
                    })

        # Generate session shopping list and batch prep
        generate_session_shopping_list(cursor, session_id, recipe_template_map)
        generate_session_batch_prep(cursor, session_id, meal_plan_data.get("batch_prep", []))

        db.commit()

        return jsonify({
            "success": True,
            "session_id": session_id,
            "session_name": session_name,
            "created_meals": created_meals,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "message": f"Successfully generated {len(created_meals)} meals"
        })

    except Exception as e:
        db.rollback()
        return jsonify({"success": False, "message": f"Failed to generate meal plan: {str(e)}"})
    finally:
        cursor.close()


def get_or_create_recipe_template(cursor, recipe_data, meal_type):
    """Get existing recipe template or create new one"""
    recipe_name = recipe_data.get("name", "")
    instructions = recipe_data.get("instructions", "")
    
    # Check if template already exists
    check_query = """
        SELECT template_id FROM recipe_templates 
        WHERE recipe_name = %s AND meal_type = %s AND instructions = %s
    """
    cursor.execute(check_query, (recipe_name, meal_type, instructions))
    existing = cursor.fetchone()
    
    if existing:
        return existing['template_id']
    
    # Create new template
    template_query = """
        INSERT INTO recipe_templates (
            recipe_name, description, meal_type, prep_time, cook_time,
            servings, estimated_cost, difficulty, calories_per_serving, instructions
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(template_query, (
        recipe_name,
        recipe_data.get("description", ""),
        meal_type,
        recipe_data.get("prep_time", 0),
        recipe_data.get("cook_time", 0),
        recipe_data.get("servings", 1),
        recipe_data.get("cost", 0),
        recipe_data.get("difficulty", "medium"),
        recipe_data.get("calories", 0),
        instructions
    ))
    template_id = cursor.lastrowid
    
    # Add ingredients
    for ingredient in recipe_data.get("ingredients", []):
        ingredient_query = """
            INSERT INTO template_ingredients (
                template_id, ingredient_name, quantity, unit, notes, estimated_cost
            ) VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(ingredient_query, (
            template_id,
            ingredient.get("name", ""),
            ingredient.get("quantity", 1),
            ingredient.get("unit", ""),
            ingredient.get("notes", ""),
            ingredient.get("cost", 0)
        ))
    
    return template_id


@meals_bp.route("/meals", methods=["GET"])
def get_meals():
    """Get meals for date range (for calendar view)"""
    if "user_ID" not in session:
        return jsonify({"success": False, "message": "Not authenticated"})

    user_id = session["user_ID"]
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    if not start_date or not end_date:
        return jsonify({"success": False, "message": "start_date and end_date are required"})

    try:
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"success": False, "message": "Invalid date format. Use YYYY-MM-DD"})

    db = get_db()
    cursor = db.cursor()

    try:
        query = """
            SELECT 
                m.meal_id,
                m.meal_date,
                m.meal_type,
                m.is_locked,
                m.is_completed,
                m.notes,
                m.session_id,
                rt.recipe_name,
                rt.prep_time,
                rt.cook_time,
                rt.difficulty,
                m.custom_recipe_name,
                mps.session_name
            FROM meals m
            LEFT JOIN recipe_templates rt ON m.recipe_template_id = rt.template_id
            LEFT JOIN meal_plan_sessions mps ON m.session_id = mps.session_id
            WHERE m.user_id = %s AND m.meal_date BETWEEN %s AND %s
            ORDER BY m.meal_date, FIELD(m.meal_type, 'breakfast', 'lunch', 'dinner', 'snack')
        """
        cursor.execute(query, (user_id, start_date, end_date))
        meals = cursor.fetchall()

        # Format for frontend
        formatted_meals = []
        for meal in meals:
            meal_name = meal['recipe_name'] or meal['custom_recipe_name'] or f"Custom {meal['meal_type']}"
            formatted_meals.append({
                "meal_id": meal['meal_id'],
                "date": meal['meal_date'].strftime("%Y-%m-%d"),
                "type": meal['meal_type'],
                "name": meal_name,
                "prep_time": meal['prep_time'],
                "cook_time": meal['cook_time'],
                "difficulty": meal['difficulty'],
                "is_locked": meal['is_locked'],
                "is_completed": meal['is_completed'],
                "notes": meal['notes'],
                "session_id": meal['session_id'],
                "session_name": meal['session_name']
            })

        return jsonify({"success": True, "meals": formatted_meals})

    except Exception as e:
        return jsonify({"success": False, "message": f"Failed to get meals: {str(e)}"})
    finally:
        cursor.close()


@meals_bp.route("/meals/<int:meal_id>", methods=["GET"])
def get_meal_details(meal_id):
    """Get detailed information for a specific meal"""
    if "user_ID" not in session:
        return jsonify({"success": False, "message": "Not authenticated"})

    user_id = session["user_ID"]
    db = get_db()
    cursor = db.cursor()

    try:
        # Get meal with recipe template details
        meal_query = """
            SELECT 
                m.*,
                rt.recipe_name,
                rt.description,
                rt.prep_time,
                rt.cook_time,
                rt.servings,
                rt.estimated_cost,
                rt.difficulty,
                rt.calories_per_serving,
                rt.instructions,
                rt.cuisine_type,
                rt.dietary_tags
            FROM meals m
            LEFT JOIN recipe_templates rt ON m.recipe_template_id = rt.template_id
            WHERE m.meal_id = %s AND m.user_id = %s
        """
        cursor.execute(meal_query, (meal_id, user_id))
        meal = cursor.fetchone()

        if not meal:
            return jsonify({"success": False, "message": "Meal not found"})

        # Get ingredients (template + custom)
        ingredients = []
        
        if meal['recipe_template_id']:
            # Get template ingredients
            template_ingredients_query = """
                SELECT ingredient_name, quantity, unit, notes, estimated_cost, FALSE as is_custom
                FROM template_ingredients 
                WHERE template_id = %s
            """
            cursor.execute(template_ingredients_query, (meal['recipe_template_id'],))
            ingredients.extend(cursor.fetchall())

        # Get custom ingredients for this meal
        custom_ingredients_query = """
            SELECT ingredient_name, quantity, unit, notes, 0 as estimated_cost, TRUE as is_custom
            FROM meal_custom_ingredients 
            WHERE meal_id = %s
        """
        cursor.execute(custom_ingredients_query, (meal_id,))
        ingredients.extend(cursor.fetchall())

        # Format response
        meal_details = {
            "meal_id": meal['meal_id'],
            "date": meal['meal_date'].strftime("%Y-%m-%d"),
            "type": meal['meal_type'],
            "name": meal['recipe_name'] or meal['custom_recipe_name'],
            "description": meal['description'],
            "instructions": meal['instructions'] or meal['custom_instructions'],
            "prep_time": meal['prep_time'],
            "cook_time": meal['cook_time'],
            "servings": meal['servings'],
            "estimated_cost": meal['estimated_cost'],
            "difficulty": meal['difficulty'],
            "calories_per_serving": meal['calories_per_serving'],
            "cuisine_type": meal['cuisine_type'],
            "dietary_tags": json.loads(meal['dietary_tags'] or '[]'),
            "is_locked": meal['is_locked'],
            "is_completed": meal['is_completed'],
            "notes": meal['notes'],
            "ingredients": ingredients,
            "session_id": meal['session_id']
        }

        return jsonify({"success": True, "meal": meal_details})

    except Exception as e:
        return jsonify({"success": False, "message": f"Failed to get meal details: {str(e)}"})
    finally:
        cursor.close()


@meals_bp.route("/meals/<int:meal_id>", methods=["PUT"])
def update_meal(meal_id):
    """Update a specific meal"""
    if "user_ID" not in session:
        return jsonify({"success": False, "message": "Not authenticated"})

    user_id = session["user_ID"]
    data = request.get_json()
    
    db = get_db()
    cursor = db.cursor()

    try:
        # Verify meal belongs to user
        verify_query = "SELECT meal_id FROM meals WHERE meal_id = %s AND user_id = %s"
        cursor.execute(verify_query, (meal_id, user_id))
        if not cursor.fetchone():
            return jsonify({"success": False, "message": "Meal not found or access denied"})

        # Update meal fields
        update_fields = []
        params = []
        
        if 'custom_recipe_name' in data:
            update_fields.append("custom_recipe_name = %s")
            params.append(data['custom_recipe_name'])
            
        if 'custom_instructions' in data:
            update_fields.append("custom_instructions = %s")
            params.append(data['custom_instructions'])
            
        if 'is_locked' in data:
            update_fields.append("is_locked = %s")
            params.append(data['is_locked'])
            
        if 'is_completed' in data:
            update_fields.append("is_completed = %s")
            params.append(data['is_completed'])
            
        if 'notes' in data:
            update_fields.append("notes = %s")
            params.append(data['notes'])

        if update_fields:
            update_fields.append("updated_at = NOW()")
            params.extend([meal_id, user_id])
            
            update_query = f"""
                UPDATE meals SET {', '.join(update_fields)}
                WHERE meal_id = %s AND user_id = %s
            """
            cursor.execute(update_query, params)

        # Handle custom ingredients if provided
        if 'custom_ingredients' in data:
            # Remove existing custom ingredients
            cursor.execute("DELETE FROM meal_custom_ingredients WHERE meal_id = %s", (meal_id,))
            
            # Add new custom ingredients
            for ingredient in data['custom_ingredients']:
                ingredient_query = """
                    INSERT INTO meal_custom_ingredients (
                        meal_id, ingredient_name, quantity, unit, notes
                    ) VALUES (%s, %s, %s, %s, %s)
                """
                cursor.execute(ingredient_query, (
                    meal_id,
                    ingredient.get('name', ''),
                    ingredient.get('quantity', 1),
                    ingredient.get('unit', ''),
                    ingredient.get('notes', '')
                ))

        db.commit()
        return jsonify({"success": True, "message": "Meal updated successfully"})

    except Exception as e:
        db.rollback()
        return jsonify({"success": False, "message": f"Failed to update meal: {str(e)}"})
    finally:
        cursor.close()


@meals_bp.route("/meals/<int:meal_id>", methods=["DELETE"])
def delete_meal(meal_id):
    """Delete a specific meal"""
    if "user_ID" not in session:
        return jsonify({"success": False, "message": "Not authenticated"})

    user_id = session["user_ID"]
    db = get_db()
    cursor = db.cursor()

    try:
        # Verify meal belongs to user
        verify_query = "SELECT meal_id FROM meals WHERE meal_id = %s AND user_id = %s"
        cursor.execute(verify_query, (meal_id, user_id))
        if not cursor.fetchone():
            return jsonify({"success": False, "message": "Meal not found or access denied"})

        # Delete meal (cascades will handle custom ingredients)
        cursor.execute("DELETE FROM meals WHERE meal_id = %s AND user_id = %s", (meal_id, user_id))
        
        db.commit()
        return jsonify({"success": True, "message": "Meal deleted successfully"})

    except Exception as e:
        db.rollback()
        return jsonify({"success": False, "message": f"Failed to delete meal: {str(e)}"})
    finally:
        cursor.close()


# Import AI generation function from the old file
def generate_meal_plan_with_ai(days, start_date, ingredients, dietary_preference, budget, cooking_time, blocked_slots=None):
    """Use Gemini AI to generate a structured meal plan"""
    import os
    import google.generativeai as genai

    try:
        # Configure Gemini
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("WARNING: GEMINI_API_KEY not found")
            return None

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash-latest")

        # Format ingredients list
        ingredients_text = ", ".join(ingredients) if ingredients else "No specific ingredients provided"
        
        # Format blocked slots
        blocked_info = ""
        if blocked_slots:
            blocked_list = [f"{date.strftime('%Y-%m-%d')} {meal_type}" for date, meal_type in blocked_slots]
            blocked_info = f"\nSKIP these locked meal slots: {', '.join(blocked_list)}"

        # Create detailed prompt for meal planning
        prompt = f"""You are a professional meal prep consultant. Create a detailed {days}-day meal plan starting from {start_date.strftime('%B %d, %Y')} with the following requirements:

REQUIREMENTS:
- Days: {days}
- Available ingredients: {ingredients_text}
- Dietary preference: {dietary_preference}
- Budget limit: ${budget if budget else 'No limit'}
- Max cooking time per day: {cooking_time} minutes
- Include breakfast, lunch, and dinner for each day
- Focus on meal prep efficiency and batch cooking
- Prioritize using available ingredients first{blocked_info}

IMPORTANT: Respond with a valid JSON object in exactly this format:
Do not use fractions like 1/2 — convert them to decimals (e.g., 0.5) to ensure valid JSON

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
  ]
}}

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
            print(f"DEBUG: Successfully parsed meal plan with {len(meal_plan.get('days', []))} days")
            return meal_plan
        except json.JSONDecodeError as e:
            print(f"DEBUG: JSON parse error: {str(e)}")
            print("FULL RAW RESPONSE:\n", response.text)
            return None

    except Exception as e:
        print(f"ERROR: Meal plan generation failed: {str(e)}")
        return None


def generate_session_shopping_list(cursor, session_id, recipe_template_map):
    """Generate shopping list for a meal plan session"""
    try:
        # Get all meals in this session
        meals_query = """
            SELECT m.meal_id, rt.template_id
            FROM meals m
            JOIN recipe_templates rt ON m.recipe_template_id = rt.template_id
            WHERE m.session_id = %s
        """
        cursor.execute(meals_query, (session_id,))
        session_meals = cursor.fetchall()

        if not session_meals:
            return

        # Get ingredients for all templates used in this session
        template_ids = [meal['template_id'] for meal in session_meals]
        placeholders = ','.join(['%s'] * len(template_ids))
        
        ingredients_query = f"""
            SELECT ti.template_id, ti.ingredient_name, ti.quantity, ti.unit, ti.estimated_cost
            FROM template_ingredients ti
            WHERE ti.template_id IN ({placeholders})
        """
        cursor.execute(ingredients_query, template_ids)
        ingredients = cursor.fetchall()

        # Consolidate ingredients by name
        consolidated = {}
        meal_usage = {}
        
        for ingredient in ingredients:
            name = ingredient["ingredient_name"].lower()
            if name not in consolidated:
                consolidated[name] = {
                    "name": ingredient["ingredient_name"],
                    "total_quantity": 0,
                    "unit": ingredient["unit"],
                    "total_cost": 0,
                    "meals_using": []
                }

            consolidated[name]["total_quantity"] += ingredient["quantity"]
            consolidated[name]["total_cost"] += ingredient["estimated_cost"] or 0
            
            # Track which meals use this ingredient
            for meal in session_meals:
                if meal['template_id'] == ingredient['template_id']:
                    consolidated[name]["meals_using"].append(meal['meal_id'])

        # Insert consolidated shopping list items
        for item_data in consolidated.values():
            category = categorize_ingredient(item_data["name"])
            
            shopping_query = """
                INSERT INTO session_shopping_lists (
                    session_id, ingredient_name, total_quantity, unit,
                    estimated_cost, category, meals_using
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(shopping_query, (
                session_id,
                item_data["name"],
                item_data["total_quantity"],
                item_data["unit"],
                item_data["total_cost"],
                category,
                json.dumps(item_data["meals_using"])
            ))

    except Exception as e:
        print(f"ERROR: Failed to generate shopping list: {str(e)}")


def generate_session_batch_prep(cursor, session_id, batch_prep_data):
    """Generate batch prep steps for a meal plan session"""
    try:
        for step_data in batch_prep_data:
            step_query = """
                INSERT INTO session_batch_prep (
                    session_id, prep_session_name, step_order, description,
                    estimated_time, equipment_needed, tips
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(step_query, (
                session_id,
                step_data.get("session_name", "Prep Session"),
                step_data.get("order", 1),
                step_data.get("description", ""),
                step_data.get("time", 30),
                step_data.get("equipment", ""),
                step_data.get("tips", "")
            ))
    except Exception as e:
        print(f"ERROR: Failed to generate batch prep: {str(e)}")


def categorize_ingredient(ingredient_name):
    """Simple ingredient categorization"""
    name = ingredient_name.lower()

    if any(word in name for word in ["apple", "banana", "orange", "lettuce", "tomato", "potato", "carrot", "onion"]):
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