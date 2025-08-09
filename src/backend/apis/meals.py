from flask import Blueprint, request, jsonify, session
from src.database import get_db
from src.timezone_utils import get_user_current_date
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
    minimal_cooking_sessions = data.get("minimal_cooking_sessions", False)

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

        # Check for existing meals in date range
        existing_meals_query = """
            SELECT meal_date, meal_type, is_locked 
            FROM meals 
            WHERE user_id = %s AND meal_date BETWEEN %s AND %s
        """
        cursor.execute(existing_meals_query, (user_id, start_date, end_date))
        existing_meals = cursor.fetchall()
        
        # Check if there are any existing meals in the date range
        if existing_meals:
            existing_dates = set()
            locked_meals = []
            unlocked_meals = []
            
            for meal in existing_meals:
                meal_date_str = meal['meal_date'].strftime('%Y-%m-%d')
                existing_dates.add(meal_date_str)
                
                if meal['is_locked']:
                    locked_meals.append(f"{meal_date_str} ({meal['meal_type']})")
                else:
                    unlocked_meals.append(f"{meal_date_str} ({meal['meal_type']})")
            
            # Create detailed error message
            error_parts = []
            if locked_meals:
                error_parts.append(f"Locked meals: {', '.join(locked_meals)}")
            if unlocked_meals:
                error_parts.append(f"Existing meals: {', '.join(unlocked_meals)}")
            
            error_message = f"Cannot generate meal plan. The selected date range conflicts with existing meals. {' | '.join(error_parts)}. Please choose a different date range or delete conflicting meals first."
            
            return jsonify({
                "success": False, 
                "message": error_message,
                "conflicting_dates": list(existing_dates),
                "locked_meals": locked_meals,
                "unlocked_meals": unlocked_meals
            })
        
        # No existing meals, safe to proceed
        blocked_slots = set()

        # Generate meal plan using AI
        meal_plan_data = generate_meal_plan_with_ai(
            days=days,
            start_date=start_date,
            ingredients=ingredients,
            dietary_preference=dietary_preference,
            budget=budget,
            cooking_time=cooking_time,
            blocked_slots=blocked_slots,
            minimal_cooking_sessions=minimal_cooking_sessions
        )

        if not meal_plan_data:
            return jsonify({"success": False, "message": "Failed to generate meal plan. Please try again."})

        # Create meal plan session
        session_name = f"Meal Plan - {start_date.strftime('%b %d')}"
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
            day_value = day_data.get("day", 1)
            print(f"DEBUG: day_value = {day_value}, type = {type(day_value)}")
            
            # Handle different possible formats for the day field
            if isinstance(day_value, str):
                # Check if it's a date string
                if '-' in str(day_value):
                    # It's a date string, extract day number from index
                    day_number = meal_plan_data.get("days", []).index(day_data) + 1
                    print(f"DEBUG: Using index-based day number: {day_number}")
                else:
                    # It's a string number
                    day_number = int(day_value)
            else:
                # It's already a number
                day_number = int(day_value)
            
            meal_date = start_date + timedelta(days=day_number - 1)
            print(f"DEBUG: Final meal_date = {meal_date}")
            
            for meal_type in ["breakfast", "lunch", "dinner"]:
                if meal_type in day_data:
                    recipe_data = day_data[meal_type]
                    recipe_name = recipe_data.get("name", "")

                    # Get or create recipe template
                    print(f"DEBUG: Creating template for {recipe_name} ({meal_type})")
                    template_id = get_or_create_recipe_template(cursor, recipe_data, meal_type)
                    print(f"DEBUG: Created template_id = {template_id}")
                    recipe_template_map[template_id] = recipe_data

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
        generate_session_shopping_list_with_fuzzy_matching(cursor, session_id, user_id, recipe_template_map)
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
    
    # Handle instructions - convert array to string if needed
    instructions_raw = recipe_data.get("instructions", "")
    if isinstance(instructions_raw, list):
        # Convert array of instructions to numbered string
        instructions = "\n".join([f"{i+1}. {step}" for i, step in enumerate(instructions_raw)])
        print(f"DEBUG: Converted instructions array to string: {len(instructions_raw)} steps")
    else:
        instructions = instructions_raw
    
    print(f"DEBUG: Final instructions type: {type(instructions)}")
    
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
    ingredients_list = recipe_data.get("ingredients", [])
    print(f"DEBUG: Adding {len(ingredients_list)} ingredients for template {template_id}")
    
    for i, ingredient in enumerate(ingredients_list):
        print(f"DEBUG: Ingredient {i}: {ingredient}")
        ingredient_query = """
            INSERT INTO template_ingredients (
                template_id, ingredient_name, quantity, unit, notes, estimated_cost
            ) VALUES (%s, %s, %s, %s, %s, %s)
        """
        ingredient_values = (
            template_id,
            ingredient.get("name", ""),
            ingredient.get("quantity", 1),
            ingredient.get("unit", ""),
            ingredient.get("notes", ""),
            ingredient.get("cost", 0)
        )
        print(f"DEBUG: Ingredient values: {ingredient_values}")
        cursor.execute(ingredient_query, ingredient_values)
    
    return template_id


@meals_bp.route("/meals", methods=["GET"])
def get_meals():
    """Get meals for date range (for calendar view) - timezone-aware"""
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

        # Format for frontend with timezone awareness for "today" detection
        formatted_meals = []
        user_today = get_user_current_date(user_id)
        
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
                "session_name": meal['session_name'],
                "is_today": meal['meal_date'] == user_today,
                "is_future": meal['meal_date'] > user_today
            })

        return jsonify({"success": True, "meals": formatted_meals, "user_today": user_today.strftime("%Y-%m-%d")})

    except Exception as e:
        return jsonify({"success": False, "message": f"Failed to get meals: {str(e)}"})
    finally:
        cursor.close()


@meals_bp.route("/meals/today", methods=["GET"])
def get_todays_meals():
    """Get today's meals based on user's timezone"""
    if "user_ID" not in session:
        return jsonify({"success": False, "message": "Not authenticated"})

    user_id = session["user_ID"]
    
    try:
        # Get user's current date in their timezone
        user_today = get_user_current_date(user_id)
        
        db = get_db()
        cursor = db.cursor()

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
                rt.instructions,
                rt.estimated_cost,
                m.custom_recipe_name,
                m.custom_instructions,
                mps.session_name
            FROM meals m
            LEFT JOIN recipe_templates rt ON m.recipe_template_id = rt.template_id
            LEFT JOIN meal_plan_sessions mps ON m.session_id = mps.session_id
            WHERE m.user_id = %s AND m.meal_date = %s
            ORDER BY FIELD(m.meal_type, 'breakfast', 'lunch', 'dinner', 'snack')
        """
        cursor.execute(query, (user_id, user_today))
        meals = cursor.fetchall()
        
        # Format for frontend
        formatted_meals = []
        for meal in meals:
            meal_name = meal['recipe_name'] or meal['custom_recipe_name'] or f"Custom {meal['meal_type']}"
            instructions = meal['instructions'] or meal['custom_instructions'] or "No instructions available"
            
            formatted_meals.append({
                "meal_id": meal['meal_id'],
                "date": meal['meal_date'].strftime("%Y-%m-%d"),
                "type": meal['meal_type'],
                "name": meal_name,
                "instructions": instructions,
                "prep_time": meal['prep_time'],
                "cook_time": meal['cook_time'],
                "difficulty": meal['difficulty'],
                "estimated_cost": float(meal['estimated_cost']) if meal['estimated_cost'] else None,
                "is_locked": meal['is_locked'],
                "is_completed": meal['is_completed'],
                "notes": meal['notes'],
                "session_id": meal['session_id'],
                "session_name": meal['session_name']
            })

        return jsonify({
            "success": True, 
            "meals": formatted_meals,
            "date": user_today.strftime("%Y-%m-%d"),
            "total_meals": len(formatted_meals),
            "completed_meals": len([m for m in formatted_meals if m['is_completed']])
        })

    except Exception as e:
        return jsonify({"success": False, "message": f"Failed to get today's meals: {str(e)}"})
    finally:
        if 'cursor' in locals():
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
        # Verify meal belongs to user and get meal date
        verify_query = "SELECT meal_id, meal_date FROM meals WHERE meal_id = %s AND user_id = %s"
        cursor.execute(verify_query, (meal_id, user_id))
        meal_info = cursor.fetchone()
        if not meal_info:
            return jsonify({"success": False, "message": "Meal not found or access denied"})
        
        # Check if trying to complete a future meal (timezone-aware)
        if 'is_completed' in data and data['is_completed']:
            meal_date = meal_info['meal_date']
            user_today = get_user_current_date(user_id)
            if meal_date > user_today:
                return jsonify({
                    "success": False, 
                    "message": "Cannot mark future meals as completed. You can only complete meals for today or past dates."
                })

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
def generate_meal_plan_with_ai(days, start_date, ingredients, dietary_preference, budget, cooking_time, blocked_slots=None, minimal_cooking_sessions=False):
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

        # Format the minimal cooking sessions mode setting
        minimal_sessions_text = "true" if minimal_cooking_sessions else "false"
        budget_text = f"${budget}" if budget else "No limit"
        start_date_text = start_date.strftime('%B %d, %Y')
        
        # Create detailed prompt for meal planning
        prompt = f'''You are a professional meal prep consultant and nutrition planner. Create a detailed {days}-day meal plan starting from {start_date_text} with the following requirements:

IMPORTANT: Use numeric day numbers (1, 2, 3, etc.) NOT dates in the "day" field.

REQUIREMENTS:
- Days: {days}
- Available ingredients: {ingredients_text}
- Dietary preference: {dietary_preference}
- Budget limit: {budget_text}
- Max cooking time per day: {cooking_time} minutes
- Minimal cooking sessions mode: {minimal_sessions_text} (true or false)
- Include breakfast, lunch, and dinner for each day
- Focus on meal prep efficiency and batch cooking
- Prioritize using available ingredients first{blocked_info}

If "minimal_cooking_sessions" is true:
- Minimize recipe variety by reusing the same meals for multiple days
- Show repeated meals using the "reused_from_day" field
- Plan larger batch prep sessions covering multiple days
- Add a "storage_plan" section listing fridge/freezer life for each recipe
- Emphasize cost savings and fewer total ingredients

If "minimal_cooking_sessions" is false:
- Provide unique recipes for each meal with more variety in flavors and ingredients
- Focus on balanced variety while still using pantry items first

For all plans:
- Make cooking "instructions" a step-by-step array with clear numbered steps, each including timing and equipment
- Include "make_ahead_tips", "storage", and "reheat_instructions" for every recipe
- Provide "macros" (protein, carbs, fat in grams) along with "calories"
- Include "alternate_ingredients" for substitutions
- Maintain flavor and ingredient balance across the plan

Do not use fractions like 1/2 - convert them to decimals (e.g., 0.5) to ensure valid JSON
Do not wrap any times like (10 min) in the instructions. Just add times in the instructions themselves such as Roast broccoli for 20 minutes

CRITICAL: In the JSON response, the "day" field must be a NUMBER (1, 2, 3, etc.), never a date string.

Respond with a valid JSON object in exactly this format:

{{
  "minimal_cooking_sessions": true,
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
        "macros": {{"protein": 20, "carbs": 30, "fat": 10}},
        "instructions": [
          "Step 1: ...",
          "Step 2: ..."
        ],
        "ingredients": [
          {{"name": "eggs", "quantity": 2, "unit": "pcs", "notes": "", "cost": 1.00}}
        ],
        "make_ahead_tips": "Chop vegetables the night before",
        "storage": "Store in airtight container for up to 3 days in fridge",
        "reheat_instructions": "Microwave for 60 seconds or reheat in skillet on low heat for 5 minutes",
        "notes": "Can be prepped night before"
      }},
      "lunch": {{"...": "..."}},
      "dinner": {{"...": "..."}}
    }},
    {{
      "day": 2,
      "breakfast": {{"reused_from_day": 1}},
      "lunch": {{"reused_from_day": 1}},
      "dinner": {{"reused_from_day": 1}}
    }}
  ],
  "batch_prep": [
    {{
      "session_name": "Main Cooking Session",
      "order": 1,
      "description": "Prepare all breakfasts, lunches, and dinners for Days 1-4 in one batch",
      "time": 180,
      "recipes": "All meals for Days 1-4",
      "equipment": "Large pot, oven, storage containers",
      "tips": "Cool completely before refrigerating or freezing"
    }}
  ],
  "storage_plan": [
    {{
      "recipe": "Overnight Oats with Berries",
      "fridge_life_days": 4,
      "freezer_life_days": 0,
      "notes": "Best eaten fresh"
    }}
  ]
}}

Generate the complete meal plan now. Remember to convert fractions into decimal'''

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
            print("FULL RAW RESPONSE:\n", response.text)
            print(f"DEBUG: Successfully parsed meal plan with {len(meal_plan.get('days', []))} days")
            return meal_plan
        except json.JSONDecodeError as e:
            print(f"DEBUG: JSON parse error: {str(e)}")
            print("FULL RAW RESPONSE:\n", response.text)
            return None

    except Exception as e:
        print(f"ERROR: Meal plan generation failed: {str(e)}")
        return None


def generate_session_shopping_list_with_fuzzy_matching(cursor, session_id, user_id, recipe_template_map):
    """Generate shopping list for a meal plan session with fuzzy matching integration"""
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
        print(f"DEBUG: template_ids = {template_ids}")
        
        if not template_ids:
            print("DEBUG: No template IDs found, skipping ingredient generation")
            return
        
        placeholders = ','.join(['%s'] * len(template_ids))
        
        ingredients_query = f"""
            SELECT ti.template_id, ti.ingredient_name, ti.quantity, ti.unit, ti.estimated_cost
            FROM template_ingredients ti
            WHERE ti.template_id IN ({placeholders})
        """
        print(f"DEBUG: ingredients_query = {ingredients_query}")
        print(f"DEBUG: template_ids for query = {template_ids}")
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

            consolidated[name]["total_quantity"] += float(ingredient["quantity"] or 0)
            consolidated[name]["total_cost"] += float(ingredient["estimated_cost"] or 0)
            
            # Track which meals use this ingredient
            for meal in session_meals:
                if meal['template_id'] == ingredient['template_id']:
                    consolidated[name]["meals_using"].append(meal['meal_id'])

        # Use enhanced shopping generation with fuzzy matching
        from src.services.enhanced_shopping_generation import enhanced_shopping_generator
        
        # Prepare ingredients for fuzzy matching
        ingredients_for_matching = [
            {
                "ingredient_name": item_data["name"],
                "quantity": item_data["total_quantity"],
                "unit": item_data["unit"]
            }
            for item_data in consolidated.values()
        ]
        
        # Perform fuzzy matching and get enhanced results
        if ingredients_for_matching:
            from src.services.fuzzy_matching import fuzzy_matching_service
            matching_results = fuzzy_matching_service.batch_match_ingredients(user_id, ingredients_for_matching)
            
            # Create shopping generation session
            cursor.execute("""
                INSERT INTO shopping_generation_sessions 
                (user_id, meal_plan_session_id, generation_type, total_ingredients)
                VALUES (%s, %s, 'meal_plan', %s)
            """, [user_id, session_id, len(matching_results)])
            
            generation_id = cursor.lastrowid
            
            # Process matching results and create shopping list entries
            auto_matched = 0
            confirm_needed = 0
            missing = 0
            
            for i, result in enumerate(matching_results):
                original_data = list(consolidated.values())[i]
                
                # Skip items with zero or negative required quantities
                if result.required_quantity <= 0:
                    print(f"DEBUG: Skipping zero-quantity ingredient: {result.ingredient_name}")
                    continue
                
                # Store detailed matching result
                cursor.execute("""
                    INSERT INTO generation_ingredient_matches 
                    (generation_id, ingredient_name, required_quantity, required_unit, 
                     pantry_item_id, pantry_available_quantity, match_confidence, 
                     match_type, needs_to_buy_quantity, estimated_cost)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, [
                    generation_id,
                    result.ingredient_name,
                    result.required_quantity,
                    result.required_unit,
                    result.best_match.pantry_item_id if result.best_match else None,
                    result.best_match.available_quantity if result.best_match else None,
                    result.best_match.confidence_score if result.best_match else None,
                    result.match_type,
                    result.needs_to_buy,
                    original_data["total_cost"]
                ])
                
                # Count match types
                if result.match_type == "auto":
                    auto_matched += 1
                elif result.match_type == "confirm":
                    confirm_needed += 1
                else:
                    missing += 1
                
                # Insert into session shopping list (original table for compatibility)
                category = categorize_ingredient(result.ingredient_name)
                
                shopping_query = """
                    INSERT INTO session_shopping_lists (
                        session_id, ingredient_name, total_quantity, unit,
                        estimated_cost, category, meals_using
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(shopping_query, (
                    session_id,
                    result.ingredient_name,
                    result.required_quantity,  # Show total required quantity, not just what's needed
                    result.required_unit,
                    original_data["total_cost"],
                    category,
                    json.dumps(original_data["meals_using"])
                ))
            
            # Update generation session with summary
            cursor.execute("""
                UPDATE shopping_generation_sessions 
                SET auto_matched_count = %s, confirm_needed_count = %s, 
                    missing_count = %s, completed_at = NOW()
                WHERE generation_id = %s
            """, [auto_matched, confirm_needed, missing, generation_id])
            
            print(f"DEBUG: Enhanced shopping list generated - Auto: {auto_matched}, Confirm: {confirm_needed}, Missing: {missing}")
        
        else:
            # No ingredients found, create empty session for tracking
            cursor.execute("""
                INSERT INTO shopping_generation_sessions 
                (user_id, meal_plan_session_id, generation_type, total_ingredients, completed_at)
                VALUES (%s, %s, 'meal_plan', 0, NOW())
            """, [user_id, session_id])

    except Exception as e:
        print(f"ERROR: Failed to generate enhanced shopping list: {str(e)}")
        # Fallback to basic generation if fuzzy matching fails
        generate_session_shopping_list_basic(cursor, session_id, consolidated if 'consolidated' in locals() else {})


def generate_session_shopping_list_basic(cursor, session_id, consolidated):
    """Fallback basic shopping list generation without fuzzy matching"""
    try:
        # Insert consolidated shopping list items using basic method
        for item_data in consolidated.values():
            # Skip items with zero or negative quantities
            if item_data["total_quantity"] <= 0:
                print(f"DEBUG: Skipping zero-quantity item: {item_data['name']}")
                continue
                
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
            
        print(f"DEBUG: Basic shopping list generated with {len(consolidated)} items")
        
    except Exception as e:
        print(f"ERROR: Failed to generate basic shopping list: {str(e)}")


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