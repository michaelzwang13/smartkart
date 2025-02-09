#Import Flask Library
from flask import Flask, render_template, request, session, url_for, redirect, jsonify, flash
import requests
import pyodbc
import pymysql.cursors
import hashlib
import config
import helper

#Initialize the app from Flask
app = Flask(__name__)

#Configure MySQL
# conn = pymysql.connect(host='localhost',
# 											 port= 8889,
#                        user='root',
#                        password='root',
#                        db='hacknyu25',
#                        charset='utf8mb4',
#                        cursorclass=pymysql.cursors.DictCursor)

# conn = pymysql.connect(host='localhost',
# 						port= 3306,
#                          user='willy',
#                          password='willy',
#                          database='hacknyu25',
#                          charset='utf8mb4',
#                          cursorclass=pymysql.cursors.DictCursor)

server = 'smart-kart-server.database.windows.net'
database = 'smart-kart-db'
username = config.AZURE_UID
password = config.AZURE_PWD
driver = '{ODBC DRIVER 18 for SQL Server}'

conn = pyodbc.connect(f'DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}')

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
  user_ID = session['user_ID']
  return render_template('home.html', user_ID=user_ID)

#Authenticates the login
@app.route('/loginAuth', methods=['GET', 'POST'])
def loginAuth():
    #grabs information from the forms
    user_ID = request.form['user_ID']
    password = request.form['password']

    #cursor used to send queries
    cursor = conn.cursor()
    #executes query
    query = 'SELECT * FROM user_account WHERE user_ID = ?'
    cursor.execute(query, (user_ID,))
    #stores the results in a variable
    data = cursor.fetchone()
    #use fetchall() if you are expecting more than 1 data row
    cursor.close()
    error = None
    if(data):
        #if bcrypt.checkpw(password.encode('utf-8'), data['password'].encode('utf-8')):
        if hash_password_md5(password)==data[2]:
        #creates a session for the the user
        #session is a built in
            session['user_ID'] = user_ID
            session['cart_ID'] = None
            # return redirect(url_for('home'))
            return render_template('home.html', user_ID=user_ID)
        else:
            error = 'Invalid username or password'
            return render_template('login.html', error=error)
            
    else:
           #returns an error message to the html page
        error = 'Invalid username or password'
        return render_template('login.html', error=error)
      
@app.route('/registerAuth', methods=['GET', 'POST'])
def registerAuth():
    #grabs information from the forms
    user_ID = request.form['user_ID']
    password = request.form['password']
    email_address = request.form['email_address']

    hashed_password = hash_password_md5(password)#bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    #cursor used to send queries
    cursor = conn.cursor()
    #executes query
    query = 'SELECT * FROM user_account WHERE user_ID = ?'
    cursor.execute(query, (user_ID))
    #stores the results in a variable
    data = cursor.fetchone()
    #use fetchall() if you are expecting more than 1 data row
    error = None
    if(data):
        #If the previous query returns data, then user exists
        error = "This username already exists"
        return render_template('register.html', error = error)
    else:
        ins = 'INSERT INTO user_account VALUES(?, ?, ?)'
        cursor.execute(ins, (user_ID, email_address, hashed_password))
        
        conn.commit()
        cursor.close()
        session['user_ID'] = user_ID
        return render_template('home.html', user_ID=user_ID)

@app.route('/start-shopping', methods=['POST'])
def start_shopping():
    store_name = request.form.get('storeName')
    user_ID = session['user_ID']
    
    cursor = conn.cursor()
    
    query = 'SELECT * FROM cart WHERE user_ID = ? AND status = ?'
    cursor.execute(query, (user_ID, "active"))
    cart_ID = cursor.fetchone()
    
    items, total_items, total_spent = None, 0, 0
    if cart_ID:
      print("BRONNY")
      session['cart_ID'] = cart_ID['cart_ID']
      items, total_items, total_spent = retrieve_totals(cart_ID['cart_ID'])
    else:
      print("ALPEREN SENGUN")
      ins = 'INSERT INTO cart (user_ID, store_name, status) VALUES(?, ?, ?)'
      cursor.execute(ins, (user_ID, store_name, "active"))
      conn.commit()

      query = 'SELECT * FROM cart WHERE user_ID = ? AND status = ?'
      cursor.execute(query, (user_ID, "active"))
      cart_ID = cursor.fetchone()
      session['cart_ID'] = cart_ID[0]
      
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
        print("KYLE KUZMA")
        
        cursor = conn.cursor()
        query = 'SELECT * FROM cart WHERE user_ID = ? AND status = ?'
        cursor.execute(query, (session['user_ID'], "active"))
        cart_ID = cursor.fetchone()
        
        cursor.close()
        
        cart_session = None
        if cart_ID:
          print("KLAY THOMPSON")
          cart_session = cart_ID
          session['cart_ID'] = cart_ID[0]
          
        return render_template(
            'shopping_trip.html',
            cart_session=cart_session
        )
    else:
        # Query DB for cart items, budget, etc.
        cart_ID = session['cart_ID']
        
        cursor = conn.cursor()
        query = 'SELECT * FROM cart WHERE cart_ID = ?'
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
    query = '''UPDATE cart SET status = ? 
                        WHERE cart_ID = ?'''
    cursor.execute(query, ("purchased", cart_ID))
    conn.commit()
    cursor.close()
    
    del session['cart_ID']
    
    return render_template(
            'home.html',
            user_ID=user_ID
        )

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
    ins = 'INSERT INTO item (cart_ID, user_ID, quantity, item_name, price, upc, item_lifetime, image_url) VALUES(?, ?, ?, ?, ?, ?, ?, ?)'
    cursor.execute(ins, (cart_ID, user_ID, quantity, item_name, price, upc, 7, image_url))
    
    conn.commit()
    
    cursor = conn.cursor()
    query = 'SELECT * FROM item WHERE cart_ID = ?'
    cursor.execute(query, (cart_ID))
    
    rows = cursor.fetchall()

    columns = [column[0] for column in cursor.description]
    items = [dict(zip(columns, row)) for row in rows]

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
    query = 'SELECT item_name, price, quantity, image_url FROM item WHERE cart_ID = ?'
    cursor.execute(query, (cart_ID,))

    rows = cursor.fetchall()

    columns = [column[0] for column in cursor.description]
    items = [dict(zip(columns, row)) for row in rows]

    cursor.close()
    
    return jsonify({"items": items})
  
@app.route('/edit-list')
def edit_list():
	return render_template('shopping_list.html')

@app.route('/list/items', methods=['GET'])
def list_get_items():
    """Return the current shopping list as JSON."""
    items = session.get('shopping_list', [])
    user_ID = session['user_ID']
    
    cursor = conn.cursor()
    query = "SELECT item_name as name, quantity FROM shopping_list WHERE user_ID = %s AND status = %s"
    db_items = cursor.fetchall(query, (user_ID, "pending",))
    
    print(db_items)
    
    for item in db_items:
      items.append(item)
    return jsonify({'items': items})

@app.route('/list/add_item', methods=['POST'])
def list_add_item():
    data = request.get_json()
    item_name = data.get('item')
    quantity = data.get('quantity', 1)
    if not item_name:
        return jsonify({'error': 'No item provided'}), 400

    # Create an object for the item
    new_item = {"name": item_name, "quantity": quantity}
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
            if product.get('cart_ID') != -1:
              to_be_deleted.append(product.get('cart_ID'))
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
    delete = 'DELETE FROM shopping_list WHERE cart_ID = %s'
    
    shopping_list = session.get('shopping_list', [])
    to_be_deleted = session.get('to_be_deleted', [])
    
    print(shopping_list)
    print("LEBRONNNN")
    for product in shopping_list:
      if product['list_ID'] == -1:
        cursor.execute(ins, (user_ID, product.get("name"), product.get("quantity"), "pending"))
        conn.commit()
        
    for product in to_be_deleted:
      cursor.execute(delete, (product['cart_ID']))
      conn.commit()
      
    cursor.close()
    
    session['shopping_list'] = []
    session['to_be_deleted'] = []
      
    return jsonify({'items': shopping_list})

@app.route('/rewards')
def rewards():
    return render_template('reward.html')

@app.route('/budget')
def budget():
    return render_template('budget.html')

@app.route('/searchitem', methods=['GET'])
def searchitem():
    url = 'https://trackapi.nutritionix.com/v2/search/item?upc='
    headers = {
        'x-app-id': config.API_ID,
        'x-app-key': config.API_KEY
    }

    upc = request.args.get('upc')
    
    if not upc:
        return jsonify({'error': 'UPC parameter is required'}), 400  # Return error if no 'upc' parameter

    url += upc
    response = requests.get(url, headers=headers)

    return jsonify(response.json())

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
    session.pop('cart_ID')
  if 'shopping_list' in session:
    session.pop('shopping_list')
  return redirect('/')

def retrieve_totals(cart_ID):
    cursor = conn.cursor()
    query = 'SELECT * FROM item WHERE cart_ID = ?'
    cursor.execute(query, (cart_ID))
    
    items = cursor.fetchall()
    
    query = 'SELECT COUNT(*) as num_items FROM item WHERE cart_ID = ?'
    cursor.execute(query, (cart_ID))
    
    row = cursor.fetchone()

    if row:
        total_items = row[0]
    
    query = 'SELECT SUM(price * quantity) AS total_spent FROM item WHERE cart_ID = ?'
    cursor.execute(query, (cart_ID))
    
    row = cursor.fetchone()

    if row:
        total_spent = row[0]
    
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
