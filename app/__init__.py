from flask import Flask
from flask_dotenv import DotEnv
import os

def create_app():
    app = Flask(__name__)
    
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

    # Create 'uploads/' directory if it doesn't exist
    upload_folder = os.path.join(os.getcwd(), 'uploads')  # Full path to 'uploads/'
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)  # Create the directory

    # Configure Flask upload folder
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'super-secret-key')
    app.config['UPLOAD_FOLDER'] = upload_folder  # Set the upload folder

    try:
        # Register Blueprints
        from .routes import main
        app.register_blueprint(main)
    except ImportError as e:
        app.logger.error(f"Error registering blueprints: {str(e)}")
        raise

    return app
