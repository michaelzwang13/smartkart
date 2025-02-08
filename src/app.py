#Import Flask Library
from flask import Flask, render_template, request, session, url_for, redirect
import pymysql.cursors

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

#Define route for register
@app.route('/register')
def register():
	return render_template('register.html')

#Authenticates the login
@app.route('/loginAuth', methods=['GET', 'POST'])
def loginAuth():
	#grabs information from the forms
	username = request.form['username']
	password = request.form['password']

	#cursor used to send queries
	cursor = conn.cursor()
	#executes query
	query = 'SELECT * FROM user WHERE username = %s and password = %s'
	cursor.execute(query, (username, password))
	#stores the results in a variable
	data = cursor.fetchone()
	#use fetchall() if you are expecting more than 1 data row
	cursor.close()
	error = None
	if(data):
		#creates a session for the the user
		#session is a built in
		session['username'] = username
		return redirect(url_for('home'))
	else:
		#returns an error message to the html page
		error = 'Invalid login or username'
		return render_template('login.html', error=error)

#Authenticates the register
@app.route('/registerAuth', methods=['GET', 'POST'])
def registerAuth():
	#grabs information from the forms
	username = request.form['username']
	password = request.form['password']

	#cursor used to send queries
	cursor = conn.cursor()
	#executes query
	query = 'SELECT * FROM user WHERE username = %s'
	cursor.execute(query, (username))
	#stores the results in a variable
	data = cursor.fetchone()
	#use fetchall() if you are expecting more than 1 data row
	error = None
	if(data):
		#If the previous query returns data, then user exists
		error = "This user already exists"
		return render_template('register.html', error = error)
	else:
		ins = 'INSERT INTO user VALUES(%s, %s)'
		cursor.execute(ins, (username, password))
		conn.commit()
		cursor.close()
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
	session.pop('username')
	return redirect('/')
		
app.secret_key = 'some key that you will never guess'
#Run the app on localhost port 5000
#debug = True -> you don't have to restart flask
#for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
	app.run('127.0.0.1', 5000, debug = True)
