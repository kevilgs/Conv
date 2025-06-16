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

class Config:
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    
    # File upload settings
    UPLOAD_FOLDER = get_writable_path('uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'csv'}
    
    # Output settings (writable directories)
    INTERMEDIATE_FOLDER = get_writable_path('intermediate')
    REPORTS_FOLDER = get_writable_path('reports')
    DATA_FOLDER = get_writable_path('data')  # Now writable!
    
    # Data files (now in writable data folder)
    PH_STATIONS_FILE = os.path.join(DATA_FOLDER, 'ph_stations.csv')
    WAGON_CLASSIFICATIONS_FILE = os.path.join(DATA_FOLDER, 'wagon_classifications.csv')
    
    # Create directories if they don't exist
    @staticmethod
    def init_app():
        for folder in [Config.UPLOAD_FOLDER, Config.INTERMEDIATE_FOLDER, Config.REPORTS_FOLDER, Config.DATA_FOLDER]:
            os.makedirs(folder, exist_ok=True)
        
        # Create default CSV files if they don't exist
        Config._create_default_data_files()
    
    @staticmethod
    def _create_default_data_files():
        """Create default CSV files ONLY if they don't exist"""
        # Create ph_stations.csv ONLY if missing
        if not os.path.exists(Config.PH_STATIONS_FILE):
            default_stations = ['AEMD','TPHS','TSWS','GETS','AECS','GES','NSPN','SPNG','USD','WKB','DRD','GNC','EPH']
            with open(Config.PH_STATIONS_FILE, 'w', newline='', encoding='utf-8') as f:
                f.write('STATION_CODE\n')
                for station in default_stations:
                    f.write(f'{station}\n')
            print(f"Created default PH stations file: {Config.PH_STATIONS_FILE}")
        
        # Create wagon_classifications.csv ONLY if missing
        if not os.path.exists(Config.WAGON_CLASSIFICATIONS_FILE):
            # Copy your complete classifications from the existing file
            default_classifications = {
                "ACT1": "ACT1", "BCACBM": "BCACBM", "BCBFG": "BCBFG", "BCFCM": "BCFCM",
                "BCN": "JUMBO", "BCNAHSM1": "JUMBO", "BCNAHSM2": "JUMBO", "BCNHL": "JUMBO", "BCNM": "JUMBO",
                "BFK": "CONT", "BFKN": "CONT", "BKI": "CONT", "BLC": "CONT", "BLL": "CONT", "BLLM": "CONT", "BLSS": "CONT", "BOXK": "CONT",
                "BFNS": "SHRA", "BFNS22.9": "SHRA", "BFNSM": "SHRA", "BFNSM1": "SHRA", "BFNV": "SHRA", "BOSM": "SHRA", "BOST": "SHRA", "BRN": "SHRA", "BRN22.9": "SHRA", "SHRA": "SHRA", "SHRN": "SHRA",
                "BOXN": "BOX", "BOXNEL": "BOX", "BOXNER": "BOX", "BOXNHL": "BOX", "BOXNHL25T": "BOX", "BOXNR": "BOX", "BOXNS": "BOX",
                "BTPLN": "BTPN", "BTPN": "BTPN",
                "BTPG": "BTPG", "BTPGN": "BTPG",
                "BROO": "HYNL", "MYLY": "MYLY", "NMG": "NMG", "NMGHS": "NMG"
            }
            with open(Config.WAGON_CLASSIFICATIONS_FILE, 'w', newline='', encoding='utf-8') as f:
                f.write('WAGON_TYPE,CATEGORY\n')
                for wagon_type, category in default_classifications.items():
                    f.write(f'{wagon_type},{category}\n')
            print(f"Created default wagon classifications file: {Config.WAGON_CLASSIFICATIONS_FILE}")
        else:
            print(f"Using existing wagon classifications file: {Config.WAGON_CLASSIFICATIONS_FILE}")

# Initialize directories when config is imported
Config.init_app()

