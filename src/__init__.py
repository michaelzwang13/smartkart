from flask import Flask, request, g
import uuid

def create_app():
    """Create and configure an instance of the Flask application."""

    # Initialize logging first
    from .logging_config import setup_logging, get_logger

    setup_logging()
    logger = get_logger("preppr.app")

    app = Flask(__name__, instance_relative_config=True)

    # Load configuration from the config file
    app.config.from_object("src.config.Config")
    logger.info("Application configuration loaded")

    # Initialize database
    from . import database

    database.init_app(app)
    logger.info("Database initialized")

    # Add request logging middleware
    @app.before_request
    def before_request():
        g.request_id = str(uuid.uuid4())
        g.start_time = None
        # Don't log static file requests
        if not request.path.startswith("/static"):
            logger.info(
                "Request started",
                extra={
                    "request_id": g.request_id,
                    "method": request.method,
                    "path": request.path,
                    "remote_addr": request.remote_addr,
                    "user_agent": request.headers.get("User-Agent", ""),
                },
            )

    @app.after_request
    def after_request(response):
        # Don't log static file requests
        if not request.path.startswith("/static"):
            logger.info(
                "Request completed",
                extra={
                    "request_id": getattr(g, "request_id", "unknown"),
                    "status_code": response.status_code,
                    "content_length": response.content_length,
                },
            )
        return response

    # Register blueprints for different parts of the app
    from src.backend.views import auth, shopping

    app.register_blueprint(auth.auth_bp)
    app.register_blueprint(shopping.shopping_bp)
    
    # Register new refactored blueprints
    from src.backend.apis import shopping_trip, shopping_list, shopping_list_integration, budget, pantry, meals, meal_plan_compat
    app.register_blueprint(shopping_trip.shopping_trip_bp)
    app.register_blueprint(shopping_list.shopping_list_bp)
    app.register_blueprint(shopping_list_integration.shopping_list_integration_bp)
    app.register_blueprint(budget.budget_bp)
    app.register_blueprint(pantry.pantry_bp)
    app.register_blueprint(meals.meals_bp)  # New individual meals API
    app.register_blueprint(meal_plan_compat.meal_plan_compat_bp)  # Compatibility layer
    
    
    logger.info("Blueprints registered successfully")

    logger.info("Flask application created successfully")
    return app
