import os

class Config:
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    
    # File upload settings
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'csv'}
    
    # Output settings
    INTERMEDIATE_FOLDER = 'intermediate'
    REPORTS_FOLDER = 'reports'
    
    # Create directories if they don't exist
    @staticmethod
    def init_app():
        for folder in [Config.UPLOAD_FOLDER, Config.INTERMEDIATE_FOLDER, Config.REPORTS_FOLDER]:
            os.makedirs(folder, exist_ok=True)

# Initialize directories when config is imported
Config.init_app()

