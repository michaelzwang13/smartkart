from flask import Blueprint, render_template, request, session, url_for, redirect, g, jsonify
import bcrypt

from src.database import get_db
from src.logging_config import get_logger
from src.auth_utils import AuthUtils, jwt_required

auth_bp = Blueprint("auth", __name__)
logger = get_logger("preppr.auth")


def hash_password_bcrypt(password):
    """Legacy function - use AuthUtils.hash_password instead"""
    return AuthUtils.hash_password(password)


def verify_password_bcrypt(password, hashed_password):
    """Legacy function - use AuthUtils.verify_password instead"""
    return AuthUtils.verify_password(password, hashed_password)


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
            session["cart_ID"] = active_cart["cart_ID"]
            logger.info(
                "Restored active cart for user",
                extra={
                    "user_id": user_ID,
                    "cart_id": active_cart["cart_ID"],
                    "request_id": getattr(g, "request_id", None),
                },
            )
        else:
            logger.debug(
                "No active cart found for user",
                extra={
                    "user_id": user_ID,
                    "request_id": getattr(g, "request_id", None),
                },
            )

        cursor.close()
    except Exception as e:
        logger.error(
            "Failed to restore active cart",
            extra={
                "user_id": user_ID,
                "error": str(e),
                "request_id": getattr(g, "request_id", None),
            },
            exc_info=True,
        )
        # Don't raise error - just log it


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user_ID = request.form["user_ID"].strip()
        password = request.form["password"]

        logger.info(
            "Login attempt",
            extra={"user_id": user_ID, "request_id": getattr(g, "request_id", None)},
        )

        # Basic validation
        if not user_ID or not password:
            logger.warning(
                "Login failed - missing credentials",
                extra={
                    "user_id": user_ID,
                    "request_id": getattr(g, "request_id", None),
                },
            )
            error = "Username and password are required"
            return render_template("login.html", error=error)

        try:
            db = get_db()
            cursor = db.cursor()
            query = "SELECT * FROM user_account WHERE user_ID = %s"
            cursor.execute(query, (user_ID,))
            data = cursor.fetchone()
            cursor.close()

            if data and verify_password_bcrypt(password, data["password"]):
                session["user_ID"] = user_ID
                logger.info(
                    "Login successful",
                    extra={
                        "user_id": user_ID,
                        "request_id": getattr(g, "request_id", None),
                    },
                )
                # Check for active shopping cart and restore it
                restore_active_cart(user_ID)
                return redirect(url_for("shopping.home"))
            else:
                logger.warning(
                    "Login failed - invalid credentials",
                    extra={
                        "user_id": user_ID,
                        "user_exists": data is not None,
                        "request_id": getattr(g, "request_id", None),
                    },
                )
                error = "Invalid username or password"
                return render_template("login.html", error=error)
        except Exception as e:
            logger.error(
                "Login failed - database error",
                extra={
                    "user_id": user_ID,
                    "error": str(e),
                    "request_id": getattr(g, "request_id", None),
                },
                exc_info=True,
            )
            error = "Login failed. Please try again."
            return render_template("login.html", error=error)

    return render_template("login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()
        user_ID = request.form["user_ID"].strip()
        password = request.form["password"]
        email_address = request.form["email_address"].strip()
        confirm_password = request.form.get("confirmPassword", "")

        # Validation - first_name and last_name are optional
        if not user_ID or not password or not email_address:
            error = "Email, username, and password are required"
            return render_template("register.html", error=error)

        if len(user_ID) < 3:
            error = "Username must be at least 3 characters long"
            return render_template("register.html", error=error)

        if len(password) < 6:
            error = "Password must be at least 6 characters long"
            return render_template("register.html", error=error)

        if password != confirm_password:
            error = "Passwords do not match"
            return render_template("register.html", error=error)

        # Hash password
        hashed_password = hash_password_bcrypt(password)

        db = get_db()
        cursor = db.cursor()

        # Check if username already exists
        query = "SELECT * FROM user_account WHERE user_ID = %s"
        cursor.execute(query, (user_ID,))
        data = cursor.fetchone()

        if data:
            cursor.close()
            error = "This username already exists"
            return render_template("register.html", error=error)

        # Check if email already exists
        query = "SELECT * FROM user_account WHERE email = %s"
        cursor.execute(query, (email_address,))
        data = cursor.fetchone()

        if data:
            cursor.close()
            error = "This email address is already registered"
            return render_template("register.html", error=error)

        try:
            # Insert new user
            ins = (
                "INSERT INTO user_account (user_ID, email, password, first_name, last_name) VALUES(%s, %s, %s, %s, %s)"
            )
            cursor.execute(ins, (user_ID, email_address, hashed_password, first_name, last_name))
            db.commit()
            cursor.close()
            session["user_ID"] = user_ID
            # Check for any active carts (shouldn't exist for new user, but just in case)
            restore_active_cart(user_ID)
            return redirect(url_for("shopping.home"))
        except Exception as e:
            cursor.close()
            error = "Registration failed. Please try again."
            return render_template("register.html", error=error)

    return render_template("register.html")


@auth_bp.route("/settings", methods=["GET", "POST"])
def settings():
    if "user_ID" not in session:
        return redirect(url_for("auth.login"))
    
    user_ID = session["user_ID"]
    
    if request.method == "POST":
        form_type = request.form.get("form_type")
        
        try:
            db = get_db()
            cursor = db.cursor()
            
            if form_type == "personal_info":
                # Update personal information
                first_name = request.form["first_name"].strip()
                last_name = request.form["last_name"].strip()
                email = request.form["email"].strip()
                timezone = request.form.get("timezone", "UTC").strip()
                
                # Validation
                if not first_name or not last_name or not email:
                    error = "All fields are required"
                    return render_settings_with_user_data(user_ID, error=error)
                
                # Validate timezone
                if not timezone:
                    timezone = "UTC"
                
                # Check if email is already used by another user
                query = "SELECT user_ID FROM user_account WHERE email = %s AND user_ID != %s"
                cursor.execute(query, (email, user_ID))
                existing_user = cursor.fetchone()
                
                if existing_user:
                    error = "This email address is already in use by another account"
                    return render_settings_with_user_data(user_ID, error=error)
                
                # Update user information including timezone
                update_query = "UPDATE user_account SET first_name = %s, last_name = %s, email = %s, timezone = %s WHERE user_ID = %s"
                cursor.execute(update_query, (first_name, last_name, email, timezone, user_ID))
                db.commit()
                
                success = "Personal information updated successfully"
                return render_settings_with_user_data(user_ID, success=success)
                
            elif form_type == "account_settings":
                # Update account settings
                username = request.form["username"].strip()
                current_password = request.form.get("current_password", "")
                new_password = request.form.get("new_password", "")
                
                # Validation
                if not username:
                    error = "Username is required"
                    return render_settings_with_user_data(user_ID, error=error)
                
                if len(username) < 3:
                    error = "Username must be at least 3 characters long"
                    return render_settings_with_user_data(user_ID, error=error)
                
                # Get current user data
                query = "SELECT password FROM user_account WHERE user_ID = %s"
                cursor.execute(query, (user_ID,))
                user_data = cursor.fetchone()
                
                # Check if username is already taken by another user
                if username != user_ID:
                    query = "SELECT user_ID FROM user_account WHERE user_ID = %s"
                    cursor.execute(query, (username,))
                    existing_user = cursor.fetchone()
                    
                    if existing_user:
                        error = "This username is already taken"
                        return render_settings_with_user_data(user_ID, error=error)
                
                # Handle password change
                if new_password:
                    if not current_password:
                        error = "Current password is required to set a new password"
                        return render_settings_with_user_data(user_ID, error=error)
                    
                    if not verify_password_bcrypt(current_password, user_data["password"]):
                        error = "Current password is incorrect"
                        return render_settings_with_user_data(user_ID, error=error)
                    
                    if len(new_password) < 6:
                        error = "New password must be at least 6 characters long"
                        return render_settings_with_user_data(user_ID, error=error)
                    
                    # Update username and password
                    hashed_password = hash_password_bcrypt(new_password)
                    update_query = "UPDATE user_account SET user_ID = %s, password = %s WHERE user_ID = %s"
                    cursor.execute(update_query, (username, hashed_password, user_ID))
                else:
                    # Update only username
                    update_query = "UPDATE user_account SET user_ID = %s WHERE user_ID = %s"
                    cursor.execute(update_query, (username, user_ID))
                
                db.commit()
                
                # Update session if username changed
                if username != user_ID:
                    session["user_ID"] = username
                
                success = "Account settings updated successfully"
                return render_settings_with_user_data(username, success=success)
            
            cursor.close()
                
        except Exception as e:
            logger.error(
                "Settings update failed",
                extra={
                    "user_id": user_ID,
                    "form_type": form_type,
                    "error": str(e),
                    "request_id": getattr(g, "request_id", None),
                },
                exc_info=True,
            )
            error = "Failed to update settings. Please try again."
            return render_settings_with_user_data(user_ID, error=error)
    
    # GET request - show settings page
    return render_settings_with_user_data(user_ID)


def render_settings_with_user_data(user_ID, success=None, error=None):
    """Helper function to render settings page with user data"""
    try:
        db = get_db()
        cursor = db.cursor()
        query = "SELECT user_ID, email, first_name, last_name, timezone FROM user_account WHERE user_ID = %s"
        cursor.execute(query, (user_ID,))
        user = cursor.fetchone()
        cursor.close()
        
        if not user:
            return redirect(url_for("auth.login"))
        
        return render_template("settings.html", user=user, success=success, error=error)
    except Exception as e:
        logger.error(
            "Failed to load user data for settings",
            extra={
                "user_id": user_ID,
                "error": str(e),
                "request_id": getattr(g, "request_id", None),
            },
            exc_info=True,
        )
        return redirect(url_for("shopping.home"))


@auth_bp.route("/logout")
def logout():
    # Only clear user authentication, preserve cart for later
    user_ID = session.get("user_ID")
    cart_ID = session.get("cart_ID")

    # Clear session but preserve cart association in database
    session.clear()

    return redirect(url_for("auth.login"))


# JWT API Endpoints
@auth_bp.route("/api/auth/login", methods=["POST"])
def api_login():
    """JWT-based login endpoint for API access"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request must be JSON"}), 400
            
        user_id = data.get("user_id", "").strip()
        password = data.get("password", "")
        
        if not user_id or not password:
            return jsonify({"error": "Username and password are required"}), 400
            
        # Authenticate user
        db = get_db()
        cursor = db.cursor()
        query = "SELECT * FROM user_account WHERE user_ID = %s"
        cursor.execute(query, (user_id,))
        user_data = cursor.fetchone()
        cursor.close()
        
        if not user_data or not verify_password_bcrypt(password, user_data["password"]):
            logger.warning(
                "API login failed - invalid credentials",
                extra={
                    "user_id": user_id,
                    "request_id": getattr(g, "request_id", None),
                },
            )
            return jsonify({"error": "Invalid username or password"}), 401
            
        # Generate JWT tokens
        from src.auth_utils import AuthUtils
        tokens = AuthUtils.generate_tokens(user_id)
        
        logger.info(
            "API login successful",
            extra={
                "user_id": user_id,
                "request_id": getattr(g, "request_id", None),
            },
        )
        
        return jsonify({
            "message": "Login successful",
            "user": {
                "user_id": user_data["user_ID"],
                "email": user_data["email"],
                "first_name": user_data["first_name"],
                "last_name": user_data["last_name"]
            },
            **tokens
        }), 200
        
    except Exception as e:
        logger.error(
            "API login failed - server error",
            extra={
                "error": str(e),
                "request_id": getattr(g, "request_id", None),
            },
            exc_info=True,
        )
        return jsonify({"error": "Login failed. Please try again."}), 500


@auth_bp.route("/api/auth/register", methods=["POST"])
def api_register():
    """JWT-based registration endpoint for API access"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request must be JSON"}), 400
            
        first_name = data.get("first_name", "").strip()
        last_name = data.get("last_name", "").strip()
        user_id = data.get("user_id", "").strip()
        password = data.get("password", "")
        email = data.get("email", "").strip()
        
        # Validation
        if not user_id or not password or not email:
            return jsonify({"error": "Email, username, and password are required"}), 400
            
        if len(user_id) < 3:
            return jsonify({"error": "Username must be at least 3 characters long"}), 400
            
        if len(password) < 6:
            return jsonify({"error": "Password must be at least 6 characters long"}), 400
            
        db = get_db()
        cursor = db.cursor()
        
        # Check if username exists
        query = "SELECT user_ID FROM user_account WHERE user_ID = %s"
        cursor.execute(query, (user_id,))
        if cursor.fetchone():
            cursor.close()
            return jsonify({"error": "This username already exists"}), 409
            
        # Check if email exists
        query = "SELECT user_ID FROM user_account WHERE email = %s"
        cursor.execute(query, (email,))
        if cursor.fetchone():
            cursor.close()
            return jsonify({"error": "This email address is already registered"}), 409
            
        # Create user
        hashed_password = hash_password_bcrypt(password)
        insert_query = (
            "INSERT INTO user_account (user_ID, email, password, first_name, last_name) "
            "VALUES (%s, %s, %s, %s, %s)"
        )
        cursor.execute(insert_query, (user_id, email, hashed_password, first_name, last_name))
        db.commit()
        cursor.close()
        
        # Generate JWT tokens
        from src.auth_utils import AuthUtils
        tokens = AuthUtils.generate_tokens(user_id)
        
        logger.info(
            "API registration successful",
            extra={
                "user_id": user_id,
                "request_id": getattr(g, "request_id", None),
            },
        )
        
        return jsonify({
            "message": "Registration successful",
            "user": {
                "user_id": user_id,
                "email": email,
                "first_name": first_name,
                "last_name": last_name
            },
            **tokens
        }), 201
        
    except Exception as e:
        logger.error(
            "API registration failed - server error",
            extra={
                "error": str(e),
                "request_id": getattr(g, "request_id", None),
            },
            exc_info=True,
        )
        return jsonify({"error": "Registration failed. Please try again."}), 500


@auth_bp.route("/api/auth/refresh", methods=["POST"])
def api_refresh():
    """Refresh JWT access token using refresh token"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request must be JSON"}), 400
            
        refresh_token = data.get("refresh_token")
        if not refresh_token:
            return jsonify({"error": "Refresh token is required"}), 400
            
        from src.auth_utils import AuthUtils
        new_tokens = AuthUtils.refresh_access_token(refresh_token)
        
        if not new_tokens:
            return jsonify({"error": "Invalid or expired refresh token"}), 401
            
        return jsonify({
            "message": "Token refreshed successfully",
            **new_tokens
        }), 200
        
    except Exception as e:
        logger.error(
            "Token refresh failed",
            extra={
                "error": str(e),
                "request_id": getattr(g, "request_id", None),
            },
            exc_info=True,
        )
        return jsonify({"error": "Token refresh failed"}), 500


@auth_bp.route("/api/auth/me", methods=["GET"])
@jwt_required
def api_me():
    """Get current user information using JWT token"""
    try:
        user_id = g.current_user_id
        
        db = get_db()
        cursor = db.cursor()
        query = "SELECT user_ID, email, first_name, last_name FROM user_account WHERE user_ID = %s"
        cursor.execute(query, (user_id,))
        user_data = cursor.fetchone()
        cursor.close()
        
        if not user_data:
            return jsonify({"error": "User not found"}), 404
            
        return jsonify({
            "user": {
                "user_id": user_data["user_ID"],
                "email": user_data["email"],
                "first_name": user_data["first_name"],
                "last_name": user_data["last_name"]
            }
        }), 200
        
    except Exception as e:
        logger.error(
            "Get user info failed",
            extra={
                "error": str(e),
                "request_id": getattr(g, "request_id", None),
            },
            exc_info=True,
        )
        return jsonify({"error": "Failed to get user information"}), 500


@auth_bp.route("/api/auth/logout", methods=["POST"])
@jwt_required
def api_logout():
    """Logout endpoint for JWT tokens (token invalidation would require blacklist)"""
    try:
        # Note: In a production system, you would typically implement a token blacklist
        # For now, we'll just return success as tokens will expire naturally
        
        logger.info(
            "API logout",
            extra={
                "user_id": g.current_user_id,
                "request_id": getattr(g, "request_id", None),
            },
        )
        
        return jsonify({
            "message": "Logout successful. Token will expire naturally."
        }), 200
        
    except Exception as e:
        logger.error(
            "API logout failed",
            extra={
                "error": str(e),
                "request_id": getattr(g, "request_id", None),
            },
            exc_info=True,
        )
        return jsonify({"error": "Logout failed"}), 500


@auth_bp.route("/api/user/preferences", methods=["GET"])
def get_user_preferences():
    """Get user preferences"""
    if "user_ID" not in session:
        return jsonify({"success": False, "message": "Not authenticated"}), 401
    
    user_id = session["user_ID"]
    db = get_db()
    cursor = db.cursor()
    
    try:
        # Get all preferences for the user
        query = """
            SELECT preference_key, preference_value, data_type 
            FROM user_preferences 
            WHERE user_id = %s
        """
        cursor.execute(query, (user_id,))
        preferences_raw = cursor.fetchall()
        
        # Convert to a dictionary
        preferences = {}
        for pref in preferences_raw:
            key = pref["preference_key"]
            value = pref["preference_value"]
            data_type = pref["data_type"]
            
            # Convert value based on data type
            if data_type == "boolean":
                preferences[key] = value.lower() == "true"
            elif data_type == "number":
                preferences[key] = float(value) if '.' in value else int(value)
            elif data_type == "json":
                import json
                preferences[key] = json.loads(value)
            else:
                preferences[key] = value
        
        cursor.close()
        return jsonify({
            "success": True,
            "preferences": preferences
        })
        
    except Exception as e:
        cursor.close()
        logger.error(f"Error getting user preferences: {e}")
        return jsonify({"success": False, "message": "Failed to get preferences"}), 500


@auth_bp.route("/api/user/preferences", methods=["POST"])
def save_user_preferences():
    """Save user preferences"""
    if "user_ID" not in session:
        return jsonify({"success": False, "message": "Not authenticated"}), 401
    
    user_id = session["user_ID"]
    data = request.get_json()
    
    if not data:
        return jsonify({"success": False, "message": "No data provided"}), 400
    
    db = get_db()
    cursor = db.cursor()
    
    try:
        # Process each preference
        for key, value in data.items():
            # Determine data type
            if isinstance(value, bool):
                data_type = "boolean"
                value_str = "true" if value else "false"
            elif isinstance(value, (int, float)):
                data_type = "number"
                value_str = str(value)
            elif isinstance(value, (list, dict)):
                data_type = "json"
                import json
                value_str = json.dumps(value)
            else:
                data_type = "string"
                value_str = str(value)
            
            # Use INSERT ... ON DUPLICATE KEY UPDATE for MySQL
            upsert_query = """
                INSERT INTO user_preferences (user_id, preference_key, preference_value, data_type, updated_at)
                VALUES (%s, %s, %s, %s, NOW())
                ON DUPLICATE KEY UPDATE
                preference_value = VALUES(preference_value),
                data_type = VALUES(data_type),
                updated_at = NOW()
            """
            cursor.execute(upsert_query, (user_id, key, value_str, data_type))
        
        db.commit()
        cursor.close()
        
        logger.info(f"User preferences saved for user {user_id}")
        
        return jsonify({
            "success": True,
            "message": "Preferences saved successfully"
        })
        
    except Exception as e:
        db.rollback()
        cursor.close()
        logger.error(f"Error saving user preferences: {e}")
        return jsonify({"success": False, "message": "Failed to save preferences"}), 500
