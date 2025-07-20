from flask import Flask

def create_app():
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__, instance_relative_config=True)
    
    # Load configuration from the config file
    app.config.from_object('src.config.Config')

    # Initialize database
    from . import database
    database.init_app(app)

    # Register blueprints for different parts of the app
    from .views import auth, shopping, api
    app.register_blueprint(auth.auth_bp)
    app.register_blueprint(shopping.shopping_bp)
    app.register_blueprint(api.api_bp)

    return app
