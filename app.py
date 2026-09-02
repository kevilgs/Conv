import sys
import os
from flask import Flask, render_template, redirect, url_for
from config import Config
import webbrowser
import threading

def create_app():
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller executable
        template_folder = os.path.join(sys._MEIPASS, 'templates')
        static_folder = os.path.join(sys._MEIPASS, 'static')
        app = Flask(__name__, template_folder=template_folder, static_folder=static_folder)
    else:
        # Running normally
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
        return redirect(url_for('upload.upload'))

    return app


def enable_quit_on_tab_close(app):
    """Stop the server when the browser tab is closed.

    The exe runs with --noconsole, so there is no window to close to stop it.
    Only used for the desktop run, not when a WSGI server imports `application`.
    """
    quit_timer = {'t': None}

    @app.route('/closing', methods=['POST'])
    def closing():
        # The page is going away. That also happens on a normal navigation,
        # so give the next page a few seconds to appear before quitting.
        quit_timer['t'] = threading.Timer(5.0, lambda: os._exit(0))
        quit_timer['t'].start()
        return '', 204

    @app.route('/hello', methods=['POST'])
    def hello():
        # A page just loaded, so it was a navigation, not a close.
        if quit_timer['t']:
            quit_timer['t'].cancel()
        return '', 204

    return app


application = create_app()

if __name__ == '__main__':
    def open_browser():
        webbrowser.open_new("http://127.0.0.1:5000/")  # Change port if needed

    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        threading.Timer(1.0, open_browser).start()
        
    app = create_app()
    enable_quit_on_tab_close(app)
    app.run(debug=True)