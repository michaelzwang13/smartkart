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
    ins = 'INSERT INTO item (cart_ID, user_ID, quantity, item_name, price, upc, item_lifetime, image_url) VALUES(%s, %s, %s, %s, %s, %s, %s, %s)'
    cursor.execute(ins, (session['cart_ID'], session['user_ID'], data['quantity'], data['itemName'], data['price'], data['upc'], 7, data['imageUrl']))
    db.commit()
    
    query = 'SELECT * FROM item WHERE cart_ID = %s'
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
        query = 'SELECT item_ID FROM item WHERE cart_ID = %s ORDER BY item_ID DESC LIMIT 1'
        cursor.execute(query, (session['cart_ID'],))
        last_item = cursor.fetchone()
        
        if last_item:
            # Delete the item
            delete_query = 'DELETE FROM item WHERE item_ID = %s'
            cursor.execute(delete_query, (last_item['item_ID'],))
            db.commit()
            
            # Return updated cart items
            query = 'SELECT * FROM item WHERE cart_ID = %s'
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
        verify_query = 'SELECT item_ID FROM item WHERE item_ID = %s AND cart_ID = %s AND user_ID = %s'
        cursor.execute(verify_query, (item_id, session['cart_ID'], session['user_ID']))
        if not cursor.fetchone():
            return jsonify({"error": "Item not found"}), 404
        
        # Update the quantity
        update_query = 'UPDATE item SET quantity = %s WHERE item_ID = %s'
        cursor.execute(update_query, (quantity, item_id))
        db.commit()
        
        # Return updated cart items
        query = 'SELECT item_ID, item_name, price, quantity, image_url FROM item WHERE cart_ID = %s'
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
        verify_query = 'SELECT item_ID FROM item WHERE item_ID = %s AND cart_ID = %s AND user_ID = %s'
        cursor.execute(verify_query, (item_id, session['cart_ID'], session['user_ID']))
        if not cursor.fetchone():
            return jsonify({"error": "Item not found"}), 404
        
        # Delete the item
        delete_query = 'DELETE FROM item WHERE item_ID = %s'
        cursor.execute(delete_query, (item_id,))
        db.commit()
        
        # Return updated cart items
        query = 'SELECT item_ID, item_name, price, quantity, image_url FROM item WHERE cart_ID = %s'
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
