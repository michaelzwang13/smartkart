import os
from src import create_app

# Create the application instance using the factory
app = create_app()

if __name__ == '__main__':
    # Get configuration from environment variables with sensible defaults
    host = os.getenv('FLASK_HOST', '0.0.0.0')  # Default to 0.0.0.0 for Docker compatibility
    port = int(os.getenv('FLASK_PORT', '8000'))  # Default to 8000 to match Dockerfile
    debug = os.getenv('FLASK_DEBUG', 'True').lower() in ['true', '1', 'yes', 'on']
    
    app.run(host=host, port=port, debug=debug)
