import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

class Config:
    """Base configuration."""
    SECRET_KEY = os.getenv('SECRET_KEY', 'a-default-secret-key-for-development')
    
    # Database configuration
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = int(os.getenv('DB_PORT', 8889))
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'root')
    DB_NAME = os.getenv('DB_NAME', 'hacknyu25')

    # Nutritionix API configuration
    NUTRITIONIX_API_ID = os.getenv('NUTRITIONIX_API_ID')
    NUTRITIONIX_API_KEY = os.getenv('NUTRITIONIX_API_KEY')