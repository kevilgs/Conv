import pandas as pd
import os
from config import Config

class WagonClassifier:
    def __init__(self):
        self.classification_map = {}
        self.csv_path = Config.WAGON_CLASSIFICATIONS_FILE
        self._load_classification_data()
    
    def _load_classification_data(self):
        """Load wagon classification mapping from CSV"""
        try:
            if os.path.exists(self.csv_path):
                df = pd.read_csv(self.csv_path)
                # Create mapping dictionary: WAGON_TYPE -> CATEGORY
                self.classification_map = dict(zip(df['WAGON_TYPE'], df['CATEGORY']))
            else:
                # Fallback: create the mapping manually if file doesn't exist
                self.classification_map = {
                    "ACT1": "ACT1",
                    "BCACBM": "BCACBM",
                    "BCBFG": "BCBFG",
                    "BCFCM": "BCFCM",
                    "BCN": "JUMBO",
                    "BCNAHSM1": "JUMBO",
                    "BCNAHSM2": "JUMBO",
                    "BCNHL": "JUMBO",
                    "BCNM": "JUMBO",
                    "BFK": "CONT",
                    "BFKN": "CONT",
                    "BFNS": "SHRA",
                    "BFNS22.9": "SHRA",
                    "BFNSM": "SHRA",
                    "BFNSM1": "SHRA",
                    "BFNV": "SHRA",
                    "BKI": "CONT",
                    "BLC": "CONT",
                    "BLL": "CONT",
                    "BLLM": "CONT",
                    "BLSS": "CONT",
                    "BOSM": "SHRA",
                    "BOST": "SHRA",
                    "BOXK": "CONT",
                    "BOXN": "BOX",
                    "BOXNEL": "BOX",
                    "BOXNER": "BOX",
                    "BOXNHL": "BOX",
                    "BOXNHL25T": "BOX",
                    "BOXNR": "BOX",
                    "BOXNS": "BOX",
                    "BRN": "SHRA",
                    "BRN22.9": "SHRA",
                    "BTFNL": "BTPN",
                    "BTPG": "BTPG",
                    "BTPGN": "BTPG",
                    "BTPN": "BTPN",
                    "MYLY": "MYLY",
                    "NMG": "NMG",
                    "NMGHS": "NMG",
                    "SHRA": "SHRA",
                    "SHRN": "SHRA",
                    "TURRRRRRR": "JUMBOOOO"
                }
                # Create the CSV file with fallback data
                self._save_to_csv()
                
        except Exception as e:
            print(f"Error loading wagon classification data: {e}")
            self.classification_map = {}
    
    def classify_wagon(self, wagon_type):
        """Get classification for a wagon type"""
        if pd.isna(wagon_type) or wagon_type == '':
            return ''
        
        # Convert to string and strip whitespace
        wagon_type = str(wagon_type).strip()
        
        # Return classification if found, otherwise return the original wagon type
        return self.classification_map.get(wagon_type, wagon_type)
    
    def add_custom_classifications(self, custom_classifications_dict):
        """Add multiple custom classifications and save to CSV"""
        if not custom_classifications_dict:
            return
        
        # Add to memory
        self.classification_map.update(custom_classifications_dict)
        
        # Save to CSV file
        self._save_to_csv()
        
        print(f"Added {len(custom_classifications_dict)} custom classifications to CSV")
    
    def _save_to_csv(self):
        """Save current classification map to CSV file"""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.csv_path), exist_ok=True)
            
            # Convert dictionary to DataFrame
            df = pd.DataFrame(list(self.classification_map.items()), 
                            columns=['WAGON_TYPE', 'CATEGORY'])
            
            # Sort by WAGON_TYPE for better organization
            df = df.sort_values('WAGON_TYPE')
            
            # Save to CSV
            df.to_csv(self.csv_path, index=False)
            
        except Exception as e:
            print(f"Error saving wagon classifications to CSV: {e}")
    
    def get_all_classifications(self):
        """Get all current classifications"""
        return self.classification_map.copy()