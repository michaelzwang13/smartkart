from flask import Blueprint, request, jsonify, session, current_app
import requests
from src.database import get_db
from src import helper

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.route("/shopping-trip/add-item", methods=["POST"])
def add_item():
    if "user_ID" not in session or "cart_ID" not in session:
        return jsonify({"error": "User or cart not in session"}), 400

    data = request.get_json()
    required_fields = ["upc", "price", "quantity", "itemName", "imageUrl"]
    if not data or not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    db = get_db()
    cursor = db.cursor()
    ins = "INSERT INTO cart_item (cart_ID, user_ID, quantity, item_name, price, upc, item_lifetime, image_url) VALUES(%s, %s, %s, %s, %s, %s, %s, %s)"
    cursor.execute(
        ins,
        (
            session["cart_ID"],
            session["user_ID"],
            data["quantity"],
            data["itemName"],
            data["price"],
            data["upc"],
            7,
            data["imageUrl"],
        ),
    )
    db.commit()

    query = "SELECT * FROM cart_item WHERE cart_ID = %s"
    cursor.execute(query, (session["cart_ID"],))
    items = cursor.fetchall()
    cursor.close()

    return jsonify({"status": "success", "items": items}), 200


@api_bp.route("/shopping-trip/remove-last-item", methods=["POST"])
def remove_last_item():
    """Remove the most recently added item from the cart"""
    if "user_ID" not in session or "cart_ID" not in session:
        return jsonify({"error": "User or cart not in session"}), 400

    db = get_db()
    cursor = db.cursor()

    try:
        # Get the most recently added item
        query = "SELECT item_ID FROM cart_item WHERE cart_ID = %s ORDER BY item_ID DESC LIMIT 1"
        cursor.execute(query, (session["cart_ID"],))
        last_item = cursor.fetchone()

        if last_item:
            # Delete the item
            delete_query = "DELETE FROM cart_item WHERE item_ID = %s"
            cursor.execute(delete_query, (last_item["item_ID"],))
            db.commit()

            # Return updated cart items
            query = "SELECT * FROM cart_item WHERE cart_ID = %s"
            cursor.execute(query, (session["cart_ID"],))
            items = cursor.fetchall()
            cursor.close()

            return jsonify({"status": "success", "items": items}), 200
        else:
            return jsonify({"error": "No items to remove"}), 400

    except Exception as e:
        db.rollback()
        return jsonify({"error": f"Failed to remove item: {str(e)}"}), 500
    finally:
        cursor.close()


@api_bp.route("/shopping-trip/update-item", methods=["POST"])
def update_item_quantity():
    """Update the quantity of an item in the cart"""
    if "user_ID" not in session or "cart_ID" not in session:
        return jsonify({"error": "User or cart not in session"}), 400

    data = request.get_json()
    if not data or "item_id" not in data or "quantity" not in data:
        return jsonify({"error": "Missing item_id or quantity"}), 400

    item_id = data["item_id"]
    quantity = data["quantity"]

    try:
        quantity = int(quantity)
        if quantity < 1:
            return jsonify({"error": "Quantity must be at least 1"}), 400
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid quantity"}), 400

    db = get_db()
    cursor = db.cursor()

    try:
        # Verify the item belongs to the current user's cart
        verify_query = "SELECT item_ID FROM cart_item WHERE item_ID = %s AND cart_ID = %s AND user_ID = %s"
        cursor.execute(verify_query, (item_id, session["cart_ID"], session["user_ID"]))
        if not cursor.fetchone():
            return jsonify({"error": "Item not found"}), 404

        # Update the quantity
        update_query = "UPDATE cart_item SET quantity = %s WHERE item_ID = %s"
        cursor.execute(update_query, (quantity, item_id))
        db.commit()

        # Return updated cart items
        query = "SELECT item_ID, item_name, price, quantity, image_url FROM cart_item WHERE cart_ID = %s"
        cursor.execute(query, (session["cart_ID"],))
        items = cursor.fetchall()

        # Calculate totals
        total_items = sum(item["quantity"] for item in items)
        total_spent = sum(item["price"] * item["quantity"] for item in items)
        allocated_budget = 1000
        remaining = allocated_budget - total_spent

        cursor.close()

        return (
            jsonify(
                {
                    "status": "success",
                    "items": items,
                    "total_items": total_items,
                    "total_spent": total_spent,
                    "allocated_budget": allocated_budget,
                    "remaining": remaining,
                }
            ),
            200,
        )

    except Exception as e:
        db.rollback()
        return jsonify({"error": f"Failed to update item: {str(e)}"}), 500
    finally:
        cursor.close()


@api_bp.route("/shopping-trip/delete-item", methods=["POST"])
def delete_item():
    """Delete a specific item from the cart"""
    if "user_ID" not in session or "cart_ID" not in session:
        return jsonify({"error": "User or cart not in session"}), 400

    data = request.get_json()
    if not data or "item_id" not in data:
        return jsonify({"error": "Missing item_id"}), 400

    item_id = data["item_id"]

    db = get_db()
    cursor = db.cursor()

    try:
        # Verify the item belongs to the current user's cart
        verify_query = "SELECT item_ID FROM cart_item WHERE item_ID = %s AND cart_ID = %s AND user_ID = %s"
        cursor.execute(verify_query, (item_id, session["cart_ID"], session["user_ID"]))
        if not cursor.fetchone():
            return jsonify({"error": "Item not found"}), 404

        # Delete the item
        delete_query = "DELETE FROM cart_item WHERE item_ID = %s"
        cursor.execute(delete_query, (item_id,))
        db.commit()

        # Return updated cart items
        query = "SELECT item_ID, item_name, price, quantity, image_url FROM cart_item WHERE cart_ID = %s"
        cursor.execute(query, (session["cart_ID"],))
        items = cursor.fetchall()

        # Calculate totals
        total_items = sum(item["quantity"] for item in items)
        total_spent = sum(item["price"] * item["quantity"] for item in items)
        allocated_budget = 1000
        remaining = allocated_budget - total_spent

        cursor.close()

        return (
            jsonify(
                {
                    "status": "success",
                    "items": items,
                    "total_items": total_items,
                    "total_spent": total_spent,
                    "allocated_budget": allocated_budget,
                    "remaining": remaining,
                }
            ),
            200,
        )

    except Exception as e:
        db.rollback()
        return jsonify({"error": f"Failed to delete item: {str(e)}"}), 500
    finally:
        cursor.close()


@api_bp.route("/shopping-trip/items", methods=["GET"])
def get_cart_items():
    if "cart_ID" not in session or not session["cart_ID"]:
        return jsonify(
            {
                "items": [],
                "total_items": 0,
                "total_spent": 0,
                "allocated_budget": 1000,
                "remaining": 1000,
            }
        )

    db = get_db()
    cursor = db.cursor()

    # Get items
    query = "SELECT item_ID, item_name, price, quantity, image_url FROM cart_item WHERE cart_ID = %s"
    cursor.execute(query, (session["cart_ID"],))
    items = cursor.fetchall()

    # Calculate totals
    total_items = sum(item["quantity"] for item in items)
    total_spent = sum(item["price"] * item["quantity"] for item in items)
    allocated_budget = 1000  # You can make this dynamic later
    remaining = allocated_budget - total_spent

    cursor.close()

    return jsonify(
        {
            "items": items,
            "total_items": total_items,
            "total_spent": total_spent,
            "allocated_budget": allocated_budget,
            "remaining": remaining,
        }
    )


@api_bp.route("/searchitem", methods=["GET"])
def searchitem():
    """Search for item by UPC using Nutritionix API"""
    api_id = current_app.config.get("NUTRITIONIX_API_ID")
    api_key = current_app.config.get("NUTRITIONIX_API_KEY")

    if not api_id or not api_key:
        return (
            jsonify({"error": "Nutritionix API keys are not configured", "foods": []}),
            500,
        )

    upc = request.args.get("upc")
    if not upc:
        return jsonify({"error": "UPC parameter is required"}), 400

    # Clean UPC - remove any whitespace and validate basic format
    upc = upc.strip()
    if not upc.isdigit() or len(upc) < 8:
        return jsonify({"error": "Invalid UPC format", "foods": []}), 400

    url = f"https://trackapi.nutritionix.com/v2/search/item?upc={upc}"
    headers = {
        "x-app-id": api_id,
        "x-app-key": api_key,
        "Content-Type": "application/json",
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 404:
            # Item not found in Nutritionix database
            return jsonify(
                {
                    "foods": [],
                    "message": "Product not found in database",
                    "fallback": create_fallback_item(upc),
                }
            )

        response.raise_for_status()
        api_data = response.json()

        # Return the API response with enhanced structure
        return jsonify(
            {
                "foods": api_data.get("foods", []),
                "message": "Product found successfully",
                "upc": upc,
            }
        )

    except requests.exceptions.Timeout:
        return (
            jsonify(
                {
                    "error": "API request timed out",
                    "foods": [],
                    "fallback": create_fallback_item(upc),
                }
            ),
            408,
        )

    except requests.exceptions.RequestException as e:
        return (
            jsonify(
                {
                    "error": f"API request failed: {str(e)}",
                    "foods": [],
                    "fallback": create_fallback_item(upc),
                }
            ),
            500,
        )


def create_fallback_item(upc):
    """Create a fallback item when API fails or item not found"""
    return {
        "food_name": f"Unknown Product (UPC: {upc})",
        "brand_name": "Unknown Brand",
        "nf_total_carbohydrate": 0,
        "nf_sugars": 0,
        "nf_sodium": 0,
        "nf_saturated_fat": 0,
        "nf_calories": 0,
        "photo": {
            "thumb": "https://t4.ftcdn.net/jpg/02/51/95/53/360_F_251955356_FAQH0U1y1TZw3ZcdPGybwUkH90a3VAhb.jpg"
        },
        "upc": upc,
        "is_fallback": True,
    }


# Additional route alias for better API consistency
@api_bp.route("/upc-lookup", methods=["GET"])
def upc_lookup():
    """Alias for searchitem endpoint for better API naming"""
    return searchitem()


@api_bp.route("/predict")
def predict():
    carbs = request.args.get("carbs", 0)
    sugar = request.args.get("sugar", 0)
    sodium = request.args.get("sodium", 0)
    fat = request.args.get("fat", 0)

    if helper.model is None:
        return jsonify({"error": "Model not loaded"}), 500

    prediction = helper.predict_impulsive_purchase(carbs, sugar, sodium, fat).item()
    return jsonify({"prediction": int(prediction)})


@api_bp.route("/learn")
def learn():
    carbs = request.args.get("carbs", 0)
    sugar = request.args.get("sugar", 0)
    sodium = request.args.get("sodium", 0)
    fat = request.args.get("fat", 0)

    if helper.model is None:
        return jsonify({"error": "Model not loaded"}), 500

    helper.model_learn(carbs, sugar, sodium, fat)
    return jsonify({"status": "learned"}), 200


# Budget API Routes


@api_bp.route("/budget/overview", methods=["GET"])
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


@api_bp.route("/budget/spending-trends", methods=["GET"])
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
                SELECT DATE(DATE_SUB(c.created_at, INTERVAL DAYOFWEEK(c.created_at)-2 DAY)) as date,
                       COALESCE(SUM(i.price * i.quantity), 0) as amount
                FROM shopping_cart c
                LEFT JOIN cart_item i ON c.cart_ID = i.cart_ID
                WHERE c.user_ID = %s 
                  AND c.status = 'purchased'
                  AND c.created_at >= DATE_SUB(CURRENT_DATE(), INTERVAL 31 DAY)
                GROUP BY YEARWEEK(c.created_at, 1)
                ORDER BY date
            """
        elif period == "3m":
            # Last 90 days - weekly buckets (6-12 bars)
            query = """
                SELECT DATE(DATE_SUB(c.created_at, INTERVAL DAYOFWEEK(c.created_at)-2 DAY)) as date,
                       COALESCE(SUM(i.price * i.quantity), 0) as amount
                FROM shopping_cart c
                LEFT JOIN cart_item i ON c.cart_ID = i.cart_ID
                WHERE c.user_ID = %s 
                  AND c.status = 'purchased'
                  AND c.created_at >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
                GROUP BY YEARWEEK(c.created_at, 1)
                ORDER BY date
            """
        else:  # 1y - Last 12 months - monthly buckets
            query = """
                SELECT DATE(CONCAT(YEAR(c.created_at), '-', LPAD(MONTH(c.created_at), 2, '0'), '-01')) as date,
                       COALESCE(SUM(i.price * i.quantity), 0) as amount
                FROM shopping_cart c
                LEFT JOIN cart_item i ON c.cart_ID = i.cart_ID
                WHERE c.user_ID = %s 
                  AND c.status = 'purchased'
                  AND c.created_at >= DATE_SUB(CURRENT_DATE(), INTERVAL 12 MONTH)
                GROUP BY YEAR(c.created_at), MONTH(c.created_at)
                ORDER BY date
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
        elif period == "1m":
            # Last 31 days - weekly buckets (4-5 bars)
            # Simplify: just sum all data from trend_data and create 5 weeks
            weeks_back = 5
            for i in range(weeks_back):
                # Calculate week start (Monday of each week)
                days_back = (weeks_back - 1 - i) * 7 + datetime.now().weekday()
                week_start = (datetime.now() - timedelta(days=days_back)).date()

                # Sum all data for this week
                week_amount = 0.0
                for j in range(7):  # Sum 7 days of the week
                    day = week_start + timedelta(days=j)
                    day_str = day.strftime("%Y-%m-%d")
                    week_amount += trend_data.get(day_str, 0.0)

                week_start_str = week_start.strftime("%Y-%m-%d")
                label = f"Week of {week_start.strftime('%b %d')}"
                formatted_trends.append(
                    {"date": week_start_str, "label": label, "amount": week_amount}
                )
        elif period == "3m":
            # Last 90 days - weekly buckets (12 bars)
            weeks_back = 12
            for i in range(weeks_back):
                # Calculate week start (Monday of each week)
                days_back = (weeks_back - 1 - i) * 7 + datetime.now().weekday()
                week_start = (datetime.now() - timedelta(days=days_back)).date()

                # Sum all data for this week
                week_amount = 0.0
                for j in range(7):  # Sum 7 days of the week
                    day = week_start + timedelta(days=j)
                    day_str = day.strftime("%Y-%m-%d")
                    week_amount += trend_data.get(day_str, 0.0)

                week_start_str = week_start.strftime("%Y-%m-%d")
                label = f"Week of {week_start.strftime('%b %d')}"
                formatted_trends.append(
                    {"date": week_start_str, "label": label, "amount": week_amount}
                )
        else:  # 1y - Last 12 months - monthly buckets (12 bars)
            for i in range(12):
                # Calculate month (11 months ago to current month)
                current_month = datetime.now().replace(day=1)
                months_back = 11 - i

                target_month = current_month
                for _ in range(months_back):
                    if target_month.month == 1:
                        target_month = target_month.replace(
                            year=target_month.year - 1, month=12
                        )
                    else:
                        target_month = target_month.replace(
                            month=target_month.month - 1
                        )

                # Sum all data for this month
                month_amount = 0.0
                # Check all possible days in the month
                days_in_month = calendar.monthrange(
                    target_month.year, target_month.month
                )[1]
                for day in range(1, days_in_month + 1):
                    day_date = target_month.replace(day=day)
                    day_str = day_date.strftime("%Y-%m-%d")
                    month_amount += trend_data.get(day_str, 0.0)

                date_str = target_month.strftime("%Y-%m-%d")
                label = target_month.strftime("%b")
                formatted_trends.append(
                    {"date": date_str, "label": label, "amount": month_amount}
                )

        cursor.close()

        print(f"DEBUG: Final formatted_trends: {formatted_trends}")

        return jsonify({"trends": formatted_trends, "period": period})

    except Exception as e:
        return jsonify({"error": f"Failed to get spending trends: {str(e)}"}), 500
    finally:
        cursor.close()


@api_bp.route("/budget/spending-details", methods=["GET"])
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


@api_bp.route("/budget/categories", methods=["GET"])
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


@api_bp.route("/budget/settings", methods=["POST"])
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


# TEMPORARILY DISABLED - Shopping trip details API
"""
@api_bp.route('/shopping-trip/details', methods=['GET'])
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

# Shopping Lists API Routes


@api_bp.route("/shopping-lists", methods=["GET"])
def get_shopping_lists():
    """Get all shopping lists for the current user"""
    if "user_ID" not in session:
        return jsonify({"error": "Not authenticated"}), 401

    user_ID = session["user_ID"]
    db = get_db()
    cursor = db.cursor()

    try:
        # Get all shopping lists for the user
        query = """
            SELECT list_id, list_name, description, created_at, updated_at, is_active
            FROM shopping_lists 
            WHERE user_id = %s AND is_active = TRUE
            ORDER BY updated_at DESC
        """
        cursor.execute(query, (user_ID,))
        lists = cursor.fetchall()

        # For each list, get its items
        for shopping_list in lists:
            list_id = shopping_list["list_id"]
            items_query = """
                SELECT item_id, item_name, quantity, notes, is_completed, created_at, updated_at
                FROM shopping_list_items 
                WHERE list_id = %s
                ORDER BY created_at ASC
            """
            cursor.execute(items_query, (list_id,))
            items = cursor.fetchall()

            # Convert items to list format expected by frontend
            shopping_list["items"] = [
                {
                    "id": item["item_id"],
                    "name": item["item_name"],
                    "quantity": item["quantity"],
                    "notes": item["notes"],
                    "is_completed": bool(item["is_completed"]),
                    "created_at": (
                        item["created_at"].isoformat() if item["created_at"] else None
                    ),
                    "updated_at": (
                        item["updated_at"].isoformat() if item["updated_at"] else None
                    ),
                }
                for item in items
            ]

            # Convert list timestamps to strings
            shopping_list["id"] = shopping_list["list_id"]
            shopping_list["name"] = shopping_list["list_name"]
            shopping_list["created_at"] = (
                shopping_list["created_at"].isoformat()
                if shopping_list["created_at"]
                else None
            )
            shopping_list["updated_at"] = (
                shopping_list["updated_at"].isoformat()
                if shopping_list["updated_at"]
                else None
            )

        return jsonify({"lists": lists})

    except Exception as e:
        return jsonify({"error": f"Failed to fetch shopping lists: {str(e)}"}), 500
    finally:
        cursor.close()


@api_bp.route("/shopping-lists", methods=["POST"])
def create_shopping_list():
    """Create a new shopping list"""
    if "user_ID" not in session:
        return jsonify({"error": "Not authenticated"}), 401

    data = request.get_json()
    user_ID = session["user_ID"]
    list_name = data.get("name", "").strip()
    description = data.get("description", "").strip()

    if not list_name:
        return jsonify({"error": "List name is required"}), 400

    db = get_db()
    cursor = db.cursor()

    try:
        # Insert new shopping list
        query = """
            INSERT INTO shopping_lists (user_id, list_name, description)
            VALUES (%s, %s, %s)
        """
        cursor.execute(query, (user_ID, list_name, description))
        list_id = cursor.lastrowid
        db.commit()

        # Return the created list
        new_list = {
            "id": list_id,
            "name": list_name,
            "description": description,
            "items": [],
            "created_at": None,  # Will be set by database
            "updated_at": None,
        }

        return jsonify({"list": new_list}), 201

    except Exception as e:
        db.rollback()
        return jsonify({"error": f"Failed to create shopping list: {str(e)}"}), 500
    finally:
        cursor.close()


@api_bp.route("/shopping-lists/<int:list_id>", methods=["PATCH"])
def update_shopping_list(list_id):
    """Update a shopping list"""
    if "user_ID" not in session:
        return jsonify({"error": "Not authenticated"}), 401

    data = request.get_json()
    user_ID = session["user_ID"]

    db = get_db()
    cursor = db.cursor()

    try:
        # Verify the list belongs to the user
        verify_query = (
            "SELECT list_id FROM shopping_lists WHERE list_id = %s AND user_id = %s"
        )
        cursor.execute(verify_query, (list_id, user_ID))
        if not cursor.fetchone():
            return jsonify({"error": "Shopping list not found"}), 404

        # Update the list
        update_fields = []
        update_values = []

        if "name" in data:
            update_fields.append("list_name = %s")
            update_values.append(data["name"].strip())

        if "description" in data:
            update_fields.append("description = %s")
            update_values.append(data["description"].strip())

        if update_fields:
            update_values.append(list_id)
            query = f"UPDATE shopping_lists SET {', '.join(update_fields)} WHERE list_id = %s"
            cursor.execute(query, update_values)
            db.commit()

        return jsonify({"success": True})

    except Exception as e:
        db.rollback()
        return jsonify({"error": f"Failed to update shopping list: {str(e)}"}), 500
    finally:
        cursor.close()


@api_bp.route("/shopping-lists/<int:list_id>", methods=["DELETE"])
def delete_shopping_list(list_id):
    """Delete a shopping list"""
    if "user_ID" not in session:
        return jsonify({"error": "Not authenticated"}), 401

    user_ID = session["user_ID"]
    db = get_db()
    cursor = db.cursor()

    try:
        # Verify the list belongs to the user
        verify_query = (
            "SELECT list_id FROM shopping_lists WHERE list_id = %s AND user_id = %s"
        )
        cursor.execute(verify_query, (list_id, user_ID))
        if not cursor.fetchone():
            return jsonify({"error": "Shopping list not found"}), 404

        # Set is_active to FALSE instead of deleting (soft delete)
        query = "UPDATE shopping_lists SET is_active = FALSE WHERE list_id = %s"
        cursor.execute(query, (list_id,))
        db.commit()

        return jsonify({"success": True})

    except Exception as e:
        db.rollback()
        return jsonify({"error": f"Failed to delete shopping list: {str(e)}"}), 500
    finally:
        cursor.close()


@api_bp.route("/shopping-lists/<int:list_id>/items", methods=["POST"])
def add_item_to_list(list_id):
    """Add an item to a shopping list"""
    if "user_ID" not in session:
        return jsonify({"error": "Not authenticated"}), 401

    data = request.get_json()
    user_ID = session["user_ID"]
    item_name = data.get("name", "").strip()
    quantity = data.get("quantity", 1)
    notes = data.get("notes", "").strip()

    if not item_name:
        return jsonify({"error": "Item name is required"}), 400

    try:
        quantity = int(quantity)
        if quantity < 1:
            quantity = 1
    except (ValueError, TypeError):
        quantity = 1

    db = get_db()
    cursor = db.cursor()

    try:
        # Verify the list belongs to the user and check item count
        verify_query = """
            SELECT sl.list_id, COUNT(sli.item_id) as item_count
            FROM shopping_lists sl
            LEFT JOIN shopping_list_items sli ON sl.list_id = sli.list_id
            WHERE sl.list_id = %s AND sl.user_id = %s AND sl.is_active = TRUE
            GROUP BY sl.list_id
        """
        cursor.execute(verify_query, (list_id, user_ID))
        result = cursor.fetchone()

        if not result:
            return jsonify({"error": "Shopping list not found"}), 404

        # Check 25 item limit
        if result["item_count"] >= 25:
            return (
                jsonify({"error": "Cannot add more items. Maximum 25 items per list."}),
                400,
            )

        # Insert new item
        query = """
            INSERT INTO shopping_list_items (list_id, item_name, quantity, notes)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(query, (list_id, item_name, quantity, notes))
        item_id = cursor.lastrowid
        db.commit()

        # Return the created item
        new_item = {
            "id": item_id,
            "name": item_name,
            "quantity": quantity,
            "notes": notes,
            "is_completed": False,
        }

        return jsonify({"item": new_item}), 201

    except Exception as e:
        db.rollback()
        return jsonify({"error": f"Failed to add item: {str(e)}"}), 500
    finally:
        cursor.close()


@api_bp.route(
    "/shopping-lists/<int:list_id>/items/<int:item_id>/toggle", methods=["PATCH"]
)
def toggle_item_completion(list_id, item_id):
    """Toggle item completion status"""
    if "user_ID" not in session:
        return jsonify({"error": "Not authenticated"}), 401

    user_ID = session["user_ID"]
    db = get_db()
    cursor = db.cursor()

    try:
        # Verify the item belongs to a list owned by the user
        verify_query = """
            SELECT sli.item_id, sli.is_completed
            FROM shopping_list_items sli
            JOIN shopping_lists sl ON sli.list_id = sl.list_id
            WHERE sli.item_id = %s AND sli.list_id = %s AND sl.user_id = %s AND sl.is_active = TRUE
        """
        cursor.execute(verify_query, (item_id, list_id, user_ID))
        result = cursor.fetchone()

        if not result:
            return jsonify({"error": "Item not found"}), 404

        # Toggle completion status
        new_status = not bool(result["is_completed"])
        query = "UPDATE shopping_list_items SET is_completed = %s WHERE item_id = %s"
        cursor.execute(query, (new_status, item_id))
        db.commit()

        return jsonify({"success": True, "is_completed": new_status})

    except Exception as e:
        db.rollback()
        return jsonify({"error": f"Failed to toggle item: {str(e)}"}), 500
    finally:
        cursor.close()


@api_bp.route("/shopping-lists/<int:list_id>/items/<int:item_id>", methods=["PATCH"])
def update_shopping_list_item(list_id, item_id):
    """Update a shopping list item (name or quantity)"""
    if "user_ID" not in session:
        return jsonify({"error": "Not authenticated"}), 401

    data = request.get_json()
    user_ID = session["user_ID"]

    db = get_db()
    cursor = db.cursor()

    try:
        # Verify the item belongs to a list owned by the user
        verify_query = """
            SELECT sli.item_id
            FROM shopping_list_items sli
            JOIN shopping_lists sl ON sli.list_id = sl.list_id
            WHERE sli.item_id = %s AND sli.list_id = %s AND sl.user_id = %s AND sl.is_active = TRUE
        """
        cursor.execute(verify_query, (item_id, list_id, user_ID))
        if not cursor.fetchone():
            return jsonify({"error": "Item not found"}), 404

        # Update the item
        update_fields = []
        update_values = []

        if "name" in data:
            item_name = data["name"].strip()
            if not item_name:
                return jsonify({"error": "Item name cannot be empty"}), 400
            update_fields.append("item_name = %s")
            update_values.append(item_name)

        if "quantity" in data:
            try:
                quantity = int(data["quantity"])
                if quantity < 1:
                    return jsonify({"error": "Quantity must be at least 1"}), 400
                update_fields.append("quantity = %s")
                update_values.append(quantity)
            except (ValueError, TypeError):
                return jsonify({"error": "Invalid quantity"}), 400

        if not update_fields:
            return jsonify({"error": "No valid fields to update"}), 400

        # Add updated timestamp and item_id for WHERE clause
        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        update_values.append(item_id)

        query = f"UPDATE shopping_list_items SET {', '.join(update_fields)} WHERE item_id = %s"
        cursor.execute(query, update_values)
        db.commit()

        return jsonify({"success": True})

    except Exception as e:
        db.rollback()
        return jsonify({"error": f"Failed to update item: {str(e)}"}), 500
    finally:
        cursor.close()


@api_bp.route("/shopping-lists/<int:list_id>/items/<int:item_id>", methods=["DELETE"])
def delete_item_from_list(list_id, item_id):
    """Delete an item from a shopping list"""
    if "user_ID" not in session:
        return jsonify({"error": "Not authenticated"}), 401

    user_ID = session["user_ID"]
    db = get_db()
    cursor = db.cursor()

    try:
        # Verify the item belongs to a list owned by the user
        verify_query = """
            SELECT sli.item_id
            FROM shopping_list_items sli
            JOIN shopping_lists sl ON sli.list_id = sl.list_id
            WHERE sli.item_id = %s AND sli.list_id = %s AND sl.user_id = %s AND sl.is_active = TRUE
        """
        cursor.execute(verify_query, (item_id, list_id, user_ID))

        if not cursor.fetchone():
            return jsonify({"error": "Item not found"}), 404

        # Delete the item
        query = "DELETE FROM shopping_list_items WHERE item_id = %s"
        cursor.execute(query, (item_id,))
        db.commit()

        return jsonify({"success": True})

    except Exception as e:
        db.rollback()
        return jsonify({"error": f"Failed to delete item: {str(e)}"}), 500
    finally:
        cursor.close()


# =============================================================================
# PANTRY INTEGRATION API ENDPOINTS
# =============================================================================


@api_bp.route("/pantry/items", methods=["GET"])
def get_pantry_items():
    """Get all pantry items for the current user"""
    if "user_ID" not in session:
        return jsonify({"success": False, "message": "Not authenticated"})

    user_ID = session["user_ID"]
    db = get_db()
    cursor = db.cursor()

    # Get filter parameters
    storage_filter = request.args.get("storage_type", "")
    category_filter = request.args.get("category", "")
    expiry_filter = request.args.get("expiry_status", "")

    try:
        # Build query with filters
        query = """
            SELECT p.*, 
                   CASE 
                       WHEN p.expiration_date IS NULL THEN 'no_expiry'
                       WHEN p.expiration_date < CURDATE() THEN 'expired'
                       WHEN p.expiration_date <= DATE_ADD(CURDATE(), INTERVAL 3 DAY) THEN 'expiring_soon'
                       ELSE 'fresh'
                   END as expiry_status,
                   DATEDIFF(p.expiration_date, CURDATE()) as days_until_expiry
            FROM pantry_items p
            WHERE p.user_id = %s AND p.is_consumed = FALSE
        """
        params = [user_ID]

        # Add storage filter
        if storage_filter:
            query += " AND p.storage_type = %s"
            params.append(storage_filter)

        # Add category filter
        if category_filter:
            query += " AND p.category = %s"
            params.append(category_filter)

        query += " ORDER BY p.expiration_date ASC, p.date_added DESC"

        cursor.execute(query, params)
        all_items = cursor.fetchall()

        # Apply expiry filter if needed (post-query filtering for computed field)
        items = []
        for item in all_items:
            if expiry_filter:
                if expiry_filter == "expired" and item["expiry_status"] != "expired":
                    continue
                elif (
                    expiry_filter == "expiring_soon"
                    and item["expiry_status"] != "expiring_soon"
                ):
                    continue
                elif expiry_filter == "fresh" and item["expiry_status"] not in [
                    "fresh",
                    "no_expiry",
                ]:
                    continue
            items.append(item)

        # Group items by category for better organization
        categorized_items = {}
        for item in items:
            category = item["category"] or "Other"
            if category not in categorized_items:
                categorized_items[category] = []
            categorized_items[category].append(item)

        return jsonify(
            {
                "success": True,
                "items": items,
                "categorized_items": categorized_items,
                "total_items": len(items),
            }
        )

    except Exception as e:
        return jsonify(
            {"success": False, "message": f"Failed to get pantry items: {str(e)}"}
        )
    finally:
        cursor.close()


@api_bp.route("/pantry/items", methods=["POST"])
def add_pantry_item():
    """Add a new item to pantry manually"""
    if "user_ID" not in session:
        return jsonify({"success": False, "message": "Not authenticated"})

    data = request.get_json()
    user_ID = session["user_ID"]

    # Required fields
    item_name = data.get("item_name", "").strip()
    quantity = data.get("quantity", 1)
    unit = data.get("unit", "pcs")

    # Optional fields
    category = data.get("category", "Other")
    storage_type = data.get("storage_type", "pantry")
    expiration_date = data.get("expiration_date")  # YYYY-MM-DD format
    use_ai_prediction = data.get("ai_predict_expiry", False)  # Fixed parameter name
    notes = data.get("notes", "")

    if not item_name:
        return jsonify({"success": False, "message": "Item name is required"})

    try:
        quantity = float(quantity)
        if quantity <= 0:
            return jsonify({"success": False, "message": "Quantity must be positive"})
    except (ValueError, TypeError):
        return jsonify({"success": False, "message": "Invalid quantity"})

    db = get_db()
    cursor = db.cursor()

    try:
        # Handle AI expiration prediction
        is_ai_predicted = False
        if use_ai_prediction and not expiration_date:
            predicted_expiry = predict_expiration_date(item_name, storage_type)
            if predicted_expiry:
                expiration_date = predicted_expiry
                is_ai_predicted = True

        # Insert pantry item
        query = """
            INSERT INTO pantry_items (
                user_id, item_name, quantity, unit, category, storage_type,
                expiration_date, source_type, is_ai_predicted_expiry, notes
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        # Debug: print the values being inserted
        print(
            f"DEBUG: Inserting pantry item - user_ID: {user_ID}, item_name: {item_name}, quantity: {quantity}"
        )

        cursor.execute(
            query,
            (
                user_ID,
                item_name,
                quantity,
                unit,
                category,
                storage_type,
                expiration_date,
                "manual",
                is_ai_predicted,
                notes,
            ),
        )

        item_id = cursor.lastrowid
        db.commit()

        # Return the created item
        cursor.execute(
            "SELECT * FROM pantry_items WHERE pantry_item_id = %s", (item_id,)
        )
        new_item = cursor.fetchone()

        return jsonify(
            {
                "success": True,
                "item": new_item,
                "ai_predicted": is_ai_predicted,
                "message": "Item added successfully",
            }
        )

    except Exception as e:
        db.rollback()
        return jsonify(
            {"success": False, "message": f"Failed to add pantry item: {str(e)}"}
        )
    finally:
        cursor.close()


@api_bp.route("/pantry/transfer-from-trip", methods=["POST"])
def transfer_shopping_trip_to_pantry():
    """Transfer items from a completed shopping trip to pantry"""
    if "user_ID" not in session:
        return jsonify({"success": False, "message": "Not authenticated"})

    data = request.get_json()
    user_ID = session["user_ID"]
    cart_id = data.get("cart_id")
    items_data = data.get("items", [])  # List of items with pantry details

    if not cart_id:
        return jsonify({"success": False, "message": "Cart ID is required"})

    print(f"DEBUG: Transfer request - cart_id: {cart_id}, items: {len(items_data)}")

    db = get_db()
    cursor = db.cursor()

    try:
        # Verify cart belongs to user and is completed
        verify_query = """
            SELECT cart_ID FROM shopping_cart 
            WHERE cart_ID = %s AND user_ID = %s AND status = 'purchased'
        """
        cursor.execute(verify_query, (cart_id, user_ID))
        if not cursor.fetchone():
            return jsonify(
                {
                    "success": False,
                    "message": "Shopping trip not found or not completed",
                }
            )

        # Check if already transferred
        check_query = (
            "SELECT transfer_id FROM pantry_transfer_sessions WHERE cart_id = %s"
        )
        cursor.execute(check_query, (cart_id,))
        if cursor.fetchone():
            return jsonify(
                {
                    "success": False,
                    "message": "Items from this trip have already been transferred",
                }
            )

        # Create transfer session
        session_query = """
            INSERT INTO pantry_transfer_sessions (user_id, cart_id, items_transferred)
            VALUES (%s, %s, %s)
        """
        cursor.execute(session_query, (user_ID, cart_id, len(items_data)))
        transfer_id = cursor.lastrowid

        # Add items to pantry
        items_added = 0
        for item_data in items_data:
            item_id = item_data.get("item_id")

            # Get the original item details from cart_item table
            item_query = "SELECT * FROM cart_item WHERE item_ID = %s AND cart_ID = %s"
            cursor.execute(item_query, (item_id, cart_id))
            original_item = cursor.fetchone()

            if not original_item:
                print(f"DEBUG: Item {item_id} not found in cart {cart_id}")
                continue

            # Use original item name, but allow override of other properties
            item_name = original_item["item_name"]
            quantity = item_data.get("quantity", original_item.get("quantity", 1))
            unit = item_data.get("unit", original_item.get("unit", "pcs"))
            category = item_data.get("category", "Other")
            storage_type = item_data.get("storage_type", "pantry")
            expiration_date = item_data.get("expiration_date")
            use_ai_prediction = item_data.get(
                "ai_predict_expiry", False
            )  # Fixed parameter name
            notes = item_data.get("notes", "")

            print(
                f"DEBUG: Processing item - name: {item_name}, quantity: {quantity}, ai_predict: {use_ai_prediction}"
            )

            if not item_name:
                continue

            # Handle AI prediction if requested
            is_ai_predicted = False
            if use_ai_prediction and not expiration_date:
                predicted_expiry = predict_expiration_date(item_name, storage_type)
                if predicted_expiry:
                    expiration_date = predicted_expiry
                    is_ai_predicted = True

            # Insert pantry item
            insert_query = """
                INSERT INTO pantry_items (
                    user_id, item_name, quantity, unit, category, storage_type,
                    expiration_date, source_type, source_cart_id, is_ai_predicted_expiry, notes
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(
                insert_query,
                (
                    user_ID,
                    item_name,
                    quantity,
                    unit,
                    category,
                    storage_type,
                    expiration_date,
                    "shopping_trip",
                    cart_id,
                    is_ai_predicted,
                    notes,
                ),
            )
            items_added += 1
            print(f"DEBUG: Added item {item_name} to pantry")

        db.commit()

        return jsonify(
            {
                "success": True,
                "transfer_id": transfer_id,
                "items_added": items_added,
                "message": f"Successfully added {items_added} items to pantry",
            }
        )

    except Exception as e:
        db.rollback()
        print(f"DEBUG: Transfer error: {str(e)}")
        return jsonify(
            {"success": False, "message": f"Failed to transfer items: {str(e)}"}
        )
    finally:
        cursor.close()


def predict_expiration_date(item_name, storage_type):
    """Predict expiration date using AI or cached predictions"""
    db = get_db()
    cursor = db.cursor()

    try:
        # First check if we have a cached prediction
        cache_query = """
            SELECT predicted_days FROM expiry_predictions 
            WHERE item_name = %s AND storage_type = %s
        """
        cursor.execute(cache_query, (item_name.lower(), storage_type))
        cached = cursor.fetchone()

        if cached:
            # Update usage count
            cursor.execute(
                """
                UPDATE expiry_predictions 
                SET used_count = used_count + 1 
                WHERE item_name = %s AND storage_type = %s
            """,
                (item_name.lower(), storage_type),
            )

            # Calculate expiration date
            from datetime import datetime, timedelta

            expiry_date = datetime.now().date() + timedelta(
                days=cached["predicted_days"]
            )
            cursor.close()
            return expiry_date.strftime("%Y-%m-%d")

        # Use Gemini AI to predict expiration
        predicted_days = get_gemini_prediction(item_name, storage_type)

        if predicted_days:
            # Cache the prediction
            cursor.execute(
                """
                INSERT INTO expiry_predictions (item_name, storage_type, predicted_days)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                used_count = used_count + 1, 
                predicted_days = VALUES(predicted_days)
            """,
                (item_name.lower(), storage_type, predicted_days),
            )

            # Calculate expiration date
            from datetime import datetime, timedelta

            expiry_date = datetime.now().date() + timedelta(days=predicted_days)
            cursor.close()
            return expiry_date.strftime("%Y-%m-%d")

        cursor.close()
        return None

    except Exception as e:
        print(f"Error predicting expiration: {str(e)}")
        cursor.close()
        return None


def get_gemini_prediction(item_name, storage_type):
    """Use Gemini AI to predict expiration date based on item and storage type"""
    import os
    import google.generativeai as genai

    try:
        # Configure Gemini with API key from environment
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print(
                "WARNING: GEMINI_API_KEY not found in environment, falling back to simple prediction"
            )
            return get_simple_prediction(item_name, storage_type)

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash-latest")

        # Create a specific prompt for food expiration prediction
        prompt = f"""You are a food safety expert. I need to know how many days a food item will last.

Item: {item_name}
Storage: {storage_type} (pantry, fridge, or freezer)

Based on typical food safety guidelines, how many days will this item last from today if stored in the {storage_type}?

Important instructions:
- Only respond with a single number (the number of days)
- Consider typical shelf life for opened/unopened items
- Use conservative estimates for food safety
- For pantry items, assume they are in a cool, dry place
- For fridge items, assume proper refrigeration (35-40°F)
- For freezer items, assume proper freezing (0°F or below)

Examples:
- Fresh milk in fridge: 7
- Bread in pantry: 5
- Frozen chicken in freezer: 365
- Bananas in pantry: 5

Just respond with the number of days:"""

        # Generate prediction
        response = model.generate_content(prompt)
        prediction_text = response.text.strip()

        # Log the actual response for debugging
        print(
            f"DEBUG: Gemini raw response for {item_name} in {storage_type}: '{prediction_text}'"
        )

        # Extract number from response
        import re

        numbers = re.findall(r"\d+", prediction_text)
        if numbers:
            predicted_days = int(numbers[0])
            print(
                f"DEBUG: Extracted {predicted_days} days from response: '{prediction_text}'"
            )

            # Validate the prediction (sanity check)
            if 1 <= predicted_days <= 3650:  # Between 1 day and 10 years
                return predicted_days
            else:
                print(
                    f"WARNING: Gemini prediction {predicted_days} days seems unrealistic, falling back"
                )
                return get_simple_prediction(item_name, storage_type)
        else:
            print(f"WARNING: Could not parse Gemini response: {prediction_text}")
            return get_simple_prediction(item_name, storage_type)

    except Exception as e:
        print(
            f"ERROR: Gemini prediction failed: {str(e)}, falling back to simple prediction"
        )
        return get_simple_prediction(item_name, storage_type)


def get_simple_prediction(item_name, storage_type):
    """Simple heuristic-based expiration prediction"""
    item_lower = item_name.lower()

    # Storage-based multipliers
    storage_multiplier = {"freezer": 30, "fridge": 1, "pantry": 1}

    # Item category predictions (base days for fridge)
    if any(word in item_lower for word in ["milk", "dairy", "yogurt", "cheese"]):
        return 14 * storage_multiplier.get(storage_type, 1)
    elif any(
        word in item_lower for word in ["meat", "chicken", "beef", "pork", "fish"]
    ):
        return 3 * storage_multiplier.get(storage_type, 1)
    elif any(word in item_lower for word in ["bread", "bagel", "muffin"]):
        return 5 * storage_multiplier.get(storage_type, 1)
    elif any(
        word in item_lower
        for word in ["apple", "banana", "orange", "fruit", "vegetable"]
    ):
        return 7 * storage_multiplier.get(storage_type, 1)
    elif any(word in item_lower for word in ["rice", "pasta", "grain", "cereal"]):
        return 365 * storage_multiplier.get(storage_type, 1)
    elif any(word in item_lower for word in ["canned", "can", "jar"]):
        return 730 * storage_multiplier.get(storage_type, 1)
    else:
        # Default prediction
        base_days = (
            30 if storage_type == "pantry" else 14 if storage_type == "fridge" else 90
        )
        return base_days

    return None


@api_bp.route("/pantry/items/<int:item_id>", methods=["GET"])
def get_pantry_item(item_id):
    """Get a single pantry item by ID"""
    if "user_ID" not in session:
        return jsonify({"success": False, "message": "Not authenticated"})

    user_id = session["user_ID"]

    try:
        db = get_db()
        cursor = db.cursor()

        # Get the specific item
        query = "SELECT * FROM pantry_items WHERE pantry_item_id = %s AND user_id = %s"
        cursor.execute(query, (item_id, user_id))
        item = cursor.fetchone()

        if not item:
            return jsonify(
                {"success": False, "message": "Item not found or access denied"}
            )

        cursor.close()
        return jsonify({"success": True, "item": item})

    except Exception as e:
        return jsonify({"success": False, "message": f"Database error: {str(e)}"})
    finally:
        if cursor:
            cursor.close()


@api_bp.route("/pantry/items/<int:item_id>", methods=["PUT"])
def update_pantry_item(item_id):
    """Update a pantry item"""
    if "user_ID" not in session:
        return jsonify({"success": False, "message": "Not authenticated"})

    user_id = session["user_ID"]
    data = request.get_json()

    # Required fields
    item_name = data.get("item_name", "").strip()
    quantity = data.get("quantity", 1)
    unit = data.get("unit", "pcs")

    # Optional fields
    category = data.get("category", "Other")
    storage_type = data.get("storage_type", "pantry")
    expiration_date = data.get("expiration_date")
    use_ai_prediction = data.get("ai_predict_expiry", False)
    notes = data.get("notes", "")

    if not item_name:
        return jsonify({"success": False, "message": "Item name is required"})

    try:
        quantity = float(quantity)
        if quantity <= 0:
            return jsonify({"success": False, "message": "Quantity must be positive"})
    except (ValueError, TypeError):
        return jsonify({"success": False, "message": "Invalid quantity"})

    try:
        db = get_db()
        cursor = db.cursor()

        # Verify the item belongs to the user
        verify_query = "SELECT pantry_item_id FROM pantry_items WHERE pantry_item_id = %s AND user_id = %s"
        cursor.execute(verify_query, (item_id, user_id))
        if not cursor.fetchone():
            return jsonify(
                {"success": False, "message": "Item not found or access denied"}
            )

        # Handle AI prediction if requested
        is_ai_predicted = False
        if use_ai_prediction and not expiration_date:
            predicted_expiry = predict_expiration_date(item_name, storage_type)
            if predicted_expiry:
                expiration_date = predicted_expiry
                is_ai_predicted = True

        # Update the item
        update_query = """
            UPDATE pantry_items SET 
                item_name = %s, quantity = %s, unit = %s, category = %s, 
                storage_type = %s, expiration_date = %s, is_ai_predicted_expiry = %s, notes = %s,
                date_updated = CURRENT_TIMESTAMP
            WHERE pantry_item_id = %s AND user_id = %s
        """
        cursor.execute(
            update_query,
            (
                item_name,
                quantity,
                unit,
                category,
                storage_type,
                expiration_date,
                is_ai_predicted,
                notes,
                item_id,
                user_id,
            ),
        )

        db.commit()

        # Return the updated item
        cursor.execute(
            "SELECT * FROM pantry_items WHERE pantry_item_id = %s", (item_id,)
        )
        updated_item = cursor.fetchone()

        return jsonify(
            {
                "success": True,
                "item": updated_item,
                "ai_predicted": is_ai_predicted,
                "message": "Item updated successfully",
            }
        )

    except Exception as e:
        db.rollback()
        return jsonify(
            {"success": False, "message": f"Failed to update pantry item: {str(e)}"}
        )
    finally:
        cursor.close()


@api_bp.route("/pantry/items/<int:item_id>", methods=["DELETE"])
def delete_pantry_item(item_id):
    """Delete a pantry item"""
    if "user_ID" not in session:
        return jsonify({"success": False, "message": "Not authenticated"})

    user_id = session["user_ID"]

    try:
        db = get_db()
        cursor = db.cursor()

        # Verify the item belongs to the user before deleting
        query = "SELECT pantry_item_id FROM pantry_items WHERE pantry_item_id = %s AND user_id = %s"
        cursor.execute(query, (item_id, user_id))
        item = cursor.fetchone()

        if not item:
            cursor.close()
            return jsonify(
                {"success": False, "message": "Item not found or access denied"}
            )

        # Delete the item
        delete_query = (
            "DELETE FROM pantry_items WHERE pantry_item_id = %s AND user_id = %s"
        )
        cursor.execute(delete_query, (item_id, user_id))
        db.commit()
        cursor.close()

        return jsonify({"success": True, "message": "Item deleted successfully"})

    except Exception as e:
        return jsonify({"success": False, "message": f"Database error: {str(e)}"})


@api_bp.route("/pantry/test", methods=["GET"])
def test_pantry():
    """Test endpoint to check pantry functionality"""
    if "user_ID" not in session:
        return jsonify({"success": False, "message": "Not authenticated"})

    user_ID = session["user_ID"]
    db = get_db()
    cursor = db.cursor()

    try:
        # Test basic connection and table access
        cursor.execute(
            "SELECT COUNT(*) as count FROM pantry_items WHERE user_id = %s", (user_ID,)
        )
        result = cursor.fetchone()

        return jsonify(
            {
                "success": True,
                "message": f'Pantry test successful. User {user_ID} has {result["count"]} items.',
                "user_id": user_ID,
            }
        )

    except Exception as e:
        return jsonify({"success": False, "message": f"Pantry test failed: {str(e)}"})
    finally:
        cursor.close()


@api_bp.route("/pantry/test-gemini", methods=["GET"])
def test_gemini():
    """Test Gemini AI integration"""
    item_name = request.args.get("item_name", "banana")
    storage_type = request.args.get("storage_type", "pantry")

    try:
        predicted_days = get_gemini_prediction(item_name, storage_type)
        return jsonify(
            {
                "success": True,
                "item_name": item_name,
                "storage_type": storage_type,
                "predicted_days": predicted_days,
                "message": f"Gemini predicted {predicted_days} days for {item_name} in {storage_type}",
            }
        )
    except Exception as e:
        return jsonify({"success": False, "message": f"Gemini test failed: {str(e)}"})


# =============================================================================
# MEAL PLAN GENERATOR API ENDPOINTS
# =============================================================================


@api_bp.route("/generate-meal-plan", methods=["POST"])
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


@api_bp.route("/meal-plans", methods=["GET"])
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


@api_bp.route("/meal-plans/<int:plan_id>", methods=["GET"])
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
