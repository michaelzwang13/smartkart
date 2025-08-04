from flask import Blueprint, request, jsonify, session
from src.database import get_db
from datetime import datetime

meal_goals_bp = Blueprint("meal_goals", __name__, url_prefix="/api")


@meal_goals_bp.route("/meal-goals", methods=["GET"])
def get_meal_goals():
    """Get meal goals for a specific month/year"""
    if "user_ID" not in session:
        return jsonify({"success": False, "message": "Not authenticated"})

    user_id = session["user_ID"]
    month = request.args.get("month", datetime.now().month)
    year = request.args.get("year", datetime.now().year)

    try:
        month = int(month)
        year = int(year)
        
        if not (1 <= month <= 12):
            return jsonify({"success": False, "message": "Invalid month"})
        if not (2020 <= year <= 2030):
            return jsonify({"success": False, "message": "Invalid year"})
            
    except (ValueError, TypeError):
        return jsonify({"success": False, "message": "Invalid month or year format"})

    db = get_db()
    cursor = db.cursor()

    try:
        query = """
            SELECT meal_plans_goal, meals_completed_goal, new_recipes_goal, 
                   created_at, updated_at
            FROM monthly_meal_goals 
            WHERE user_id = %s AND month = %s AND year = %s
        """
        cursor.execute(query, (user_id, month, year))
        goals = cursor.fetchone()

        if goals:
            return jsonify({
                "success": True,
                "goals": {
                    "meal_plans_goal": goals["meal_plans_goal"],
                    "meals_completed_goal": goals["meals_completed_goal"],
                    "new_recipes_goal": goals["new_recipes_goal"],
                    "month": month,
                    "year": year,
                    "created_at": goals["created_at"].isoformat() if goals["created_at"] else None,
                    "updated_at": goals["updated_at"].isoformat() if goals["updated_at"] else None
                }
            })
        else:
            # Return default goals if none exist
            return jsonify({
                "success": True,
                "goals": {
                    "meal_plans_goal": 4,
                    "meals_completed_goal": 60,
                    "new_recipes_goal": 12,
                    "month": month,
                    "year": year,
                    "created_at": None,
                    "updated_at": None
                }
            })

    except Exception as e:
        return jsonify({"success": False, "message": f"Failed to get meal goals: {str(e)}"})
    finally:
        cursor.close()


@meal_goals_bp.route("/meal-goals", methods=["POST", "PUT"])
def save_meal_goals():
    """Save or update meal goals for a specific month/year"""
    if "user_ID" not in session:
        return jsonify({"success": False, "message": "Not authenticated"})

    user_id = session["user_ID"]
    data = request.get_json()

    # Validate required fields
    required_fields = ["month", "year", "meal_plans_goal", "meals_completed_goal", "new_recipes_goal"]
    for field in required_fields:
        if field not in data:
            return jsonify({"success": False, "message": f"Missing required field: {field}"})

    try:
        month = int(data["month"])
        year = int(data["year"])
        meal_plans_goal = int(data["meal_plans_goal"])
        meals_completed_goal = int(data["meals_completed_goal"])
        new_recipes_goal = int(data["new_recipes_goal"])

        # Validate ranges
        if not (1 <= month <= 12):
            return jsonify({"success": False, "message": "Month must be between 1 and 12"})
        if not (2020 <= year <= 2030):
            return jsonify({"success": False, "message": "Year must be between 2020 and 2030"})
        if not (1 <= meal_plans_goal <= 20):
            return jsonify({"success": False, "message": "Meal plans goal must be between 1 and 20"})
        if not (10 <= meals_completed_goal <= 200):
            return jsonify({"success": False, "message": "Meals completed goal must be between 10 and 200"})
        if not (1 <= new_recipes_goal <= 50):
            return jsonify({"success": False, "message": "New recipes goal must be between 1 and 50"})

    except (ValueError, TypeError):
        return jsonify({"success": False, "message": "Invalid data types for goal values"})

    db = get_db()
    cursor = db.cursor()

    try:
        # Use INSERT ... ON DUPLICATE KEY UPDATE for upsert functionality
        upsert_query = """
            INSERT INTO monthly_meal_goals 
            (user_id, month, year, meal_plans_goal, meals_completed_goal, new_recipes_goal)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                meal_plans_goal = VALUES(meal_plans_goal),
                meals_completed_goal = VALUES(meals_completed_goal),
                new_recipes_goal = VALUES(new_recipes_goal),
                updated_at = CURRENT_TIMESTAMP
        """
        
        cursor.execute(upsert_query, (
            user_id, month, year, meal_plans_goal, 
            meals_completed_goal, new_recipes_goal
        ))
        
        db.commit()
        
        return jsonify({
            "success": True,
            "message": "Meal goals saved successfully",
            "goals": {
                "meal_plans_goal": meal_plans_goal,
                "meals_completed_goal": meals_completed_goal,
                "new_recipes_goal": new_recipes_goal,
                "month": month,
                "year": year
            }
        })

    except Exception as e:
        db.rollback()
        return jsonify({"success": False, "message": f"Failed to save meal goals: {str(e)}"})
    finally:
        cursor.close()


@meal_goals_bp.route("/meal-goals/progress", methods=["GET"])
def get_goals_progress():
    """Get current progress towards meal goals for a specific month"""
    if "user_ID" not in session:
        return jsonify({"success": False, "message": "Not authenticated"})

    user_id = session["user_ID"]
    month = request.args.get("month", datetime.now().month)
    year = request.args.get("year", datetime.now().year)

    try:
        month = int(month)
        year = int(year)
    except (ValueError, TypeError):
        return jsonify({"success": False, "message": "Invalid month or year format"})

    db = get_db()
    cursor = db.cursor()

    try:
        # Get the start and end dates for the month
        start_date = f"{year}-{month:02d}-01"
        if month == 12:
            end_date = f"{year + 1}-01-01"
        else:
            end_date = f"{year}-{month + 1:02d}-01"

        # Get meal plans created this month
        meal_plans_query = """
            SELECT COUNT(*) as plan_count
            FROM meal_plan_sessions
            WHERE user_id = %s 
            AND generated_at >= %s 
            AND generated_at < %s
        """
        cursor.execute(meal_plans_query, (user_id, start_date, end_date))
        meal_plans_result = cursor.fetchone()
        meal_plans_count = meal_plans_result["plan_count"] if meal_plans_result else 0

        # Get completed meals this month
        completed_meals_query = """
            SELECT COUNT(*) as completed_count
            FROM meals
            WHERE user_id = %s 
            AND is_completed = TRUE
            AND meal_date >= %s 
            AND meal_date < %s
        """
        cursor.execute(completed_meals_query, (user_id, start_date, end_date))
        completed_meals_result = cursor.fetchone()
        completed_meals_count = completed_meals_result["completed_count"] if completed_meals_result else 0

        # For new recipes, we'll count unique recipe templates used this month
        new_recipes_query = """
            SELECT COUNT(DISTINCT m.recipe_template_id) as unique_recipes
            FROM meals m
            WHERE m.user_id = %s 
            AND m.recipe_template_id IS NOT NULL
            AND m.meal_date >= %s 
            AND m.meal_date < %s
        """
        cursor.execute(new_recipes_query, (user_id, start_date, end_date))
        new_recipes_result = cursor.fetchone()
        new_recipes_count = new_recipes_result["unique_recipes"] if new_recipes_result else 0


        return jsonify({
            "success": True,
            "progress": {
                "meal_plans_count": meal_plans_count,
                "completed_meals_count": completed_meals_count,
                "new_recipes_count": new_recipes_count,
                "month": month,
                "year": year
            }
        })

    except Exception as e:
        return jsonify({"success": False, "message": f"Failed to get goals progress: {str(e)}"})
    finally:
        cursor.close()


@meal_goals_bp.route("/meal-goals", methods=["DELETE"])
def delete_meal_goals():
    """Delete meal goals for a specific month/year"""
    if "user_ID" not in session:
        return jsonify({"success": False, "message": "Not authenticated"})

    user_id = session["user_ID"]
    month = request.args.get("month", datetime.now().month)
    year = request.args.get("year", datetime.now().year)

    try:
        month = int(month)
        year = int(year)
    except (ValueError, TypeError):
        return jsonify({"success": False, "message": "Invalid month or year format"})

    db = get_db()
    cursor = db.cursor()

    try:
        delete_query = """
            DELETE FROM monthly_meal_goals 
            WHERE user_id = %s AND month = %s AND year = %s
        """
        cursor.execute(delete_query, (user_id, month, year))
        db.commit()

        if cursor.rowcount > 0:
            return jsonify({"success": True, "message": "Meal goals deleted successfully"})
        else:
            return jsonify({"success": False, "message": "No goals found for the specified month/year"})

    except Exception as e:
        db.rollback()
        return jsonify({"success": False, "message": f"Failed to delete meal goals: {str(e)}"})
    finally:
        cursor.close()