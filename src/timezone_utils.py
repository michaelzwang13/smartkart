"""
Timezone utility functions for handling user-specific timezone conversions.
"""

from datetime import datetime, date
import pytz
from typing import Optional, Union
from src.database import get_db
from src.logging_config import get_logger

logger = get_logger("preppr.timezone_utils")

def get_user_timezone(user_id: str) -> str:
    """
    Get the timezone for a specific user from the database.
    
    Args:
        user_id: The user's ID
        
    Returns:
        str: The user's timezone (defaults to UTC if not found)
    """
    try:
        connection = get_db()
        cursor = connection.cursor()
        
        cursor.execute(
            "SELECT timezone FROM user_account WHERE user_ID = %s",
            (user_id,)
        )
        
        result = cursor.fetchone()
        cursor.close()
        
        if result and result['timezone']:
            return result['timezone']
        else:
            logger.warning(f"No timezone found for user {user_id}, defaulting to UTC")
            return 'UTC'
            
    except Exception as e:
        logger.error(f"Error getting timezone for user {user_id}: {str(e)}")
        return 'UTC'

def get_user_current_date(user_id: str) -> date:
    """
    Get the current date in the user's timezone.
    
    Args:
        user_id: The user's ID
        
    Returns:
        date: Current date in user's timezone
    """
    try:
        user_timezone = get_user_timezone(user_id)
        tz = pytz.timezone(user_timezone)
        
        # Get current UTC time and convert to user's timezone
        utc_now = datetime.utcnow().replace(tzinfo=pytz.UTC)
        user_now = utc_now.astimezone(tz)
        
        return user_now.date()
        
    except Exception as e:
        logger.error(f"Error getting current date for user {user_id}: {str(e)}")
        # Fallback to UTC
        return datetime.utcnow().date()

def get_user_current_datetime(user_id: str) -> datetime:
    """
    Get the current datetime in the user's timezone.
    
    Args:
        user_id: The user's ID
        
    Returns:
        datetime: Current datetime in user's timezone
    """
    try:
        user_timezone = get_user_timezone(user_id)
        tz = pytz.timezone(user_timezone)
        
        # Get current UTC time and convert to user's timezone
        utc_now = datetime.utcnow().replace(tzinfo=pytz.UTC)
        user_now = utc_now.astimezone(tz)
        
        return user_now
        
    except Exception as e:
        logger.error(f"Error getting current datetime for user {user_id}: {str(e)}")
        # Fallback to UTC
        return datetime.utcnow().replace(tzinfo=pytz.UTC)

def convert_date_to_user_timezone(date_obj: Union[date, datetime], user_id: str) -> Union[date, datetime]:
    """
    Convert a UTC date/datetime to the user's timezone.
    
    Args:
        date_obj: The date or datetime object to convert (assumed to be UTC)
        user_id: The user's ID
        
    Returns:
        date or datetime: The converted date/datetime in user's timezone
    """
    try:
        user_timezone = get_user_timezone(user_id)
        tz = pytz.timezone(user_timezone)
        
        if isinstance(date_obj, date) and not isinstance(date_obj, datetime):
            # If it's just a date, convert to datetime at midnight UTC first
            dt = datetime.combine(date_obj, datetime.min.time())
            dt = dt.replace(tzinfo=pytz.UTC)
            user_dt = dt.astimezone(tz)
            return user_dt.date()
        elif isinstance(date_obj, datetime):
            # Handle datetime conversion
            if date_obj.tzinfo is None:
                # Assume UTC if no timezone info
                dt = date_obj.replace(tzinfo=pytz.UTC)
            else:
                dt = date_obj
            
            user_dt = dt.astimezone(tz)
            return user_dt
        else:
            return date_obj
            
    except Exception as e:
        logger.error(f"Error converting date to user timezone for user {user_id}: {str(e)}")
        return date_obj

def is_date_today_for_user(check_date: date, user_id: str) -> bool:
    """
    Check if the given date is today in the user's timezone.
    
    Args:
        check_date: The date to check
        user_id: The user's ID
        
    Returns:
        bool: True if the date is today in user's timezone
    """
    try:
        user_today = get_user_current_date(user_id)
        return check_date == user_today
        
    except Exception as e:
        logger.error(f"Error checking if date is today for user {user_id}: {str(e)}")
        return False

def get_user_date_range_utc(user_id: str, start_date: date, end_date: date) -> tuple[datetime, datetime]:
    """
    Convert user's local date range to UTC datetime range.
    This is useful for database queries where we need to find all records
    that fall within a user's local date range.
    
    Args:
        user_id: The user's ID
        start_date: Start date in user's timezone
        end_date: End date in user's timezone
        
    Returns:
        tuple: (start_datetime_utc, end_datetime_utc)
    """
    try:
        user_timezone = get_user_timezone(user_id)
        tz = pytz.timezone(user_timezone)
        
        # Convert start_date to start of day in user's timezone
        start_dt_local = tz.localize(datetime.combine(start_date, datetime.min.time()))
        start_dt_utc = start_dt_local.astimezone(pytz.UTC)
        
        # Convert end_date to end of day in user's timezone
        end_dt_local = tz.localize(datetime.combine(end_date, datetime.max.time()))
        end_dt_utc = end_dt_local.astimezone(pytz.UTC)
        
        return start_dt_utc, end_dt_utc
        
    except Exception as e:
        logger.error(f"Error getting date range UTC for user {user_id}: {str(e)}")
        # Fallback to UTC dates
        start_dt_utc = datetime.combine(start_date, datetime.min.time()).replace(tzinfo=pytz.UTC)
        end_dt_utc = datetime.combine(end_date, datetime.max.time()).replace(tzinfo=pytz.UTC)
        return start_dt_utc, end_dt_utc

def format_datetime_for_user(dt: datetime, user_id: str, format_string: str = "%Y-%m-%d %H:%M") -> str:
    """
    Format a datetime object for display to the user in their timezone.
    
    Args:
        dt: The datetime object to format (assumed to be UTC)
        user_id: The user's ID
        format_string: The format string for strftime
        
    Returns:
        str: Formatted datetime string in user's timezone
    """
    try:
        user_dt = convert_date_to_user_timezone(dt, user_id)
        if isinstance(user_dt, datetime):
            return user_dt.strftime(format_string)
        else:
            return str(user_dt)
            
    except Exception as e:
        logger.error(f"Error formatting datetime for user {user_id}: {str(e)}")
        return dt.strftime(format_string) if isinstance(dt, datetime) else str(dt)

def get_timezone_display_name(timezone_str: str) -> str:
    """
    Get a human-readable display name for a timezone.
    
    Args:
        timezone_str: The timezone string (e.g., 'America/New_York')
        
    Returns:
        str: Human-readable timezone name
    """
    timezone_names = {
        'America/New_York': 'Eastern Time (New York)',
        'America/Chicago': 'Central Time (Chicago)',
        'America/Denver': 'Mountain Time (Denver)',
        'America/Los_Angeles': 'Pacific Time (Los Angeles)',
        'America/Anchorage': 'Alaska Time (Anchorage)',
        'Pacific/Honolulu': 'Hawaii Time (Honolulu)',
        'America/Toronto': 'Eastern Time (Toronto)',
        'America/Vancouver': 'Pacific Time (Vancouver)',
        'Europe/London': 'Greenwich Mean Time (London)',
        'Europe/Paris': 'Central European Time (Paris)',
        'Europe/Berlin': 'Central European Time (Berlin)',
        'Europe/Rome': 'Central European Time (Rome)',
        'Europe/Madrid': 'Central European Time (Madrid)',
        'Europe/Amsterdam': 'Central European Time (Amsterdam)',
        'Europe/Stockholm': 'Central European Time (Stockholm)',
        'Europe/Moscow': 'Moscow Time (Moscow)',
        'Asia/Tokyo': 'Japan Standard Time (Tokyo)',
        'Asia/Shanghai': 'China Standard Time (Shanghai)',
        'Asia/Seoul': 'Korea Standard Time (Seoul)',
        'Asia/Hong_Kong': 'Hong Kong Time (Hong Kong)',
        'Asia/Singapore': 'Singapore Standard Time (Singapore)',
        'Asia/Dubai': 'Gulf Standard Time (Dubai)',
        'Asia/Kolkata': 'India Standard Time (Mumbai)',
        'Asia/Bangkok': 'Indochina Time (Bangkok)',
        'Australia/Sydney': 'Australian Eastern Time (Sydney)',
        'Australia/Melbourne': 'Australian Eastern Time (Melbourne)',
        'Australia/Perth': 'Australian Western Time (Perth)',
        'Pacific/Auckland': 'New Zealand Standard Time (Auckland)',
        'UTC': 'Coordinated Universal Time (UTC)'
    }
    
    return timezone_names.get(timezone_str, timezone_str)