from flask import Flask, render_template
from config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize directories
    Config.init_app()
    
    # Register blueprints
    from routes.upload_route import upload_bp
    from routes.process_route import process_bp
    from routes.download_route import download_bp
    
    app.register_blueprint(upload_bp)
    app.register_blueprint(process_bp)
    app.register_blueprint(download_bp)
    
    # Main route
    @app.route('/')
    def index():
        return render_template('index.html')
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)