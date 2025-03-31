from flask import Flask
from flask_dotenv import DotEnv
from .config import config
from .utils import setup_logger, ensure_folder_exists
import os
from .services import init_services

def create_app(config_name='default'):
    app = Flask(__name__)
    
    # Load config
    app.config.from_object(config[config_name])
    
    # Setup logging
    setup_logger()
    
    try:
        # Load environment variables from .env file
        env = DotEnv()
        env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
        if os.path.exists(env_path):
            env.init_app(app, env_file=env_path)
        else:
            app.logger.warning('.env file not found, using default configuration')
    except Exception as e:
        app.logger.error(f'Error loading .env file: {str(e)}')

    # Ensure required directories exist
    ensure_folder_exists(app.config['UPLOAD_FOLDER'])
    ensure_folder_exists(os.path.join(app.config['UPLOAD_FOLDER'], 'audio'))
    ensure_folder_exists(os.path.join(app.config['UPLOAD_FOLDER'], 'video'))
    ensure_folder_exists(os.path.join(app.config['UPLOAD_FOLDER'], 'metadata'))

    try:
        # Initialize services
        init_services(app)
    except Exception as e:
        app.logger.error(f"Failed to initialize services: {str(e)}")
        raise

    try:
        # Register Blueprints
        from .routes import main
        app.register_blueprint(main)
    except ImportError as e:
        app.logger.error(f"Error registering blueprints: {str(e)}")
        raise

    return app
