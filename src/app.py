#Import Flask Library
from flask import Flask, render_template, request, session, url_for, redirect, jsonify
import requests
import pymysql.cursors
import hashlib
import config

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
	return render_template('home.html')

#Authenticates the login
@app.route('/loginAuth', methods=['GET', 'POST'])
def loginAuth():
    #grabs information from the forms
    user_ID = request.form['user_ID']
    password = request.form['password']

    #cursor used to send queries
    cursor = conn.cursor()
    #executes query
    query = 'SELECT * FROM user_account WHERE user_ID = %s'
    cursor.execute(query, (user_ID))
    #stores the results in a variable
    data = cursor.fetchone()
    #use fetchall() if you are expecting more than 1 data row
    cursor.close()
    error = None
    if(data):
        #if bcrypt.checkpw(password.encode('utf-8'), data['password'].encode('utf-8')):
        if hash_password_md5(password)==data['password']:
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
    query = 'SELECT * FROM user_account WHERE user_ID = %s'
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
        ins = 'INSERT INTO user_account VALUES(%s, %s, %s)'
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
    
    query = 'SELECT * FROM cart WHERE user_ID = %s AND status = %s'
    cursor.execute(query, (user_ID, "active"))
    cart_ID = cursor.fetchone()
    
    items, total_items, total_spent = None, None, None
    if cart_ID:
      print("BRONNY")
      session['cart_ID'] = cart_ID['cart_ID']
      items, total_items, total_spent = retrieve_totals(cart_ID)
    else:
      print("ALPEREN SENGUN")
      ins = 'INSERT INTO cart (user_ID, store_name, status) VALUES(%s, %s, %s)'
      cursor.execute(ins, (user_ID, store_name, "active"))
      conn.commit()

      query = 'SELECT * FROM cart WHERE user_ID = %s AND status = %s'
      cursor.execute(query, (user_ID, "active"))
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
        print("KYLE KUZMA")
        
        cursor = conn.cursor()
        query = 'SELECT * FROM cart WHERE user_ID = %s AND status = %s'
        cursor.execute(query, (session['user_ID'], "active"))
        cart_ID = cursor.fetchone()
        
        cursor.close()
        
        cart_session = None
        if cart_ID:
          print("KLAY THOMPSON")
          cart_session = cart_ID
          session['cart_ID'] = cart_ID['cart_ID']
          
        return render_template(
            'shopping_trip.html',
            cart_session=cart_session
        )
    else:
        # Query DB for cart items, budget, etc.
        cart_ID = session['cart_ID']
        print(type(cart_ID))
        print(cart_ID)
        print("LEBRON JAMES")
        
        items, total_items, total_spent = retrieve_totals(cart_ID)
        
        return render_template(
            'shopping_trip.html',
            cart_session=cart_ID, 
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
    
    return render_template(
            'shopping_trip.html',
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

@app.route('/logout')
def logout():
  session.pop('user_ID')
  if 'cart_ID' in session:
    session.pop('cart_ID')
  return redirect('/')

def retrieve_totals(cart_ID):
    cursor = conn.cursor()
    query = 'SELECT * FROM item WHERE cart_ID = %s'
    cursor.execute(query, (cart_ID))
    
    items = cursor.fetchall()
    
    query = 'SELECT COUNT(*) FROM item WHERE cart_ID = %s'
    cursor.execute(query, (cart_ID))
    
    total_items = cursor.fetchall()['COUNT(*)']
    
    query = 'SELECT SUM(price * quantity) AS total_spent FROM item WHERE cart_ID = %s'
    cursor.execute(query, (cart_ID))
    
    total_spent = cursor.fetchall()['total_spent']
    
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
