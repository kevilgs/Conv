import os
import sys

def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEI
        base_path = sys._MEIPASS
    except Exception:
        # Running in development mode
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

def get_writable_path(relative_path):
    """Get writable path for output files and data"""
    if hasattr(sys, '_MEIPASS'):
        # Running as PyInstaller bundle - use current working directory
        base_path = os.getcwd()
    else:
        # Running in development mode
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

def get_deployment_base_path():
    """Detect if running on deployment platform and return appropriate base path"""
    # Check for Render
    if 'RENDER' in os.environ:
        return '/tmp'
    # Check for PythonAnywhere
    elif '/home/' in os.getcwd() and 'pythonanywhere' in os.getcwd():
        return '/home/kevilgs/mysite'
    # Check for Heroku
    elif 'DYNO' in os.environ:
        return '/tmp'
    # Local development
    else:
        return os.path.abspath(".")

class Config:
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-production-secret-key-render'
    DEBUG = False
    
    # Get base path for deployment vs local
    BASE_PATH = get_deployment_base_path()
    
    # File upload settings - adaptive paths
    UPLOAD_FOLDER = get_writable_path('uploads') if BASE_PATH == os.path.abspath(".") else os.path.join(BASE_PATH, 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    ALLOWED_EXTENSIONS = {'csv'}
    
    # Output settings - adaptive paths
    INTERMEDIATE_FOLDER = get_writable_path('intermediate') if BASE_PATH == os.path.abspath(".") else os.path.join(BASE_PATH, 'intermediate')
    REPORTS_FOLDER = get_writable_path('reports') if BASE_PATH == os.path.abspath(".") else os.path.join(BASE_PATH, 'reports')
    DATA_FOLDER = get_writable_path('data') if BASE_PATH == os.path.abspath(".") else os.path.join(BASE_PATH, 'data')
    
    # Data files
    PH_STATIONS_FILE = os.path.join(DATA_FOLDER, 'ph_stations.csv')
    WAGON_CLASSIFICATIONS_FILE = os.path.join(DATA_FOLDER, 'wagon_classifications.csv')
    
    @staticmethod
    def init_app():
        print(f"=== CONFIG DEBUG ===")
        print(f"BASE_PATH: {Config.BASE_PATH}")
        print(f"INTERMEDIATE_FOLDER: {Config.INTERMEDIATE_FOLDER}")
        print(f"REPORTS_FOLDER: {Config.REPORTS_FOLDER}")
        
        for folder in [Config.UPLOAD_FOLDER, Config.INTERMEDIATE_FOLDER, 
                      Config.REPORTS_FOLDER, Config.DATA_FOLDER]:
            os.makedirs(folder, exist_ok=True)
            print(f"Created/verified: {folder}")
        Config._create_default_data_files()
    
    @staticmethod 
    def _create_default_data_files():
        # Create ph_stations.csv if missing
        if not os.path.exists(Config.PH_STATIONS_FILE):
            default_stations = ['AEMD','TPHS','TSWS','GETS','AECS','GES','NSPN','SPNG','USD','WKB','DRD','GNC','EPH']
            with open(Config.PH_STATIONS_FILE, 'w', newline='', encoding='utf-8') as f:
                f.write('STATION_CODE\n')
                for station in default_stations:
                    f.write(f'{station}\n')
        
        # Create wagon_classifications.csv if missing  
        if not os.path.exists(Config.WAGON_CLASSIFICATIONS_FILE):
            default_classifications = {
                "ACT1": "ACT1", "BCACBM": "BCACBM", "BCBFG": "BCBFG", "BCFCM": "BCFCM",
                "BCN": "JUMBO", "BCNAHSM1": "JUMBO", "BCNAHSM2": "JUMBO", "BCNHL": "JUMBO", 
                "BOXN": "BOX", "BOXNEL": "BOX", "BOXNER": "BOX",
                "BTPN": "BTPN", "BTPG": "BTPG",
                "BFK": "CONT", "BKI": "CONT", "BLC": "CONT", "BLSS": "CONT",  # Added BLSS
                "BFNS": "SHRA", "BRN": "SHRA", "SHRA": "SHRA"
            }
            with open(Config.WAGON_CLASSIFICATIONS_FILE, 'w', newline='', encoding='utf-8') as f:
                f.write('WAGON_TYPE,CATEGORY\n')
                for wagon_type, category in default_classifications.items():
                    f.write(f'{wagon_type},{category}\n')

Config.init_app()

