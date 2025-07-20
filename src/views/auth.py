from flask import Blueprint, render_template, request, session, url_for, redirect
import hashlib

from src.database import get_db

auth_bp = Blueprint('auth', __name__)

def hash_password_md5(password):
    """Generates an MD5 hash for a given password."""
    return hashlib.md5(password.encode('utf-8')).hexdigest()

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_ID = request.form['user_ID']
        password = request.form['password']

        db = get_db()
        cursor = db.cursor()
        query = 'SELECT * FROM user_account WHERE user_ID = %s'
        cursor.execute(query, (user_ID,))
        data = cursor.fetchone()
        cursor.close()

        if data and hash_password_md5(password) == data['password']:
            session['user_ID'] = user_ID
            session.pop('cart_ID', None)
            return redirect(url_for('shopping.home'))
        else:
            error = 'Invalid username or password'
            return render_template('login.html', error=error)
            
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user_ID = request.form['user_ID']
        password = request.form['password']
        email_address = request.form['email_address']

        hashed_password = hash_password_md5(password)

        db = get_db()
        cursor = db.cursor()
        query = 'SELECT * FROM user_account WHERE user_ID = %s'
        cursor.execute(query, (user_ID,))
        data = cursor.fetchone()

        if data:
            error = "This username already exists"
            return render_template('register.html', error=error)
        else:
            ins = 'INSERT INTO user_account (user_ID, email, password) VALUES(%s, %s, %s)'
            cursor.execute(ins, (user_ID, email_address, hashed_password))
            db.commit()
            cursor.close()
            session['user_ID'] = user_ID
            return redirect(url_for('shopping.home'))
            
    return render_template('register.html')

@auth_bp.route('/logout')
def logout():
  session.clear()
  return redirect(url_for('auth.login'))
