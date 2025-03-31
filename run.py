from app import create_app
import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)

# Get environment from FLASK_ENV, default to development
env = os.environ.get('FLASK_ENV', 'development')
app = create_app(env)

if __name__ == "__main__":
    # Only use debug mode in development
    debug = env == 'development'
    # Use 0.0.0.0 in production for proper container support
    host = "localhost" if debug else "0.0.0.0"
    port = int(os.environ.get('PORT', 5000))
    
    app.run(debug=debug, host=host, port=port)