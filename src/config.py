import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Flask configuration variables."""
    # General Config
    SECRET_KEY = os.getenv("SECRET_KEY")
    FLASK_APP = os.getenv('FLASK_APP')
    FLASK_ENV = os.getenv('FLASK_ENV')

    # Database
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = int(os.getenv("DB_PORT", 3306))
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_NAME = os.getenv("DB_NAME")

    # APIs
    NUTRITIONIX_API_ID = os.getenv("NUTRITIONIX_API_ID")
    NUTRITIONIX_API_KEY = os.getenv("NUTRITIONIX_API_KEY")
