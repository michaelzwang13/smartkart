from flask import Blueprint, request, jsonify, session, current_app
import requests
from src.database import get_db
from src import helper

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/shopping-trip/add-item', methods=['POST'])
def add_item():
    if 'user_ID' not in session or 'cart_ID' not in session:
        return jsonify({"error": "User or cart not in session"}), 400

    data = request.get_json()
    required_fields = ['upc', 'price', 'quantity', 'itemName', 'imageUrl']
    if not data or not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    db = get_db()
    cursor = db.cursor()
    ins = 'INSERT INTO cart_item (cart_ID, user_ID, quantity, item_name, price, upc, item_lifetime, image_url) VALUES(%s, %s, %s, %s, %s, %s, %s, %s)'
    cursor.execute(ins, (session['cart_ID'], session['user_ID'], data['quantity'], data['itemName'], data['price'], data['upc'], 7, data['imageUrl']))
    db.commit()
    
    query = 'SELECT * FROM cart_item WHERE cart_ID = %s'
    cursor.execute(query, (session['cart_ID'],))
    items = cursor.fetchall()
    cursor.close()

    return jsonify({"status": "success", "items": items}), 200

@api_bp.route('/shopping-trip/remove-last-item', methods=['POST'])
def remove_last_item():
    """Remove the most recently added item from the cart"""
    if 'user_ID' not in session or 'cart_ID' not in session:
        return jsonify({"error": "User or cart not in session"}), 400

    db = get_db()
    cursor = db.cursor()
    
    try:
        # Get the most recently added item
        query = 'SELECT item_ID FROM cart_item WHERE cart_ID = %s ORDER BY item_ID DESC LIMIT 1'
        cursor.execute(query, (session['cart_ID'],))
        last_item = cursor.fetchone()
        
        if last_item:
            # Delete the item
            delete_query = 'DELETE FROM cart_item WHERE item_ID = %s'
            cursor.execute(delete_query, (last_item['item_ID'],))
            db.commit()
            
            # Return updated cart items
            query = 'SELECT * FROM cart_item WHERE cart_ID = %s'
            cursor.execute(query, (session['cart_ID'],))
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

@api_bp.route('/shopping-trip/update-item', methods=['POST'])
def update_item_quantity():
    """Update the quantity of an item in the cart"""
    if 'user_ID' not in session or 'cart_ID' not in session:
        return jsonify({"error": "User or cart not in session"}), 400

    data = request.get_json()
    if not data or 'item_id' not in data or 'quantity' not in data:
        return jsonify({"error": "Missing item_id or quantity"}), 400

    item_id = data['item_id']
    quantity = data['quantity']
    
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
        verify_query = 'SELECT item_ID FROM cart_item WHERE item_ID = %s AND cart_ID = %s AND user_ID = %s'
        cursor.execute(verify_query, (item_id, session['cart_ID'], session['user_ID']))
        if not cursor.fetchone():
            return jsonify({"error": "Item not found"}), 404
        
        # Update the quantity
        update_query = 'UPDATE cart_item SET quantity = %s WHERE item_ID = %s'
        cursor.execute(update_query, (quantity, item_id))
        db.commit()
        
        # Return updated cart items
        query = 'SELECT item_ID, item_name, price, quantity, image_url FROM cart_item WHERE cart_ID = %s'
        cursor.execute(query, (session['cart_ID'],))
        items = cursor.fetchall()
        
        # Calculate totals
        total_items = sum(item['quantity'] for item in items)
        total_spent = sum(item['price'] * item['quantity'] for item in items)
        allocated_budget = 1000
        remaining = allocated_budget - total_spent
        
        cursor.close()
        
        return jsonify({
            "status": "success",
            "items": items,
            "total_items": total_items,
            "total_spent": total_spent,
            "allocated_budget": allocated_budget,
            "remaining": remaining
        }), 200
        
    except Exception as e:
        db.rollback()
        return jsonify({"error": f"Failed to update item: {str(e)}"}), 500
    finally:
        cursor.close()

@api_bp.route('/shopping-trip/delete-item', methods=['POST'])
def delete_item():
    """Delete a specific item from the cart"""
    if 'user_ID' not in session or 'cart_ID' not in session:
        return jsonify({"error": "User or cart not in session"}), 400

    data = request.get_json()
    if not data or 'item_id' not in data:
        return jsonify({"error": "Missing item_id"}), 400

    item_id = data['item_id']

    db = get_db()
    cursor = db.cursor()
    
    try:
        # Verify the item belongs to the current user's cart
        verify_query = 'SELECT item_ID FROM cart_item WHERE item_ID = %s AND cart_ID = %s AND user_ID = %s'
        cursor.execute(verify_query, (item_id, session['cart_ID'], session['user_ID']))
        if not cursor.fetchone():
            return jsonify({"error": "Item not found"}), 404
        
        # Delete the item
        delete_query = 'DELETE FROM cart_item WHERE item_ID = %s'
        cursor.execute(delete_query, (item_id,))
        db.commit()
        
        # Return updated cart items
        query = 'SELECT item_ID, item_name, price, quantity, image_url FROM cart_item WHERE cart_ID = %s'
        cursor.execute(query, (session['cart_ID'],))
        items = cursor.fetchall()
        
        # Calculate totals
        total_items = sum(item['quantity'] for item in items)
        total_spent = sum(item['price'] * item['quantity'] for item in items)
        allocated_budget = 1000
        remaining = allocated_budget - total_spent
        
        cursor.close()
        
        return jsonify({
            "status": "success",
            "items": items,
            "total_items": total_items,
            "total_spent": total_spent,
            "allocated_budget": allocated_budget,
            "remaining": remaining
        }), 200
        
    except Exception as e:
        db.rollback()
        return jsonify({"error": f"Failed to delete item: {str(e)}"}), 500
    finally:
        cursor.close()
  
@api_bp.route('/shopping-trip/items', methods=['GET'])
def get_cart_items():
    if "cart_ID" not in session or not session['cart_ID']:
        return jsonify({"items": [], "total_items": 0, "total_spent": 0, "allocated_budget": 1000, "remaining": 1000})
    
    db = get_db()
    cursor = db.cursor()
    
    # Get items
    query = 'SELECT item_ID, item_name, price, quantity, image_url FROM item WHERE cart_ID = %s'
    cursor.execute(query, (session['cart_ID'],))
    items = cursor.fetchall()
    
    # Calculate totals
    total_items = sum(item['quantity'] for item in items)
    total_spent = sum(item['price'] * item['quantity'] for item in items)
    allocated_budget = 1000  # You can make this dynamic later
    remaining = allocated_budget - total_spent
    
    cursor.close()
    
    return jsonify({
        "items": items,
        "total_items": total_items,
        "total_spent": total_spent,
        "allocated_budget": allocated_budget,
        "remaining": remaining
    })

@api_bp.route('/searchitem', methods=['GET'])
def searchitem():
    api_id = current_app.config.get('NUTRITIONIX_API_ID')
    api_key = current_app.config.get('NUTRITIONIX_API_KEY')

    if not api_id or not api_key or api_id == "YOUR_API_ID_HERE":
        return jsonify({'error': 'Nutritionix API keys are not configured'}), 500

    upc = request.args.get('upc')
    if not upc:
        return jsonify({'error': 'UPC parameter is required'}), 400

    url = f'https://trackapi.nutritionix.com/v2/search/item?upc={upc}'
    headers = {'x-app-id': api_id, 'x-app-key': api_key}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/predict')
def predict():
    carbs = request.args.get('carbs', 0)
    sugar = request.args.get('sugar', 0)
    sodium = request.args.get('sodium', 0)
    fat = request.args.get('fat', 0)

    if helper.model is None:
        return jsonify({'error': 'Model not loaded'}), 500
    
    prediction = helper.predict_impulsive_purchase(carbs, sugar, sodium, fat).item()
    return jsonify({'prediction': int(prediction)})

@api_bp.route('/learn')
def learn():
    carbs = request.args.get('carbs', 0)
    sugar = request.args.get('sugar', 0)
    sodium = request.args.get('sodium', 0)
    fat = request.args.get('fat', 0)

    if helper.model is None:
        return jsonify({'error': 'Model not loaded'}), 500
    
    helper.model_learn(carbs, sugar, sodium, fat)
    return jsonify({'status': 'learned'}), 200

# Budget API Routes

@api_bp.route('/budget/overview', methods=['GET'])
def get_budget_overview():
    """Get budget overview with spending data"""
    if 'user_ID' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user_ID = session['user_ID']
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
            budget_period = 'monthly'
        else:
            monthly_budget = float(budget_settings['monthly_budget'])
            alert_threshold = float(budget_settings['alert_threshold'])
            budget_period = budget_settings['budget_period']
        
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
            cursor.execute(insert_budget, (user_ID, monthly_budget, alert_threshold/100))
            db.commit()
            
            allocated_amount = monthly_budget
            total_spent = 0
            remaining = monthly_budget
        else:
            allocated_amount = float(current_budget['allocated_amount'])
            total_spent = float(current_budget['total_spent'] or 0)
            remaining = float(current_budget['remaining_amount'] or 0)
        
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
        total_trips = trips_result['total_trips'] or 0
        
        # Calculate daily average (based on current day of month)
        from datetime import datetime
        current_day = datetime.now().day
        daily_avg = total_spent / current_day if current_day > 0 else 0
        
        cursor.close()
        
        return jsonify({
            'monthly_budget': allocated_amount,
            'total_spent': total_spent,
            'remaining': remaining,
            'daily_average': daily_avg,
            'total_trips': total_trips,
            'alert_threshold': alert_threshold,
            'budget_period': budget_period
        })
        
    except Exception as e:
        db.rollback()
        return jsonify({'error': f'Failed to get budget overview: {str(e)}'}), 500
    finally:
        cursor.close()

@api_bp.route('/budget/spending-trends', methods=['GET'])
def get_spending_trends():
    """Get spending trends for charts"""
    if 'user_ID' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user_ID = session['user_ID']
    period = request.args.get('period', '7d')  # 7d, 1m, 3m, 1y
    
    db = get_db()
    cursor = db.cursor()
    
    try:
        if period == '7d':
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
        elif period == '1m':
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
        elif period == '3m':
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
            date_key = trend['date'].strftime('%Y-%m-%d')
            trend_data[date_key] = float(trend['amount'])
            print(f"DEBUG: Added to trend_data: {date_key} = {trend_data[date_key]}")
        
        # Generate complete date range and labels based on period
        formatted_trends = []
        if period == '7d':
            # Last 7 days - daily buckets (7 bars)
            for i in range(7):
                date = (datetime.now() - timedelta(days=6-i)).date()
                date_str = date.strftime('%Y-%m-%d')
                label = date.strftime('%b %d')  # "Jul 14", "Jul 15"
                formatted_trends.append({
                    'date': date_str,
                    'label': label,
                    'amount': trend_data.get(date_str, 0.0)
                })
        elif period == '1m':
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
                    day_str = day.strftime('%Y-%m-%d')
                    week_amount += trend_data.get(day_str, 0.0)
                
                week_start_str = week_start.strftime('%Y-%m-%d')
                label = f"Week of {week_start.strftime('%b %d')}"
                formatted_trends.append({
                    'date': week_start_str,
                    'label': label,
                    'amount': week_amount
                })
        elif period == '3m':
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
                    day_str = day.strftime('%Y-%m-%d')
                    week_amount += trend_data.get(day_str, 0.0)
                
                week_start_str = week_start.strftime('%Y-%m-%d')
                label = f"Week of {week_start.strftime('%b %d')}"
                formatted_trends.append({
                    'date': week_start_str,
                    'label': label,
                    'amount': week_amount
                })
        else:  # 1y - Last 12 months - monthly buckets (12 bars)
            for i in range(12):
                # Calculate month (11 months ago to current month)
                current_month = datetime.now().replace(day=1)
                months_back = 11 - i
                
                target_month = current_month
                for _ in range(months_back):
                    if target_month.month == 1:
                        target_month = target_month.replace(year=target_month.year-1, month=12)
                    else:
                        target_month = target_month.replace(month=target_month.month-1)
                
                # Sum all data for this month
                month_amount = 0.0
                # Check all possible days in the month
                days_in_month = calendar.monthrange(target_month.year, target_month.month)[1]
                for day in range(1, days_in_month + 1):
                    day_date = target_month.replace(day=day)
                    day_str = day_date.strftime('%Y-%m-%d')
                    month_amount += trend_data.get(day_str, 0.0)
                
                date_str = target_month.strftime('%Y-%m-%d')
                label = target_month.strftime('%b')
                formatted_trends.append({
                    'date': date_str,
                    'label': label,
                    'amount': month_amount
                })
        
        cursor.close()
        
        print(f"DEBUG: Final formatted_trends: {formatted_trends}")
        
        return jsonify({
            'trends': formatted_trends,
            'period': period
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get spending trends: {str(e)}'}), 500
    finally:
        cursor.close()

@api_bp.route('/budget/spending-details', methods=['GET'])
def get_spending_details():
    """Get detailed shopping items for a specific time period"""
    if 'user_ID' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user_ID = session['user_ID']
    period = request.args.get('period', '7d')
    date = request.args.get('date')  # Specific date for the bar clicked
    
    if not date:
        return jsonify({'error': 'Date parameter required'}), 400
    
    db = get_db()
    cursor = db.cursor()
    
    try:
        from datetime import datetime, timedelta
        
        # Parse the date
        try:
            target_date = datetime.strptime(date, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid date format'}), 400
        
        # Build query based on period type to get items for the specific time range
        if period == '7d':
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
        elif period == '1m' or period == '3m':
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
                month_end = target_date.replace(year=target_date.year+1, month=1, day=1) - timedelta(days=1)
            else:
                month_end = target_date.replace(month=target_date.month+1, day=1) - timedelta(days=1)
            
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
            cart_id = item['cart_ID']
            item_total = float(item['item_total'])
            total_amount += item_total
            
            if cart_id not in trips:
                trips[cart_id] = {
                    'cart_id': cart_id,
                    'store_name': item['store_name'],
                    'date': item['created_at'].strftime('%Y-%m-%d'),
                    'datetime': item['created_at'].strftime('%b %d, %Y at %I:%M %p'),
                    'items': [],
                    'trip_total': 0
                }
            
            trips[cart_id]['items'].append({
                'name': item['item_name'],
                'quantity': item['quantity'],
                'price': float(item['price']),
                'total': item_total,
                'image_url': item['image_url']
            })
            trips[cart_id]['trip_total'] += item_total
        
        # Convert to list and sort by date
        trips_list = list(trips.values())
        trips_list.sort(key=lambda x: x['date'], reverse=True)
        
        cursor.close()
        
        # Determine period label
        period_labels = {
            '7d': target_date.strftime('%B %d, %Y'),
            '1m': f"Week of {target_date.strftime('%B %d, %Y')}",
            '3m': f"Week of {target_date.strftime('%B %d, %Y')}",
            '1y': target_date.strftime('%B %Y')
        }
        
        return jsonify({
            'period_label': period_labels.get(period, target_date.strftime('%B %d, %Y')),
            'total_amount': round(total_amount, 2),
            'total_trips': len(trips_list),
            'total_items': sum(len(trip['items']) for trip in trips_list),
            'trips': trips_list
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get spending details: {str(e)}'}), 500
    finally:
        cursor.close()

@api_bp.route('/budget/categories', methods=['GET'])
def get_category_breakdown():
    """Get spending breakdown by category"""
    if 'user_ID' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user_ID = session['user_ID']
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
            'Fresh Produce': {'amount': 0, 'items': []},
            'Meat & Seafood': {'amount': 0, 'items': []},
            'Bakery & Dairy': {'amount': 0, 'items': []},
            'Pantry Items': {'amount': 0, 'items': []},
            'Frozen Foods': {'amount': 0, 'items': []},
            'Beverages': {'amount': 0, 'items': []}
        }
        
        # Categorization keywords
        category_keywords = {
            'Fresh Produce': ['apple', 'banana', 'orange', 'lettuce', 'tomato', 'potato', 'carrot', 'onion', 'fruit', 'vegetable'],
            'Meat & Seafood': ['chicken', 'beef', 'pork', 'fish', 'salmon', 'turkey', 'ham', 'meat'],
            'Bakery & Dairy': ['milk', 'cheese', 'yogurt', 'butter', 'bread', 'bagel', 'muffin', 'dairy'],
            'Frozen Foods': ['frozen', 'ice cream', 'pizza'],
            'Beverages': ['juice', 'soda', 'water', 'coffee', 'tea', 'beer', 'wine', 'drink']
        }
        
        for item in items:
            item_name = item['item_name'].lower()
            amount = float(item['amount'])
            
            categorized = False
            for category, keywords in category_keywords.items():
                if any(keyword in item_name for keyword in keywords):
                    categories[category]['amount'] += amount
                    categories[category]['items'].append(item['item_name'])
                    categorized = True
                    break
            
            if not categorized:
                categories['Pantry Items']['amount'] += amount
                categories['Pantry Items']['items'].append(item['item_name'])
        
        cursor.close()
        
        return jsonify({'categories': categories})
        
    except Exception as e:
        return jsonify({'error': f'Failed to get category breakdown: {str(e)}'}), 500
    finally:
        cursor.close()

@api_bp.route('/budget/settings', methods=['POST'])
def update_budget_settings():
    """Update user's budget settings"""
    if 'user_ID' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user_ID = session['user_ID']
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    monthly_budget = float(data.get('monthly_budget', 1000))
    budget_period = data.get('budget_period', 'monthly')
    alert_threshold = float(data.get('alert_threshold', 80))
    category_limits = data.get('category_limits', 'enabled')
    
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
            cursor.execute(update_query, (monthly_budget, budget_period, alert_threshold, 
                                        category_limits == 'enabled', user_ID))
        else:
            # Create new settings
            insert_query = """
                INSERT INTO user_budget_settings 
                (user_id, monthly_budget, budget_period, alert_threshold, category_limits_enabled)
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(insert_query, (user_ID, monthly_budget, budget_period, 
                                        alert_threshold, category_limits == 'enabled'))
        
        # Update current month's budget allocation if it exists
        update_budget_query = """
            UPDATE budget 
            SET allocated_amount = %s, alert_threshold = %s, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = %s 
              AND MONTH(created_at) = MONTH(CURRENT_DATE())
              AND YEAR(created_at) = YEAR(CURRENT_DATE())
              AND list_id IS NULL
        """
        cursor.execute(update_budget_query, (monthly_budget, alert_threshold/100, user_ID))
        
        db.commit()
        cursor.close()
        
        return jsonify({'status': 'success', 'message': 'Budget settings updated successfully'})
        
    except Exception as e:
        db.rollback()
        return jsonify({'error': f'Failed to update budget settings: {str(e)}'}), 500
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
            cursor.execute(update_query, (amount_spent, budget_entry['budget_id']))
        else:
            # Get user's budget settings to create new entry
            settings_query = "SELECT monthly_budget, alert_threshold FROM user_budget_settings WHERE user_id = %s"
            cursor.execute(settings_query, (user_id,))
            settings = cursor.fetchone()
            
            monthly_budget = settings['monthly_budget'] if settings else 1000
            alert_threshold = settings['alert_threshold'] if settings else 80
            
            # Create new budget entry
            insert_query = """
                INSERT INTO budget (user_id, allocated_amount, total_spent, alert_threshold)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(insert_query, (user_id, monthly_budget, amount_spent, alert_threshold/100))
        
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

@api_bp.route('/shopping-lists', methods=['GET'])
def get_shopping_lists():
    """Get all shopping lists for the current user"""
    if 'user_ID' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user_ID = session['user_ID']
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
            list_id = shopping_list['list_id']
            items_query = """
                SELECT item_id, item_name, quantity, notes, is_completed, created_at, updated_at
                FROM shopping_list_items 
                WHERE list_id = %s
                ORDER BY created_at ASC
            """
            cursor.execute(items_query, (list_id,))
            items = cursor.fetchall()
            
            # Convert items to list format expected by frontend
            shopping_list['items'] = [
                {
                    'id': item['item_id'],
                    'name': item['item_name'],
                    'quantity': item['quantity'],
                    'notes': item['notes'],
                    'is_completed': bool(item['is_completed']),
                    'created_at': item['created_at'].isoformat() if item['created_at'] else None,
                    'updated_at': item['updated_at'].isoformat() if item['updated_at'] else None
                }
                for item in items
            ]
            
            # Convert list timestamps to strings
            shopping_list['id'] = shopping_list['list_id']
            shopping_list['name'] = shopping_list['list_name']
            shopping_list['created_at'] = shopping_list['created_at'].isoformat() if shopping_list['created_at'] else None
            shopping_list['updated_at'] = shopping_list['updated_at'].isoformat() if shopping_list['updated_at'] else None
        
        return jsonify({'lists': lists})
        
    except Exception as e:
        return jsonify({'error': f'Failed to fetch shopping lists: {str(e)}'}), 500
    finally:
        cursor.close()

@api_bp.route('/shopping-lists', methods=['POST'])
def create_shopping_list():
    """Create a new shopping list"""
    if 'user_ID' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.get_json()
    user_ID = session['user_ID']
    list_name = data.get('name', '').strip()
    description = data.get('description', '').strip()
    
    if not list_name:
        return jsonify({'error': 'List name is required'}), 400
    
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
            'id': list_id,
            'name': list_name,
            'description': description,
            'items': [],
            'created_at': None,  # Will be set by database
            'updated_at': None
        }
        
        return jsonify({'list': new_list}), 201
        
    except Exception as e:
        db.rollback()
        return jsonify({'error': f'Failed to create shopping list: {str(e)}'}), 500
    finally:
        cursor.close()

@api_bp.route('/shopping-lists/<int:list_id>', methods=['PATCH'])
def update_shopping_list(list_id):
    """Update a shopping list"""
    if 'user_ID' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.get_json()
    user_ID = session['user_ID']
    
    db = get_db()
    cursor = db.cursor()
    
    try:
        # Verify the list belongs to the user
        verify_query = "SELECT list_id FROM shopping_lists WHERE list_id = %s AND user_id = %s"
        cursor.execute(verify_query, (list_id, user_ID))
        if not cursor.fetchone():
            return jsonify({'error': 'Shopping list not found'}), 404
        
        # Update the list
        update_fields = []
        update_values = []
        
        if 'name' in data:
            update_fields.append('list_name = %s')
            update_values.append(data['name'].strip())
        
        if 'description' in data:
            update_fields.append('description = %s')
            update_values.append(data['description'].strip())
        
        if update_fields:
            update_values.append(list_id)
            query = f"UPDATE shopping_lists SET {', '.join(update_fields)} WHERE list_id = %s"
            cursor.execute(query, update_values)
            db.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        db.rollback()
        return jsonify({'error': f'Failed to update shopping list: {str(e)}'}), 500
    finally:
        cursor.close()

@api_bp.route('/shopping-lists/<int:list_id>', methods=['DELETE'])
def delete_shopping_list(list_id):
    """Delete a shopping list"""
    if 'user_ID' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user_ID = session['user_ID']
    db = get_db()
    cursor = db.cursor()
    
    try:
        # Verify the list belongs to the user
        verify_query = "SELECT list_id FROM shopping_lists WHERE list_id = %s AND user_id = %s"
        cursor.execute(verify_query, (list_id, user_ID))
        if not cursor.fetchone():
            return jsonify({'error': 'Shopping list not found'}), 404
        
        # Set is_active to FALSE instead of deleting (soft delete)
        query = "UPDATE shopping_lists SET is_active = FALSE WHERE list_id = %s"
        cursor.execute(query, (list_id,))
        db.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        db.rollback()
        return jsonify({'error': f'Failed to delete shopping list: {str(e)}'}), 500
    finally:
        cursor.close()

@api_bp.route('/shopping-lists/<int:list_id>/items', methods=['POST'])
def add_item_to_list(list_id):
    """Add an item to a shopping list"""
    if 'user_ID' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.get_json()
    user_ID = session['user_ID']
    item_name = data.get('name', '').strip()
    quantity = data.get('quantity', 1)
    notes = data.get('notes', '').strip()
    
    if not item_name:
        return jsonify({'error': 'Item name is required'}), 400
    
    try:
        quantity = int(quantity)
        if quantity < 1:
            quantity = 1
    except (ValueError, TypeError):
        quantity = 1
    
    db = get_db()
    cursor = db.cursor()
    
    try:
        # Verify the list belongs to the user
        verify_query = "SELECT list_id FROM shopping_lists WHERE list_id = %s AND user_id = %s AND is_active = TRUE"
        cursor.execute(verify_query, (list_id, user_ID))
        if not cursor.fetchone():
            return jsonify({'error': 'Shopping list not found'}), 404
        
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
            'id': item_id,
            'name': item_name,
            'quantity': quantity,
            'notes': notes,
            'is_completed': False
        }
        
        return jsonify({'item': new_item}), 201
        
    except Exception as e:
        db.rollback()
        return jsonify({'error': f'Failed to add item: {str(e)}'}), 500
    finally:
        cursor.close()

@api_bp.route('/shopping-lists/<int:list_id>/items/<int:item_id>/toggle', methods=['PATCH'])
def toggle_item_completion(list_id, item_id):
    """Toggle item completion status"""
    if 'user_ID' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user_ID = session['user_ID']
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
            return jsonify({'error': 'Item not found'}), 404
        
        # Toggle completion status
        new_status = not bool(result['is_completed'])
        query = "UPDATE shopping_list_items SET is_completed = %s WHERE item_id = %s"
        cursor.execute(query, (new_status, item_id))
        db.commit()
        
        return jsonify({'success': True, 'is_completed': new_status})
        
    except Exception as e:
        db.rollback()
        return jsonify({'error': f'Failed to toggle item: {str(e)}'}), 500
    finally:
        cursor.close()

@api_bp.route('/shopping-lists/<int:list_id>/items/<int:item_id>', methods=['DELETE'])
def delete_item_from_list(list_id, item_id):
    """Delete an item from a shopping list"""
    if 'user_ID' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user_ID = session['user_ID']
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
            return jsonify({'error': 'Item not found'}), 404
        
        # Delete the item
        query = "DELETE FROM shopping_list_items WHERE item_id = %s"
        cursor.execute(query, (item_id,))
        db.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        db.rollback()
        return jsonify({'error': f'Failed to delete item: {str(e)}'}), 500
    finally:
        cursor.close()
