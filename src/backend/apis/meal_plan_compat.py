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
        # Get meal plan sessions with fuzzy matching summary (replaces old meal_plans table)
        query = """
            SELECT mps.session_id as plan_id, mps.session_name as plan_name, 
                   mps.start_date, mps.end_date, mps.total_days,
                   mps.dietary_preference, mps.budget_limit, mps.max_cooking_time,
                   mps.generated_at, mps.status,
                   sgs.generation_id, sgs.auto_matched_count, sgs.confirm_needed_count, 
                   sgs.missing_count, sgs.total_ingredients
            FROM meal_plan_sessions mps
            LEFT JOIN shopping_generation_sessions sgs ON mps.session_id = sgs.meal_plan_session_id
                AND sgs.generation_id = (
                    SELECT MAX(generation_id) FROM shopping_generation_sessions 
                    WHERE meal_plan_session_id = mps.session_id
                )
            WHERE mps.user_id = %s
            ORDER BY ABS(DATEDIFF(mps.start_date, CURDATE())), mps.start_date ASC
        """
        cursor.execute(query, (user_id,))
        plans = cursor.fetchall()

        # Format dates as strings and add fuzzy matching summary
        formatted_plans = []
        for plan in plans:
            plan_copy = dict(plan)
            plan_copy['start_date'] = plan['start_date'].strftime("%Y-%m-%d") if hasattr(plan['start_date'], 'strftime') else plan['start_date']
            plan_copy['end_date'] = plan['end_date'].strftime("%Y-%m-%d") if hasattr(plan['end_date'], 'strftime') else plan['end_date']
            
            # Add fuzzy matching summary if available
            if plan.get('generation_id'):
                plan_copy['fuzzy_matching_summary'] = {
                    "auto_matched": plan['auto_matched_count'] or 0,
                    "confirm_needed": plan['confirm_needed_count'] or 0,
                    "missing": plan['missing_count'] or 0,
                    "total_ingredients": plan['total_ingredients'] or 0,
                    "pantry_utilization_rate": (plan['auto_matched_count'] / plan['total_ingredients'] * 100) if (plan['total_ingredients'] and plan['total_ingredients'] > 0) else 0
                }
            else:
                plan_copy['fuzzy_matching_summary'] = None
                
            # Remove the generation fields from the main plan object
            fields_to_remove = ['generation_id', 'auto_matched_count', 'confirm_needed_count', 'missing_count', 'total_ingredients']
            for field in fields_to_remove:
                plan_copy.pop(field, None)
                
            formatted_plans.append(plan_copy)

        return jsonify({"success": True, "plans": formatted_plans})

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

        # Get shopping list with fuzzy matching data
        shopping_query = """
            SELECT * FROM session_shopping_lists 
            WHERE session_id = %s
            ORDER BY category, ingredient_name
        """
        cursor.execute(shopping_query, (plan_id,))
        shopping_items = cursor.fetchall()
        
        # Get fuzzy matching results if they exist
        fuzzy_matching_data = {}
        generation_summary = None
        
        try:
            # Get the latest generation session for this meal plan
            generation_query = """
                SELECT generation_id, auto_matched_count, confirm_needed_count, 
                       missing_count, total_ingredients, generated_at
                FROM shopping_generation_sessions 
                WHERE meal_plan_session_id = %s 
                ORDER BY generated_at DESC 
                LIMIT 1
            """
            cursor.execute(generation_query, (plan_id,))
            generation_session = cursor.fetchone()
            
            if generation_session:
                generation_summary = {
                    "generation_id": generation_session["generation_id"],
                    "auto_matched": generation_session["auto_matched_count"],
                    "confirm_needed": generation_session["confirm_needed_count"],
                    "missing": generation_session["missing_count"],
                    "total_ingredients": generation_session["total_ingredients"],
                    "generated_at": generation_session["generated_at"].isoformat() if generation_session["generated_at"] else None,
                    "pantry_utilization_rate": (generation_session["auto_matched_count"] / generation_session["total_ingredients"] * 100) if generation_session["total_ingredients"] > 0 else 0
                }
                
                # Get detailed matching results
                matches_query = """
                    SELECT gim.*, pi.item_name as pantry_item_name, pi.storage_type, pi.expiration_date
                    FROM generation_ingredient_matches gim
                    LEFT JOIN pantry_items pi ON gim.pantry_item_id = pi.pantry_item_id
                    WHERE gim.generation_id = %s
                    ORDER BY gim.ingredient_name
                """
                cursor.execute(matches_query, (generation_session["generation_id"],))
                matching_results = cursor.fetchall()
                
                # Organize matching data by ingredient name
                for match in matching_results:
                    fuzzy_matching_data[match["ingredient_name"]] = {
                        "match_type": match["match_type"],
                        "confidence": float(match["match_confidence"]) if match["match_confidence"] else None,
                        "pantry_item": {
                            "id": match["pantry_item_id"],
                            "name": match.get("pantry_item_name"),
                            "available_quantity": float(match["pantry_available_quantity"]) if match["pantry_available_quantity"] else None,
                            "storage_type": match.get("storage_type"),
                            "expiration_date": match.get("expiration_date").strftime("%Y-%m-%d") if match.get("expiration_date") else None
                        } if match["pantry_item_id"] else None,
                        "needs_to_buy": float(match["needs_to_buy_quantity"]),
                        "is_user_confirmed": bool(match["is_user_confirmed"])
                    }
                    
        except Exception as e:
            print(f"DEBUG: Failed to get fuzzy matching data: {str(e)}")
            # Continue without fuzzy matching data

        # Structure the response in old format (use raw dates from database)
        structured_plan = {
            "plan_info": {
                "plan_id": session_info['session_id'],
                "plan_name": session_info['session_name'],
                "start_date": session_info['start_date'].strftime("%Y-%m-%d") if hasattr(session_info['start_date'], 'strftime') else session_info['start_date'],
                "end_date": session_info['end_date'].strftime("%Y-%m-%d") if hasattr(session_info['end_date'], 'strftime') else session_info['end_date'],
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
            "fuzzy_matching": {
                "summary": generation_summary,
                "ingredient_matches": fuzzy_matching_data
            } if generation_summary else None
        }

        return jsonify({"success": True, "meal_plan": structured_plan})

    except Exception as e:
        return jsonify({"success": False, "message": f"Failed to get meal plan: {str(e)}"})
    finally:
        cursor.close()


@meal_plan_compat_bp.route("/meal-plans/<int:plan_id>", methods=["DELETE"])
def delete_meal_plan(plan_id):
    """Delete a meal plan and all associated data"""
    if "user_ID" not in session:
        return jsonify({"success": False, "message": "Not authenticated"})

    user_id = session["user_ID"]
    db = get_db()
    cursor = db.cursor()
    
    try:
        # First verify the meal plan belongs to the current user
        cursor.execute("""
            SELECT session_id FROM meal_plan_sessions 
            WHERE session_id = %s AND user_id = %s
        """, (plan_id, user_id))
        
        if not cursor.fetchone():
            return jsonify({"success": False, "message": "Meal plan not found or access denied"})
        
        # Delete in order to respect foreign key constraints
        # 1. Delete custom ingredients for meals in this session
        cursor.execute("""
            DELETE rt FROM recipe_templates rt
            INNER JOIN meals m ON rt.template_id = m.recipe_template_id
            WHERE m.session_id = %s
        """, (plan_id,))
        
        # 2. Delete meals in this session
        cursor.execute("""
            DELETE FROM meals WHERE session_id = %s
        """, (plan_id,))
        
        # 3. Delete meal plan session
        cursor.execute("""
            DELETE FROM meal_plan_sessions WHERE session_id = %s
        """, (plan_id,))
        
        db.commit()
        
        return jsonify({
            "success": True, 
            "message": "Meal plan deleted successfully"
        })

    except Exception as e:
        db.rollback()
        return jsonify({
            "success": False, 
            "message": f"Failed to delete meal plan: {str(e)}"
        })
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