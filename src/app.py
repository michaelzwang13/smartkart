#Import Flask Library
from flask import Flask, render_template, request, session, url_for, redirect
import pymysql.cursors
import hashlib

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
            return redirect(url_for('user_home'))
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


@app.route('/shopping_trip', methods=['GET'])
def get_shopping_trip():
    
    # total_spend = sum(item['price'] * item['quantity'] for item in CART_ITEMS)
    # remaining = BUDGET - total_spend
		
    return render_template('shopping_trip.html')

    # return render_template(
    #     'shopping_trip.html',
    #     cart_items=CART_ITEMS,
    #     allocated_budget=BUDGET,
    #     current_spend=round(total_spend, 2),
    #     remaining_budget=round(remaining, 2)
    # )

@app.route('/shopping-trip/add-item', methods=['POST'])
def add_item():
    """
    A sample endpoint that processes a form submission to add an item to the cart.
    This is optional but shows how you'd handle incoming form data.
    """
    item_name = request.form.get('itemName')
    item_price = float(request.form.get('itemPrice', 0))
    item_qty = int(request.form.get('itemQty', 1))

    # Append to our in-memory cart (in real usage, insert into your database).
    CART_ITEMS.append({
        'name': item_name,
        'price': item_price,
        'quantity': item_qty
    })

    # Redirect back to the shopping trip page.
    return redirect(url_for('get_shopping_trip'))

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
