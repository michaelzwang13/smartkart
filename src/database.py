import pymysql.cursors
from flask import g, current_app

def get_db():
    """
    Connects to the specific database.
    """
    if 'db' not in g:
        g.db = pymysql.connect(
            host=current_app.config['DB_HOST'],
            port=current_app.config['DB_PORT'],
            user=current_app.config['DB_USER'],
            password=current_app.config['DB_PASSWORD'],
            db=current_app.config['DB_NAME'],
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
    return g.db

def close_db(e=None):
    """
    Closes the database again at the end of the request.
    """
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_app(app):
    """Register database functions with the Flask app."""
    app.teardown_appcontext(close_db)
