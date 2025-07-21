from flask import Blueprint, render_template, request, session, url_for, redirect, flash
from src.database import get_db

shopping_bp = Blueprint('shopping', __name__)

def retrieve_totals(cart_ID):
    db = get_db()
    cursor = db.cursor()
    
    query_items = 'SELECT * FROM cart_item WHERE cart_ID = %s'
    cursor.execute(query_items, (cart_ID,))
    items = cursor.fetchall()
    
    query_totals = 'SELECT COUNT(*) as num_items, SUM(price * quantity) AS total_spent FROM cart_item WHERE cart_ID = %s'
    cursor.execute(query_totals, (cart_ID,))
    totals = cursor.fetchone()
    
    total_items = totals.get('num_items', 0) if totals else 0
    total_spent = totals.get('total_spent', 0) if totals else 0
    
    return items, total_items, total_spent

@shopping_bp.route('/')
def index():
	return render_template('index.html')

@shopping_bp.route('/home')
def home():
  if 'user_ID' not in session:
    return redirect(url_for('auth.login'))
    
  user_ID = session['user_ID']
  
  db = get_db()
  cursor = db.cursor()
  query = """
    SELECT c.cart_ID, c.store_name, 
           (SELECT COUNT(*) FROM cart_item i WHERE i.cart_ID = c.cart_ID) as total_items,
           (SELECT SUM(i.price * i.quantity) FROM cart_item i WHERE i.cart_ID = c.cart_ID) as total_spent
    FROM shopping_cart c
    WHERE c.user_ID = %s 
      AND EXISTS (SELECT 1 FROM cart_item i WHERE i.cart_ID = c.cart_ID)
    """
  cursor.execute(query, (user_ID,))
  cart_history = cursor.fetchall()
  
  return render_template('home.html', user_ID=user_ID, cart_history=cart_history)

@shopping_bp.route('/start-shopping', methods=['POST'])
def start_shopping():
    store_name = request.form.get('storeName')
    user_ID = session['user_ID']
    
    db = get_db()
    cursor = db.cursor()
    
    ins = 'INSERT INTO shopping_cart (user_ID, store_name, status) VALUES(%s, %s, %s)'
    cursor.execute(ins, (user_ID, store_name, "active"))
    db.commit()
    session['cart_ID'] = cursor.lastrowid
    cursor.close()
    
    return redirect(url_for('shopping.shopping_trip'))
    
@shopping_bp.route('/shopping-trip')
def shopping_trip():
    if 'user_ID' not in session:
        return redirect(url_for('auth.login'))

    cart_session = None
    items = []
    total_items = 0
    total_spent = 0

    if "cart_ID" in session and session['cart_ID']:
        cart_ID = session['cart_ID']
        db = get_db()
        cursor = db.cursor()
        query = 'SELECT * FROM shopping_cart WHERE cart_ID = %s'
        cursor.execute(query, (cart_ID,))
        cart_session = cursor.fetchone()
        
        if cart_session:
            items, total_items, total_spent = retrieve_totals(cart_ID)
        
        cursor.close()

    return render_template(
        'shopping_trip.html',
        cart_session=cart_session, 
        allocated_budget=1000,
        remaining=1000 - (total_spent or 0),
        cart_items=items,
        total_items=total_items, 
        total_spent=total_spent
    )

@shopping_bp.route('/finish-shopping', methods=['POST'])
def finish_shopping():
    cart_ID = session.pop('cart_ID', None)
    if cart_ID:
        db = get_db()
        cursor = db.cursor()
        
        # Calculate total spent for this cart
        total_query = 'SELECT SUM(price * quantity) AS total_spent FROM cart_item WHERE cart_ID = %s'
        cursor.execute(total_query, (cart_ID,))
        total_result = cursor.fetchone()
        total_spent = float(total_result['total_spent'] or 0)
        
        # Update cart status to purchased
        query = "UPDATE shopping_cart SET status = 'purchased' WHERE cart_ID = %s"
        cursor.execute(query, (cart_ID,))
        db.commit()
        cursor.close()
        
        # Update budget with this spending
        if 'user_ID' in session and total_spent > 0:
            from src.views.api import update_budget_spending
            update_budget_spending(session['user_ID'], total_spent)
    
    return redirect(url_for('shopping.home'))

@shopping_bp.route('/cancel-shopping', methods=['POST'])
def cancel_shopping():
    cart_ID = session.pop('cart_ID', None)
    if cart_ID:
        db = get_db()
        cursor = db.cursor()
        # Also delete items associated with the cart
        cursor.execute("DELETE FROM cart_item WHERE cart_ID = %s", (cart_ID,))
        cursor.execute("DELETE FROM shopping_cart WHERE cart_ID = %s", (cart_ID,))
        db.commit()
        cursor.close()
        flash("Your shopping trip has been canceled.", "info")
    return redirect(url_for('shopping.home'))
  
@shopping_bp.route('/shopping-lists')
def shopping_lists():
    """Show the shopping lists page"""
    if 'user_ID' not in session:
        return redirect(url_for('auth.login'))
    return render_template('shopping_list.html')


@shopping_bp.route('/rewards')
def rewards():
    return render_template('reward.html')

@shopping_bp.route('/budget')
def budget():
    return render_template('budget.html')
