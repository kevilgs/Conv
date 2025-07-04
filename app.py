from flask import Flask, render_template
from config import Config
import webbrowser
import threading

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

application = create_app()

if __name__ == '__main__':
    def open_browser():
        webbrowser.open_new("http://127.0.0.1:5000/")  # Change port if needed

    threading.Timer(1.0, open_browser).start()
    app = create_app()
    app.run(debug=True)