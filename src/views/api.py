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
  
@api_bp.route('/shopping-trip/items', methods=['GET'])
def get_cart_items():
    if "cart_ID" not in session or not session['cart_ID']:
        return jsonify({"items": []})
    
    db = get_db()
    cursor = db.cursor()
    query = 'SELECT item_name, price, quantity, image_url FROM item WHERE cart_ID = %s'
    cursor.execute(query, (session['cart_ID'],))
    items = cursor.fetchall()
    cursor.close()
    
    return jsonify({"items": items})

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
