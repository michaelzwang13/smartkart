from flask import Blueprint, request, jsonify, session, current_app
import requests
from src.database import get_db
from src import helper

budget_bp = Blueprint("budget", __name__, url_prefix="/api")

# Budget API Routes

@budget_bp.route("/budget/overview", methods=["GET"])
def get_budget_overview():
    """Get budget overview with spending data"""
    if "user_ID" not in session:
        return jsonify({"error": "Not authenticated"}), 401

    user_ID = session["user_ID"]
    db = get_db()
    cursor = db.cursor()

    try:
        # Get user's current budget settings (or default)
        settings_query = """
            SELECT monthly_budget, alert_threshold, budget_period 
            FROM user_budget_settings 
            WHERE user_id = %s
        """
        cursor.execute(settings_query, (user_ID,))
        budget_settings = cursor.fetchone()

        if not budget_settings:
            # Create default settings for new user
            insert_settings = """
                INSERT INTO user_budget_settings (user_id, monthly_budget, alert_threshold, budget_period)
                VALUES (%s, 1000.00, 80.00, 'monthly')
            """
            cursor.execute(insert_settings, (user_ID,))
            db.commit()

            monthly_budget = 1000
            alert_threshold = 80
            budget_period = "monthly"
        else:
            monthly_budget = float(budget_settings["monthly_budget"])
            alert_threshold = float(budget_settings["alert_threshold"])
            budget_period = budget_settings["budget_period"]

        # Get or create current month's budget entry
        budget_query = """
            SELECT budget_id, allocated_amount, total_spent, remaining_amount
            FROM budget 
            WHERE user_id = %s 
              AND MONTH(created_at) = MONTH(CURRENT_DATE())
              AND YEAR(created_at) = YEAR(CURRENT_DATE())
              AND list_id IS NULL
            ORDER BY created_at DESC
            LIMIT 1
        """
        cursor.execute(budget_query, (user_ID,))
        current_budget = cursor.fetchone()

        if not current_budget:
            # Create new budget entry for this month
            insert_budget = """
                INSERT INTO budget (user_id, allocated_amount, alert_threshold)
                VALUES (%s, %s, %s)
            """
            cursor.execute(
                insert_budget, (user_ID, monthly_budget, alert_threshold / 100)
            )
            db.commit()

            allocated_amount = monthly_budget
            total_spent = 0
            remaining = monthly_budget
        else:
            allocated_amount = float(current_budget["allocated_amount"])
            total_spent = float(current_budget["total_spent"] or 0)
            remaining = float(current_budget["remaining_amount"] or 0)

        # Get total trips this month
        trips_query = """
            SELECT COUNT(DISTINCT c.cart_ID) as total_trips
            FROM shopping_cart c
            WHERE c.user_ID = %s 
              AND c.status = 'purchased'
              AND MONTH(c.created_at) = MONTH(CURRENT_DATE())
              AND YEAR(c.created_at) = YEAR(CURRENT_DATE())
        """
        cursor.execute(trips_query, (user_ID,))
        trips_result = cursor.fetchone()
        total_trips = trips_result["total_trips"] or 0

        # Calculate daily average (based on current day of month)
        from datetime import datetime

        current_day = datetime.now().day
        daily_avg = total_spent / current_day if current_day > 0 else 0

        cursor.close()

        return jsonify(
            {
                "monthly_budget": allocated_amount,
                "total_spent": total_spent,
                "remaining": remaining,
                "daily_average": daily_avg,
                "total_trips": total_trips,
                "alert_threshold": alert_threshold,
                "budget_period": budget_period,
            }
        )

    except Exception as e:
        db.rollback()
        return jsonify({"error": f"Failed to get budget overview: {str(e)}"}), 500
    finally:
        cursor.close()


@budget_bp.route("/budget/spending-trends", methods=["GET"])
def get_spending_trends():
    """Get spending trends for charts"""
    if "user_ID" not in session:
        return jsonify({"error": "Not authenticated"}), 401

    user_ID = session["user_ID"]
    period = request.args.get("period", "7d")  # 7d, 1m, 3m, 1y
    
    db = get_db()
    cursor = db.cursor()

    try:
        if period == "7d":
            # Last 7 days - daily buckets
            query = """
                SELECT DATE(c.created_at) as date, 
                       COALESCE(SUM(i.price * i.quantity), 0) as amount
                FROM shopping_cart c
                LEFT JOIN cart_item i ON c.cart_ID = i.cart_ID
                WHERE c.user_ID = %s 
                  AND c.status = 'purchased'
                  AND c.created_at >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
                GROUP BY DATE(c.created_at)
                ORDER BY date
            """
        elif period == "1m":
            # Last 30-31 days - weekly buckets (4-5 bars)
            query = """
                SELECT 
                    DATE(DATE_SUB(c.created_at, INTERVAL WEEKDAY(c.created_at) DAY)) AS date,
                    COALESCE(SUM(i.price * i.quantity), 0) AS amount
                FROM shopping_cart c
                LEFT JOIN cart_item i ON c.cart_ID = i.cart_ID
                WHERE c.user_ID = %s
                    AND c.status = 'purchased'
                    AND c.created_at >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
                GROUP BY date
                ORDER BY date;
            """
        elif period == "3m":
            # Last 90 days - weekly buckets (6-12 bars)
            query = """
                SELECT 
                    DATE(DATE_SUB(c.created_at, INTERVAL WEEKDAY(c.created_at) DAY)) AS date,
                    COALESCE(SUM(i.price * i.quantity), 0) AS amount
                FROM shopping_cart c
                LEFT JOIN cart_item i ON c.cart_ID = i.cart_ID
                WHERE c.user_ID = %s
                    AND c.status = 'purchased'
                    AND c.created_at >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
                GROUP BY date
                ORDER BY date;
            """
        else:  # 1y - Last 12 months - monthly buckets
            query = """
                SELECT 
                    DATE(DATE_FORMAT(c.created_at, '%Y-%m-01')) AS date,
                    COALESCE(SUM(i.price * i.quantity), 0) AS amount
                FROM shopping_cart c
                LEFT JOIN cart_item i ON c.cart_ID = i.cart_ID
                WHERE c.user_ID = %s 
                    AND c.status = 'purchased'
                    AND c.created_at >= DATE_SUB(CURRENT_DATE(), INTERVAL 12 MONTH)
                GROUP BY DATE(DATE_FORMAT(c.created_at, '%Y-%m-01'))
                ORDER BY date;
            """

        cursor.execute(query, (user_ID,))
        trends = cursor.fetchall()
        
        # Create a complete date range for the period
        from datetime import datetime, timedelta
        import calendar

        # Debug: print raw data
        print(f"DEBUG: Period={period}, Raw trends count: {len(trends)}")
        for trend in trends:
            print(f"DEBUG: Raw trend: {trend}")

        # Convert existing data to dictionary for easy lookup
        trend_data = {}
        for trend in trends:
            date_key = trend["date"].strftime("%Y-%m-%d")
            trend_data[date_key] = float(trend["amount"])
            print(f"DEBUG: Added to trend_data: {date_key} = {trend_data[date_key]}")
        
        print(trend_data)

        # Generate complete date range and labels based on period
        formatted_trends = []
        if period == "7d":
            # Last 7 days - daily buckets (7 bars)
            for i in range(7):
                date = (datetime.now() - timedelta(days=6 - i)).date()
                date_str = date.strftime("%Y-%m-%d")
                label = date.strftime("%b %d")  # "Jul 14", "Jul 15"
                formatted_trends.append(
                    {
                        "date": date_str,
                        "label": label,
                        "amount": trend_data.get(date_str, 0.0),
                    }
                )
        else: # 1m, 3m, 1y
            for date_str, amount in trend_data.items():
                # Convert string to datetime object
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")

                # Format the label
                label = "Week of " if period == "1m" else ""
                label += date_obj.strftime('%b %d')

                formatted_trends.append({
                    "date": date_str,
                    "label": label,
                    "amount": amount,
                })

        cursor.close()

        print(f"DEBUG: Final formatted_trends: {formatted_trends}")

        return jsonify({"trends": formatted_trends, "period": period})

    except Exception as e:
        return jsonify({"error": f"Failed to get spending trends: {str(e)}"}), 500
    finally:
        cursor.close()


@budget_bp.route("/budget/spending-details", methods=["GET"])
def get_spending_details():
    """Get detailed shopping items for a specific time period"""
    if "user_ID" not in session:
        return jsonify({"error": "Not authenticated"}), 401

    user_ID = session["user_ID"]
    period = request.args.get("period", "7d")
    date = request.args.get("date")  # Specific date for the bar clicked

    if not date:
        return jsonify({"error": "Date parameter required"}), 400

    db = get_db()
    cursor = db.cursor()

    try:
        from datetime import datetime, timedelta

        # Parse the date
        try:
            target_date = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"error": "Invalid date format"}), 400

        # Build query based on period type to get items for the specific time range
        if period == "7d":
            # Single day
            query = """
                SELECT c.cart_ID, c.store_name, c.created_at,
                       i.item_name, i.quantity, i.price, i.image_url,
                       (i.quantity * i.price) as item_total
                FROM shopping_cart c
                JOIN cart_item i ON c.cart_ID = i.cart_ID
                WHERE c.user_ID = %s 
                  AND c.status = 'purchased'
                  AND DATE(c.created_at) = %s
                ORDER BY c.created_at DESC, i.item_name ASC
            """
            cursor.execute(query, (user_ID, target_date))
        elif period == "1m" or period == "3m":
            # Week range (Monday to Sunday)
            week_start = target_date
            week_end = target_date + timedelta(days=6)
            query = """
                SELECT c.cart_ID, c.store_name, c.created_at,
                       i.item_name, i.quantity, i.price, i.image_url,
                       (i.quantity * i.price) as item_total
                FROM shopping_cart c
                JOIN cart_item i ON c.cart_ID = i.cart_ID
                WHERE c.user_ID = %s 
                  AND c.status = 'purchased'
                  AND DATE(c.created_at) BETWEEN %s AND %s
                ORDER BY c.created_at DESC, i.item_name ASC
            """
            cursor.execute(query, (user_ID, week_start, week_end))
        else:  # 1y - Monthly range
            # Entire month
            if target_date.month == 12:
                month_end = target_date.replace(
                    year=target_date.year + 1, month=1, day=1
                ) - timedelta(days=1)
            else:
                month_end = target_date.replace(
                    month=target_date.month + 1, day=1
                ) - timedelta(days=1)

            query = """
                SELECT c.cart_ID, c.store_name, c.created_at,
                       i.item_name, i.quantity, i.price, i.image_url,
                       (i.quantity * i.price) as item_total
                FROM shopping_cart c
                JOIN cart_item i ON c.cart_ID = i.cart_ID
                WHERE c.user_ID = %s 
                  AND c.status = 'purchased'
                  AND DATE(c.created_at) BETWEEN %s AND %s
                ORDER BY c.created_at DESC, i.item_name ASC
            """
            cursor.execute(query, (user_ID, target_date, month_end))

        items = cursor.fetchall()

        # Group items by shopping trip (cart_ID)
        trips = {}
        total_amount = 0

        for item in items:
            cart_id = item["cart_ID"]
            item_total = float(item["item_total"])
            total_amount += item_total

            if cart_id not in trips:
                trips[cart_id] = {
                    "cart_id": cart_id,
                    "store_name": item["store_name"],
                    "date": item["created_at"].strftime("%Y-%m-%d"),
                    "datetime": item["created_at"].strftime("%b %d, %Y at %I:%M %p"),
                    "items": [],
                    "trip_total": 0,
                }

            trips[cart_id]["items"].append(
                {
                    "name": item["item_name"],
                    "quantity": item["quantity"],
                    "price": float(item["price"]),
                    "total": item_total,
                    "image_url": item["image_url"],
                }
            )
            trips[cart_id]["trip_total"] += item_total

        # Convert to list and sort by date
        trips_list = list(trips.values())
        trips_list.sort(key=lambda x: x["date"], reverse=True)

        cursor.close()

        # Determine period label
        period_labels = {
            "7d": target_date.strftime("%B %d, %Y"),
            "1m": f"Week of {target_date.strftime('%B %d, %Y')}",
            "3m": f"Week of {target_date.strftime('%B %d, %Y')}",
            "1y": target_date.strftime("%B %Y"),
        }

        return jsonify(
            {
                "period_label": period_labels.get(
                    period, target_date.strftime("%B %d, %Y")
                ),
                "total_amount": round(total_amount, 2),
                "total_trips": len(trips_list),
                "total_items": sum(len(trip["items"]) for trip in trips_list),
                "trips": trips_list,
            }
        )

    except Exception as e:
        return jsonify({"error": f"Failed to get spending details: {str(e)}"}), 500
    finally:
        cursor.close()


@budget_bp.route("/budget/categories", methods=["GET"])
def get_category_breakdown():
    """Get spending breakdown by category"""
    if "user_ID" not in session:
        return jsonify({"error": "Not authenticated"}), 401

    user_ID = session["user_ID"]
    db = get_db()
    cursor = db.cursor()

    try:
        # Get current month's items
        query = """
            SELECT i.item_name, SUM(i.price * i.quantity) as amount
            FROM shopping_cart c
            JOIN cart_item i ON c.cart_ID = i.cart_ID
            WHERE c.user_ID = %s 
              AND c.status = 'purchased'
              AND MONTH(c.created_at) = MONTH(CURRENT_DATE())
              AND YEAR(c.created_at) = YEAR(CURRENT_DATE())
            GROUP BY i.item_name
            ORDER BY amount DESC
        """
        cursor.execute(query, (user_ID,))
        items = cursor.fetchall()

        # Simple categorization logic
        categories = {
            "Fresh Produce": {"amount": 0, "items": []},
            "Meat & Seafood": {"amount": 0, "items": []},
            "Bakery & Dairy": {"amount": 0, "items": []},
            "Pantry Items": {"amount": 0, "items": []},
            "Frozen Foods": {"amount": 0, "items": []},
            "Beverages": {"amount": 0, "items": []},
        }

        # Categorization keywords
        category_keywords = {
            "Fresh Produce": [
                "apple",
                "banana",
                "orange",
                "lettuce",
                "tomato",
                "potato",
                "carrot",
                "onion",
                "fruit",
                "vegetable",
            ],
            "Meat & Seafood": [
                "chicken",
                "beef",
                "pork",
                "fish",
                "salmon",
                "turkey",
                "ham",
                "meat",
            ],
            "Bakery & Dairy": [
                "milk",
                "cheese",
                "yogurt",
                "butter",
                "bread",
                "bagel",
                "muffin",
                "dairy",
            ],
            "Frozen Foods": ["frozen", "ice cream", "pizza"],
            "Beverages": [
                "juice",
                "soda",
                "water",
                "coffee",
                "tea",
                "beer",
                "wine",
                "drink",
            ],
        }

        for item in items:
            item_name = item["item_name"].lower()
            amount = float(item["amount"])

            categorized = False
            for category, keywords in category_keywords.items():
                if any(keyword in item_name for keyword in keywords):
                    categories[category]["amount"] += amount
                    categories[category]["items"].append(item["item_name"])
                    categorized = True
                    break

            if not categorized:
                categories["Pantry Items"]["amount"] += amount
                categories["Pantry Items"]["items"].append(item["item_name"])

        cursor.close()

        return jsonify({"categories": categories})

    except Exception as e:
        return jsonify({"error": f"Failed to get category breakdown: {str(e)}"}), 500
    finally:
        cursor.close()


@budget_bp.route("/budget/settings", methods=["POST"])
def update_budget_settings():
    """Update user's budget settings"""
    if "user_ID" not in session:
        return jsonify({"error": "Not authenticated"}), 401

    user_ID = session["user_ID"]
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    monthly_budget = float(data.get("monthly_budget", 1000))
    budget_period = data.get("budget_period", "monthly")
    alert_threshold = float(data.get("alert_threshold", 80))
    category_limits = data.get("category_limits", "enabled")

    db = get_db()
    cursor = db.cursor()

    try:
        # Check if user already has budget settings
        check_query = "SELECT user_id FROM user_budget_settings WHERE user_id = %s"
        cursor.execute(check_query, (user_ID,))
        existing = cursor.fetchone()

        if existing:
            # Update existing settings
            update_query = """
                UPDATE user_budget_settings 
                SET monthly_budget = %s, budget_period = %s, alert_threshold = %s, 
                    category_limits_enabled = %s, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = %s
            """
            cursor.execute(
                update_query,
                (
                    monthly_budget,
                    budget_period,
                    alert_threshold,
                    category_limits == "enabled",
                    user_ID,
                ),
            )
        else:
            # Create new settings
            insert_query = """
                INSERT INTO user_budget_settings 
                (user_id, monthly_budget, budget_period, alert_threshold, category_limits_enabled)
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(
                insert_query,
                (
                    user_ID,
                    monthly_budget,
                    budget_period,
                    alert_threshold,
                    category_limits == "enabled",
                ),
            )

        # Update current month's budget allocation if it exists
        update_budget_query = """
            UPDATE budget 
            SET allocated_amount = %s, alert_threshold = %s, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = %s 
              AND MONTH(created_at) = MONTH(CURRENT_DATE())
              AND YEAR(created_at) = YEAR(CURRENT_DATE())
              AND list_id IS NULL
        """
        cursor.execute(
            update_budget_query, (monthly_budget, alert_threshold / 100, user_ID)
        )

        db.commit()
        cursor.close()

        return jsonify(
            {"status": "success", "message": "Budget settings updated successfully"}
        )

    except Exception as e:
        db.rollback()
        return jsonify({"error": f"Failed to update budget settings: {str(e)}"}), 500
    finally:
        cursor.close()


def update_budget_spending(user_id, amount_spent):
    """Helper function to update budget total_spent when a shopping trip is completed"""
    db = get_db()
    cursor = db.cursor()

    try:
        # Get current month's budget entry
        budget_query = """
            SELECT budget_id FROM budget 
            WHERE user_id = %s 
              AND MONTH(created_at) = MONTH(CURRENT_DATE())
              AND YEAR(created_at) = YEAR(CURRENT_DATE())
              AND list_id IS NULL
            ORDER BY created_at DESC
            LIMIT 1
        """
        cursor.execute(budget_query, (user_id,))
        budget_entry = cursor.fetchone()

        if budget_entry:
            # Update existing budget entry
            update_query = """
                UPDATE budget 
                SET total_spent = total_spent + %s, updated_at = CURRENT_TIMESTAMP
                WHERE budget_id = %s
            """
            cursor.execute(update_query, (amount_spent, budget_entry["budget_id"]))
        else:
            # Get user's budget settings to create new entry
            settings_query = "SELECT monthly_budget, alert_threshold FROM user_budget_settings WHERE user_id = %s"
            cursor.execute(settings_query, (user_id,))
            settings = cursor.fetchone()

            monthly_budget = settings["monthly_budget"] if settings else 1000
            alert_threshold = settings["alert_threshold"] if settings else 80

            # Create new budget entry
            insert_query = """
                INSERT INTO budget (user_id, allocated_amount, total_spent, alert_threshold)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(
                insert_query,
                (user_id, monthly_budget, amount_spent, alert_threshold / 100),
            )

        db.commit()

    except Exception as e:
        db.rollback()
        print(f"Error updating budget spending: {str(e)}")
    finally:
        cursor.close()


# MOVED TO shopping_trip_routes.py
# TEMPORARILY DISABLED - Shopping trip details API
"""
@budget_bp.route('/shopping-trip/details', methods=['GET'])
def get_shopping_trip_details():
    #Get detailed items for a specific shopping trip#
    if 'user_ID' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user_ID = session['user_ID']
    cart_id = request.args.get('cart_id')
    
    if not cart_id:
        return jsonify({'error': 'Cart ID parameter required'}), 400
    
    db = get_db()
    cursor = db.cursor()
    
    try:
        # Get cart info and verify ownership
        cart_query = \"\"\"
            SELECT cart_ID, store_name, created_at
            FROM shopping_cart 
            WHERE cart_ID = %s AND user_ID = %s AND status = 'purchased'
        \"\"\"
        cursor.execute(cart_query, (cart_id, user_ID))
        cart = cursor.fetchone()
        
        if not cart:
            return jsonify({'error': 'Shopping trip not found'}), 404
        
        # Get all items for this cart
        items_query = \"\"\"
            SELECT item_name, quantity, price, image_url
            FROM cart_item 
            WHERE cart_ID = %s
            ORDER BY item_name ASC
        \"\"\"
        cursor.execute(items_query, (cart_id,))
        items = cursor.fetchall()
        
        # Calculate totals
        total_items = sum(item['quantity'] for item in items)
        total_amount = sum(item['price'] * item['quantity'] for item in items)
        
        cursor.close()
        
        return jsonify({
            'cart_id': cart['cart_ID'],
            'store_name': cart['store_name'], 
            'created_at': cart['created_at'].strftime('%Y-%m-%d %H:%M:%S'),
            'items': items,
            'total_items': total_items,
            'total_amount': float(total_amount)
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get shopping trip details: {str(e)}'}), 500
    finally:
        cursor.close()
"""