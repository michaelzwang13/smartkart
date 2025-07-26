from flask import Blueprint, render_template, request, session, url_for, redirect
import bcrypt

from src.database import get_db

auth_bp = Blueprint('auth', __name__)

def hash_password_bcrypt(password):
    """Generates a bcrypt hash for a given password."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password_bcrypt(password, hashed_password):
    """Verifies a password against its bcrypt hash."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def restore_active_cart(user_ID):
    """Restore active shopping cart for user after login"""
    try:
        db = get_db()
        cursor = db.cursor()
        
        # Look for active shopping cart for this user
        query = 'SELECT cart_ID FROM shopping_cart WHERE user_ID = %s AND status = "active" ORDER BY created_at DESC LIMIT 1'
        cursor.execute(query, (user_ID,))
        active_cart = cursor.fetchone()
        
        if active_cart:
            session['cart_ID'] = active_cart['cart_ID']
            print(f"Restored active cart {active_cart['cart_ID']} for user {user_ID}")
        
        cursor.close()
    except Exception as e:
        print(f"Error restoring active cart: {str(e)}")
        # Don't raise error - just log it

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_ID = request.form['user_ID'].strip()
        password = request.form['password']

        # Basic validation
        if not user_ID or not password:
            error = 'Username and password are required'
            return render_template('login.html', error=error)

        try:
            db = get_db()
            cursor = db.cursor()
            query = 'SELECT * FROM user_account WHERE user_ID = %s'
            cursor.execute(query, (user_ID,))
            data = cursor.fetchone()
            cursor.close()

            if data and verify_password_bcrypt(password, data['password']):
                session['user_ID'] = user_ID
                # Check for active shopping cart and restore it
                restore_active_cart(user_ID)
                return redirect(url_for('shopping.home'))
            else:
                error = 'Invalid username or password'
                return render_template('login.html', error=error)
        except Exception as e:
            error = 'Login failed. Please try again.'
            return render_template('login.html', error=error)
            
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user_ID = request.form['user_ID'].strip()
        password = request.form['password']
        email_address = request.form['email_address'].strip()
        confirm_password = request.form.get('confirmPassword', '')

        # Validation
        if not user_ID or not password or not email_address:
            error = "All fields are required"
            return render_template('register.html', error=error)
        
        if len(user_ID) < 3:
            error = "Username must be at least 3 characters long"
            return render_template('register.html', error=error)
        
        if len(password) < 6:
            error = "Password must be at least 6 characters long"
            return render_template('register.html', error=error)
        
        if password != confirm_password:
            error = "Passwords do not match"
            return render_template('register.html', error=error)

        # Hash password
        hashed_password = hash_password_bcrypt(password)

        db = get_db()
        cursor = db.cursor()
        
        # Check if username already exists
        query = 'SELECT * FROM user_account WHERE user_ID = %s'
        cursor.execute(query, (user_ID,))
        data = cursor.fetchone()

        if data:
            cursor.close()
            error = "This username already exists"
            return render_template('register.html', error=error)
        
        # Check if email already exists
        query = 'SELECT * FROM user_account WHERE email = %s'
        cursor.execute(query, (email_address,))
        data = cursor.fetchone()

        if data:
            cursor.close()
            error = "This email address is already registered"
            return render_template('register.html', error=error)
        
        try:
            # Insert new user
            ins = 'INSERT INTO user_account (user_ID, email, password) VALUES(%s, %s, %s)'
            cursor.execute(ins, (user_ID, email_address, hashed_password))
            db.commit()
            cursor.close()
            session['user_ID'] = user_ID
            # Check for any active carts (shouldn't exist for new user, but just in case)
            restore_active_cart(user_ID)
            return redirect(url_for('shopping.home'))
        except Exception as e:
            cursor.close()
            error = "Registration failed. Please try again."
            return render_template('register.html', error=error)
            
    return render_template('register.html')

@auth_bp.route('/logout')
def logout():
  # Only clear user authentication, preserve cart for later
  user_ID = session.get('user_ID')
  cart_ID = session.get('cart_ID')
  
  # Clear session but preserve cart association in database
  session.clear()
  
  return redirect(url_for('auth.login'))
