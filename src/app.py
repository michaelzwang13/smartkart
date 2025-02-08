#Import Flask Library
from flask import Flask, render_template, request, session, url_for, redirect, jsonify
import requests
import pymysql.cursors
import hashlib
import config

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

conn = pymysql.connect(host='localhost',
						port= 3306,
                         user='willy',
                         password='willy',
                         database='hacknyu25',
                         charset='utf8mb4',
                         cursorclass=pymysql.cursors.DictCursor)

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
            return render_template('user_home.html')
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
        return render_template('index.html')

@app.route('/start-shopping', methods=['POST'])
def start_shopping():
    store_name = request.form.get('storeName')
    user_ID = session['user_ID']
    
    cursor = conn.cursor()
    
    query = 'SELECT cart_ID FROM cart WHERE user_ID = %s AND status = %s'
    cursor.execute(query, (user_ID, "active"))
    cart_ID = cursor.fetchone()
    
    if cart_ID:
      session['cart_ID'] = cart_ID
    else:
      ins = 'INSERT INTO cart VALUES(%s, %s, %s)'
      cursor.execute(ins, (user_ID, store_name, "active"))
      conn.commit()
      session['cart_ID'] = cursor.fetchone()
    
    cursor.close()
    
    return redirect(url_for('shopping_trip'))

@app.route('/shopping-trip')
def shopping_trip():
    if not "cart_ID" in session:
        # No active cart
        return render_template('shopping_trip.html', cart_session=None)
    else:
        # Query DB for cart items, budget, etc.
        cart_ID = session['cart_ID']
        cursor = conn.cursor()
        query = 'SELECT * FROM item WHERE cart_ID = %s'
        cursor.execute(query, (cart_ID))
        
        items = cursor.fetchall()
        
        return render_template(
            'shopping_trip.html', 
            cart_items=items,
            # cart_items=..., 
            # allocated_budget=..., 
            # current_spend=...
        )

@app.route('/finish-shopping', methods=['POST'])
def finish_shopping():
    cart_ID = session['cart_ID']
    cursor = conn.cursor()
    query = '''UPDATE cart SET status = %s 
                        WHERE ID = %s'''
    cursor.execute(query, ("purchased", cart_ID))
    return redirect(url_for('shopping_trip'))

@app.route('/shopping-trip/add-item', methods=['POST'])
def add_item():
    user_ID = session['user_ID']
    cart_ID = session['cart_ID']
    upc = request.form['upc']
    price = request.form['itemPrice']
    quantity = request.form['itemQty']

    cursor = conn.cursor()
    ins = 'INSERT INTO item VALUES(%s, %s, %s, %s, %s, %s, %s)'
    cursor.execute(ins, (cart_ID, user_ID, quantity, price, "BREAD", upc, 7))
    
    conn.commit()
    cursor.close()

    # Redirect back to the shopping trip page.
    return render_template('shopping_trip.html')

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
	session.pop('user_id')
	return redirect('/')

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
