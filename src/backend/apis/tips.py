from flask import Blueprint, request, jsonify, session
from src.database import get_db
from datetime import datetime, timedelta
import random

tips_bp = Blueprint("tips", __name__, url_prefix="/api")


@tips_bp.route("/tips/daily", methods=["GET"])
def get_daily_tip():
    """Get a random tip for the user that hasn't been shown in the last 10 days"""
    if "user_ID" not in session:
        return jsonify({"success": False, "message": "Not authenticated"})

    user_id = session["user_ID"]
        
    db = get_db()
    cursor = db.cursor()
    
    try:
        # First check if user has any tip history at all
        history_check = """
            SELECT COUNT(*) as count
            FROM user_tip_history
            WHERE user_id = %s
        """
        cursor.execute(history_check, (user_id,))
        history_count = cursor.fetchone()["count"]
        
        if history_count == 0:
            # New user - just get any random tip
            query = """
                SELECT tip_id, tip_text, tip_category
                FROM tips
                WHERE is_active = TRUE
                ORDER BY RAND()
                LIMIT 1
            """
            cursor.execute(query)
            tip = cursor.fetchone()
        else:
            # Existing user - get tips that haven't been shown in the last 10 days
            cutoff_date = datetime.now() - timedelta(days=10)
            
            query = """
                SELECT t.tip_id, t.tip_text, t.tip_category
                FROM tips t
                LEFT JOIN user_tip_history uth ON t.tip_id = uth.tip_id AND uth.user_id = %s
                WHERE t.is_active = TRUE 
                AND (uth.shown_at IS NULL OR uth.shown_at < %s)
                ORDER BY RAND()
                LIMIT 1
            """
            
            cursor.execute(query, (user_id, cutoff_date))
            tip = cursor.fetchone()
            
            if not tip:
                # User has seen all tips recently, get the oldest one
                fallback_query = """
                    SELECT t.tip_id, t.tip_text, t.tip_category
                    FROM tips t
                    JOIN user_tip_history uth ON t.tip_id = uth.tip_id
                    WHERE t.is_active = TRUE AND uth.user_id = %s
                    ORDER BY uth.shown_at ASC
                    LIMIT 1
                """
                cursor.execute(fallback_query, (user_id,))
                tip = cursor.fetchone()
        
        if tip:
            tip_id = tip["tip_id"]
            tip_text = tip["tip_text"]
            tip_category = tip["tip_category"]
            
            # Record that this tip was shown to the user
            upsert_history = """
                INSERT INTO user_tip_history (user_id, tip_id, shown_at)
                VALUES (%s, %s, NOW())
                ON DUPLICATE KEY UPDATE shown_at = NOW()
            """
            cursor.execute(upsert_history, (user_id, tip_id))
            db.commit()
            
            return jsonify({
                "success": True,
                "tip": {
                    "id": tip_id,
                    "text": tip_text,
                    "category": tip_category
                }
            })
        else:
            return jsonify({
                "success": False,
                "message": "No tips available"
            })
            
    except Exception as e:
        db.rollback()
        return jsonify({
            "success": False,
            "message": f"Failed to get tip: {str(e)}"
        })
    finally:
        cursor.close()


@tips_bp.route("/tips/stats", methods=["GET"])
def get_tip_stats():
    """Get statistics about tips for the current user"""
    if "user_ID" not in session:
        return jsonify({"success": False, "message": "Not authenticated"})

    user_id = session["user_ID"]
    
    db = get_db()
    cursor = db.cursor()
    
    try:
        # Get total tips available
        cursor.execute("SELECT COUNT(*) as total FROM tips WHERE is_active = TRUE")
        total_tips = cursor.fetchone()["total"]
        
        # Get tips seen by user
        cursor.execute("""
            SELECT COUNT(*) as seen 
            FROM user_tip_history 
            WHERE user_id = %s
        """, (user_id,))
        seen_tips = cursor.fetchone()["seen"]
        
        # Get tips seen in last 10 days
        cutoff_date = datetime.now() - timedelta(days=10)
        cursor.execute("""
            SELECT COUNT(*) as recent 
            FROM user_tip_history 
            WHERE user_id = %s AND shown_at >= %s
        """, (user_id, cutoff_date))
        recent_tips = cursor.fetchone()["recent"]
        
        return jsonify({
            "success": True,
            "stats": {
                "total_tips": total_tips,
                "tips_seen": seen_tips,
                "recent_tips": recent_tips,
                "available_tips": total_tips - recent_tips
            }
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Failed to get tip stats: {str(e)}"
        })
    finally:
        cursor.close()


@tips_bp.route("/tips/categories", methods=["GET"])
def get_tip_categories():
    """Get all available tip categories"""
    db = get_db()
    cursor = db.cursor()
    
    try:
        cursor.execute("""
            SELECT DISTINCT tip_category, COUNT(*) as count
            FROM tips 
            WHERE is_active = TRUE
            GROUP BY tip_category
            ORDER BY tip_category
        """)
        
        categories = []
        for row in cursor.fetchall():
            categories.append({
                "category": row["tip_category"],
                "count": row["count"]
            })
        
        return jsonify({
            "success": True,
            "categories": categories
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Failed to get categories: {str(e)}"
        })
    finally:
        cursor.close()