"""
Compatibility layer for existing meal plan endpoints
This module provides backward compatibility for the old meal plan structure
while using the new individual meals database structure underneath.
"""

from flask import Blueprint, request, jsonify, session
from src.database import get_db
from datetime import datetime, timedelta
import json

meal_plan_compat_bp = Blueprint("meal_plan_compat", __name__, url_prefix="/api")


@meal_plan_compat_bp.route("/meal-plans", methods=["GET"])
def get_meal_plans():
    """Get all meal plan sessions for the current user (backward compatibility)"""
    if "user_ID" not in session:
        return jsonify({"success": False, "message": "Not authenticated"})

    user_id = session["user_ID"]
    db = get_db()
    cursor = db.cursor()
    
    try:
        # Get meal plan sessions (replaces old meal_plans table)
        query = """
            SELECT session_id as plan_id, session_name as plan_name, 
                   start_date, end_date, total_days,
                   dietary_preference, budget_limit, max_cooking_time,
                   generated_at, status
            FROM meal_plan_sessions 
            WHERE user_id = %s
            ORDER BY generated_at DESC
        """
        cursor.execute(query, (user_id,))
        plans = cursor.fetchall()

        return jsonify({"success": True, "plans": plans})

    except Exception as e:
        return jsonify({"success": False, "message": f"Failed to get meal plans: {str(e)}"})
    finally:
        cursor.close()


@meal_plan_compat_bp.route("/meal-plans/<int:plan_id>", methods=["GET"])
def get_meal_plan_details(plan_id):
    """Get detailed meal plan with recipes and batch prep steps (backward compatibility)"""
    if "user_ID" not in session:
        return jsonify({"success": False, "message": "Not authenticated"})

    user_id = session["user_ID"]
    db = get_db()
    cursor = db.cursor()

    try:
        # Verify session belongs to user (plan_id is actually session_id in new structure)
        verify_query = "SELECT * FROM meal_plan_sessions WHERE session_id = %s AND user_id = %s"
        cursor.execute(verify_query, (plan_id, user_id))
        session_info = cursor.fetchone()

        if not session_info:
            return jsonify({"success": False, "message": "Meal plan not found"})

        # Get meals for this session and convert to old recipe format
        meals_query = """
            SELECT 
                m.meal_id,
                m.meal_date,
                m.meal_type,
                m.notes,
                rt.recipe_name,
                rt.description,
                rt.prep_time,
                rt.cook_time,
                rt.servings,
                rt.estimated_cost,
                rt.difficulty,
                rt.calories_per_serving,
                rt.instructions,
                m.custom_recipe_name,
                m.custom_instructions
            FROM meals m
            LEFT JOIN recipe_templates rt ON m.recipe_template_id = rt.template_id
            WHERE m.session_id = %s
            ORDER BY m.meal_date, FIELD(m.meal_type, 'breakfast', 'lunch', 'dinner', 'snack')
        """
        cursor.execute(meals_query, (plan_id,))
        meal_data = cursor.fetchall()

        # Get ingredients for each meal
        recipes_with_ingredients = []
        for meal in meal_data:
            # Calculate day number relative to session start
            start_date = session_info['start_date']
            meal_date = meal['meal_date']
            day_number = (meal_date - start_date).days + 1

            # Get ingredients (template + custom)
            ingredients = []
            
            if meal['recipe_name']:  # Has template
                template_query = """
                    SELECT rt.template_id FROM recipe_templates rt 
                    WHERE rt.recipe_name = %s
                """
                cursor.execute(template_query, (meal['recipe_name'],))
                template = cursor.fetchone()
                
                if template:
                    ingredients_query = """
                        SELECT ingredient_name, quantity, unit, notes as ingredient_notes
                        FROM template_ingredients 
                        WHERE template_id = %s
                    """
                    cursor.execute(ingredients_query, (template['template_id'],))
                    ingredients.extend(cursor.fetchall())

            # Get custom ingredients
            custom_ingredients_query = """
                SELECT ingredient_name, quantity, unit, notes as ingredient_notes
                FROM meal_custom_ingredients 
                WHERE meal_id = %s
            """
            cursor.execute(custom_ingredients_query, (meal['meal_id'],))
            ingredients.extend(cursor.fetchall())

            # Format as old recipe structure
            recipe_entry = {
                "recipe_id": meal['meal_id'],  # Use meal_id as recipe_id for compatibility
                "meal_type": meal['meal_type'],
                "day_number": day_number,
                "recipe_name": meal['recipe_name'] or meal['custom_recipe_name'] or f"Custom {meal['meal_type']}",
                "description": meal['description'] or "",
                "prep_time": meal['prep_time'] or 0,
                "cook_time": meal['cook_time'] or 0,
                "servings": meal['servings'] or 1,
                "estimated_cost": meal['estimated_cost'] or 0,
                "difficulty": meal['difficulty'] or "medium",
                "calories_per_serving": meal['calories_per_serving'] or 0,
                "instructions": meal['instructions'] or meal['custom_instructions'] or "",
                "notes": meal['notes'] or "",
                "ingredient_name": None,
                "quantity": None,
                "unit": None,
                "ingredient_notes": None
            }

            # Add one entry per ingredient (for compatibility with old structure)
            if ingredients:
                for ingredient in ingredients:
                    recipe_copy = recipe_entry.copy()
                    recipe_copy.update({
                        "ingredient_name": ingredient['ingredient_name'],
                        "quantity": ingredient['quantity'],
                        "unit": ingredient['unit'],
                        "ingredient_notes": ingredient['ingredient_notes']
                    })
                    recipes_with_ingredients.append(recipe_copy)
            else:
                recipes_with_ingredients.append(recipe_entry)

        # Get batch prep steps
        steps_query = """
            SELECT * FROM session_batch_prep 
            WHERE session_id = %s
            ORDER BY prep_session_name, step_order
        """
        cursor.execute(steps_query, (plan_id,))
        prep_steps = cursor.fetchall()

        # Get shopping list
        shopping_query = """
            SELECT * FROM session_shopping_lists 
            WHERE session_id = %s
            ORDER BY category, ingredient_name
        """
        cursor.execute(shopping_query, (plan_id,))
        shopping_items = cursor.fetchall()

        # Structure the response in old format
        structured_plan = {
            "plan_info": {
                "plan_id": session_info['session_id'],
                "plan_name": session_info['session_name'],
                "start_date": session_info['start_date'],
                "end_date": session_info['end_date'],
                "total_days": session_info['total_days'],
                "dietary_preference": session_info['dietary_preference'],
                "budget_limit": session_info['budget_limit'],
                "max_cooking_time": session_info['max_cooking_time'],
                "generated_at": session_info['generated_at'],
                "status": session_info['status'],
                "ai_model_used": session_info['ai_model_used'],
                "generation_prompt": session_info['generation_prompt']
            },
            "recipes": organize_recipes_by_day(recipes_with_ingredients),
            "batch_prep": prep_steps,
            "shopping_list": shopping_items,
        }

        return jsonify({"success": True, "meal_plan": structured_plan})

    except Exception as e:
        return jsonify({"success": False, "message": f"Failed to get meal plan: {str(e)}"})
    finally:
        cursor.close()


def organize_recipes_by_day(recipe_data):
    """Organize recipe data by day and meal type (backward compatibility)"""
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