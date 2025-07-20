#Import Flask Library
from flask import Flask, render_template, request, session, url_for, redirect, jsonify, flash
import requests
# import pyodbc
import pymysql.cursors
import hashlib
import helper
import os

#Initialize the app from Flask
app = Flask(__name__)

#Configure MySQL
conn = pymysql.connect(host='localhost',
											 port= 8889,
                       user='root',
                       password='root',
                       db='hacknyu25',
                       charset='utf8mb4',
                       cursorclass=pymysql.cursors.DictCursor)

# conn = pymysql.connect(host='localhost',
# 						port= 3306,
#                          user='willy',
#                          password='willy',
#                          database='hacknyu25',
#                          charset='utf8mb4',
#                          cursorclass=pymysql.cursors.DictCursor)

# server = 'smart-kart-server.database.windows.net'
# database = 'smart-kart-db'
# username = os.environ['AZURE_UID']
# password = os.environ['AZURE_PWD']
# driver = '{ODBC DRIVER 18 for SQL Server}'

# conn = pyodbc.connect(f'DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}')

#Define a route to hello function
@app.route('/')
def hello():
	return render_template('index.html')

#Define route for login
@app.route('/login')
def login():
	return render_template('login.html')

@app.route('/register')
def register():
	return render_template('register.html')

@app.route('/home')
def home():
  if 'user_ID' not in session:
    return redirect(url_for('login'))
    
  user_ID = session['user_ID']
  
  cursor = conn.cursor()
  query = """
    SELECT cart_ID, store_name 
    FROM cart 
    WHERE user_ID = %s 
      AND EXISTS (
        SELECT 1 
        FROM item 
        WHERE item.cart_ID = cart.cart_ID
      )
    """
  cursor.execute(query, (user_ID,))
  cart_history = cursor.fetchall()
  
  count_query = 'SELECT COUNT(*) as num_items FROM item WHERE cart_ID = %s'
  total_query = 'SELECT SUM(price * quantity) AS total_spent FROM item WHERE cart_ID = %s'
  for cart in cart_history:
    cursor.execute(count_query, (cart['cart_ID'],))
    cart['total_items'] = cursor.fetchone()['num_items']
    
    cursor.execute(total_query, (cart['cart_ID'],))
    cart['total_spent'] = cursor.fetchone()['total_spent']
  
  return render_template('home.html', user_ID=user_ID, cart_history=cart_history)

#Authenticates the login
@app.route('/loginAuth', methods=['GET', 'POST'])
def loginAuth():
    if request.method == 'POST':
        user_ID = request.form['user_ID']
        password = request.form['password']

        cursor = conn.cursor()
        query = 'SELECT * FROM user_account WHERE user_ID = %s'
        cursor.execute(query, (user_ID,))
        data = cursor.fetchone()
        cursor.close()

        if data and hash_password_md5(password) == data['password']:
            session['user_ID'] = user_ID
            session.pop('cart_ID', None)
            return redirect(url_for('home'))
        else:
            error = 'Invalid username or password'
            return render_template('login.html', error=error)
    return render_template('login.html')

@app.route('/registerAuth', methods=['GET', 'POST'])
def registerAuth():
    if request.method == 'POST':
        user_ID = request.form['user_ID']
        password = request.form['password']
        email_address = request.form['email_address']

        hashed_password = hash_password_md5(password)

        cursor = conn.cursor()
        query = 'SELECT * FROM user_account WHERE user_ID = %s'
        cursor.execute(query, (user_ID,))
        data = cursor.fetchone()

        if data:
            error = "This username already exists"
            return render_template('register.html', error=error)
        else:
            ins = 'INSERT INTO user_account (user_ID, email, password) VALUES(%s, %s, %s)'
            cursor.execute(ins, (user_ID, email_address, hashed_password))
            conn.commit()
            cursor.close()
            session['user_ID'] = user_ID
            return redirect(url_for('home'))
            
    return render_template('register.html')

@app.route('/start-shopping', methods=['POST'])
def start_shopping():
    store_name = request.form.get('storeName')
    user_ID = session['user_ID']
    
    cursor = conn.cursor()
    
    query = 'SELECT * FROM cart WHERE user_ID = %s AND status = %s'
    cursor.execute(query, (user_ID, "active",))
    cart_ID = cursor.fetchone()
    
    items, total_items, total_spent = None, 0, 0
    if cart_ID:
      session['cart_ID'] = cart_ID['cart_ID']
      items, total_items, total_spent = retrieve_totals(cart_ID['cart_ID'])
    else:
      ins = 'INSERT INTO cart (user_ID, store_name, status) VALUES(%s, %s, %s)'
      cursor.execute(ins, (user_ID, store_name, "active",))
      conn.commit()

      query = 'SELECT * FROM cart WHERE user_ID = %s AND status = %s'
      cursor.execute(query, (user_ID, "active",))
      cart_ID = cursor.fetchone()
      session['cart_ID'] = cart_ID['cart_ID']
      
    cursor.close()
    
    return render_template(
            'shopping_trip.html',
            cart_session=cart_ID, 
            allocated_budget=1000,
            remaining=1000-total_spent,
            cart_items=items,
            total_items=total_items, 
            total_spent=total_spent
        )
    
@app.route('/shopping-trip')
def shopping_trip():
    if not "cart_ID" in session or not session['cart_ID']:
        # No active cart
        
        cursor = conn.cursor()
        query = 'SELECT * FROM cart WHERE user_ID = %s AND status = %s'
        cursor.execute(query, (session['user_ID'], "active"))
        cart_ID = cursor.fetchone()
        
        cursor.close()
        
        cart_session = None
        if cart_ID:

          cart_session = cart_ID
          session['cart_ID'] = cart_ID['cart_ID']
          
        return render_template(
            'shopping_trip.html',
            cart_session=cart_session,
            cart_items=None
        )
    else:
        # Query DB for cart items, budget, etc.
        cart_ID = session['cart_ID']
        
        cursor = conn.cursor()
        query = 'SELECT * FROM cart WHERE cart_ID = %s'
        cursor.execute(query, (cart_ID))
        cart = cursor.fetchone()
        
        
        items, total_items, total_spent = retrieve_totals(cart_ID)
        
        return render_template(
            'shopping_trip.html',
            cart_session=cart, 
            allocated_budget=1000,
            remaining=1000-total_spent,
            cart_items=items,
            total_items=total_items, 
            total_spent=total_spent
        )

@app.route('/finish-shopping', methods=['POST'])
def finish_shopping():
    user_ID = session['user_ID']
    cart_ID = session['cart_ID']
    cursor = conn.cursor()
    query = '''UPDATE cart SET status = %s 
                        WHERE cart_ID = %s'''
    cursor.execute(query, ("purchased", cart_ID))
    conn.commit()
    cursor.close()
    
    del session['cart_ID']
    
    # return render_template(
    #         'home.html',
    #         user_ID=user_ID
    #     )
    return redirect(url_for('home'))

@app.route('/shopping-trip/add-item', methods=['POST'])
def add_item():
    user_ID = session['user_ID']
    cart_ID = session['cart_ID']
    
    if not user_ID or not cart_ID:
        return jsonify({"error": "No active cart or user session"}), 400

    # 2) Parse JSON from the request
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON body"}), 400

    upc = data.get('upc')
    price = data.get('price')
    quantity = data.get('quantity')
    item_name = data.get('itemName')
    image_url = data.get('imageUrl')

    # Basic validation
    if not upc or price is None or quantity is None or item_name is None or image_url is None:
        return jsonify({"error": "Missing fields (upc, price, quantity, item)"}), 400

    cursor = conn.cursor()
    ins = 'INSERT INTO item (cart_ID, user_ID, quantity, item_name, price, upc, item_lifetime, image_url) VALUES(%s, %s, %s, %s, %s, %s, %s, %s)'
    cursor.execute(ins, (cart_ID, user_ID, quantity, item_name, price, upc, 7, image_url))
    
    conn.commit()
    
    cursor = conn.cursor()
    query = 'SELECT * FROM item WHERE cart_ID = %s'
    cursor.execute(query, (cart_ID))
    
    items = cursor.fetchall()

    cursor.close()

    # Redirect back to the shopping trip page.
    return jsonify({"status": "success", "items": items}), 200
  
@app.route('/shopping-trip/items', methods=['GET'])
def get_cart_items():
    if "cart_ID" not in session or not session['cart_ID']:
        return jsonify({"items": [], 
              "allocated_budget": 0,
              "total_spent": 0,
              "total_items": 0,
              "remaining": 0})
    
    cart_ID = session['cart_ID']
    cursor = conn.cursor()
    query = 'SELECT item_name, price, quantity, image_url FROM item WHERE cart_ID = %s'
    cursor.execute(query, (cart_ID,))

    items = cursor.fetchall()

    cursor.close()
    
    return jsonify({"items": items})
  
@app.route('/cancel-shopping', methods=['POST'])
def cancel_shopping():
    session['cart_ID'] = []
    session.pop('cart_ID', None)
    session.modified = True
    flash("Your shopping trip has been canceled.", "info")
    return redirect('/home')
  
@app.route('/edit-list')
def edit_list():
	return render_template('shopping_list.html')

@app.route('/list/items', methods=['GET'])
def list_get_items():
    """Return the current shopping list as JSON."""
    # Get the local shopping list from the session, or initialize an empty list.
    items = session.get('shopping_list', [])
    
    flag = session.get('db_items_loaded', False)
    
    # Only load from the database if we haven't done it already.
    if not flag:
        user_ID = session['user_ID']
        
        cursor = conn.cursor()
        query = """
            SELECT list_ID, item_name AS name, quantity 
            FROM shopping_list 
            WHERE user_ID = %s AND status = %s
        """
        cursor.execute(query, (user_ID, "pending",))
        db_items = cursor.fetchall()
        
        # Append the db items to the local list
        items.extend(db_items)
        session['shopping_list'] = items
        
        # Mark that we have loaded the db items once
        session['db_items_loaded'] = True
        session['to_be_deleted'] = []

    return jsonify({'items': items})

@app.route('/list/add_item', methods=['POST'])
def list_add_item():
    data = request.get_json()
    item_name = data.get('item')
    quantity = data.get('quantity', 1)
    if not item_name:
        return jsonify({'error': 'No item provided'}), 400

    # Create an object for the item
    new_item = {"list_ID": -1, "name": item_name, "quantity": quantity}
    shopping_list = session.get('shopping_list', [])
    shopping_list.append(new_item)
    session['shopping_list'] = shopping_list
    return jsonify({'items': shopping_list})

@app.route('/list/remove_item', methods=['POST'])
def list_remove_item():
    data = request.get_json()
    item_name = data.get('item')
    shopping_list = session.get('shopping_list', [])
    to_be_deleted = session.get('to_be_deleted', [])
    
    for product in shopping_list:
        if product.get('name') == item_name:
            if product.get('list_ID') != -1:
              to_be_deleted.append(product.get('list_ID'))
              session['to_be_deleted'] = to_be_deleted
            shopping_list.remove(product)
            session['shopping_list'] = shopping_list
            return jsonify({'items': shopping_list})
    return jsonify({'error': 'Item not found'}), 404
  
@app.route('/list/save', methods=['POST'])
def list_save():
    """Return the current shopping list as JSON."""
    user_ID = session['user_ID']
    
    cursor = conn.cursor()
    ins = 'INSERT INTO shopping_list (user_ID, item_name, quantity, status) VALUES(%s, %s, %s, %s)'
    delete = 'DELETE FROM shopping_list WHERE list_ID = %s'
    
    shopping_list = session.get('shopping_list', [])
    to_be_deleted = session.get('to_be_deleted', [])

    for product in shopping_list:
      if product['list_ID'] == -1:
        cursor.execute(ins, (user_ID, product.get("name"), product.get("quantity"), "pending"))
        conn.commit()
        
    for list_ID in to_be_deleted:
      cursor.execute(delete, (list_ID,))
      conn.commit()
      
    cursor.close()
    
    session['shopping_list'] = []
    session['to_be_deleted'] = []
    session['db_items_loaded'] = False
      
    return jsonify({'items': shopping_list})

@app.route('/rewards')
def rewards():
    return render_template('reward.html')

@app.route('/budget')
def budget():
    return render_template('budget.html')

@app.route('/searchitem', methods=['GET'])
def searchitem():
    # Load API keys from environment variables
    api_id = os.getenv('NUTRITIONIX_API_ID')
    api_key = os.getenv('NUTRITIONIX_API_KEY')

    # Check if the API keys are set
    if not api_id or not api_key or api_id == "YOUR_API_ID_HERE":
        return jsonify({'error': 'Nutritionix API keys are not configured on the server.'}), 500

    upc = request.args.get('upc')
    if not upc:
        return jsonify({'error': 'UPC parameter is required'}), 400

    url = f'https://trackapi.nutritionix.com/v2/search/item?upc={upc}'
    headers = {
        'x-app-id': api_id,
        'x-app-key': api_key
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        return jsonify(response.json())
    except requests.exceptions.HTTPError as err:
        if err.response.status_code == 404:
            return jsonify({'error': f'No item found for UPC {upc}'}), 404
        return jsonify({'error': str(err)}), err.response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'A network error occurred: {e}'}), 500

@app.route('/predict')
def predict():
    carbs = request.args.get('carbs')
    sugar = request.args.get('sugar')
    sodium = request.args.get('sodium')
    fat = request.args.get('fat')

    if helper.model == None:
        return jsonify({'error': 'Model didnt load properly'}), 500
    
    prediction = helper.predict_impulsive_purchase(carbs, sugar, sodium, fat).item()

    response = {
        'prediction': int(prediction)
    }

    return jsonify(response)

@app.route('/learn')
def learn():
    carbs = request.args.get('carbs')
    sugar = request.args.get('sugar')
    sodium = request.args.get('sodium')
    fat = request.args.get('fat')

    if helper.model == None:
        return jsonify({'error': 'Model didnt load properly'}), 500
    
    helper.model_learn(carbs, sugar, sodium, fat)
    print('model learned its mistake, model promises it may or may not make the same mistake again')

    return jsonify({'status': 'learned'}), 200

@app.route('/logout')
def logout():
  session.pop('user_ID')
  if 'cart_ID' in session:
    session.pop('cart_ID', None)
  if 'shopping_list' in session:
    session.pop('shopping_list', None)
  if 'to_be_deleted' in session:
    session.pop('to_be_deleted', None)
  if 'db_items_loaded' in session:
    session.pop('db_items_loaded', None)
    
  session.clear()
  return redirect('/')

def retrieve_totals(cart_ID):
    cursor = conn.cursor()
    query = 'SELECT * FROM item WHERE cart_ID = %s'
    cursor.execute(query, (cart_ID))
    
    items = cursor.fetchall()
    
    query = 'SELECT COUNT(*) as num_items FROM item WHERE cart_ID = %s'
    cursor.execute(query, (cart_ID))
    
    row = cursor.fetchone()

    if row:
        total_items = row['num_items']
    
    query = 'SELECT SUM(price * quantity) AS total_spent FROM item WHERE cart_ID = %s'
    cursor.execute(query, (cart_ID))
    
    row = cursor.fetchone()

    if row:
        total_spent = row['total_spent']
    
    if not total_items:
      total_items = 0
      
    if not total_spent:
      total_spent = 0
    
    return items, total_items, total_spent

def hash_password_md5(password):
    # Create an MD5 hash object
    md5 = hashlib.md5()
    # Encode and hash the password
    md5.update(password.encode('utf-8'))
    return md5.hexdigest()
		
app.secret_key = 'some key that you will never guess'
#Run the app on localhost port 5000
#debug = True -> you don't have to restart flask
#for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
	app.run('127.0.0.1', 5000, debug = True)
