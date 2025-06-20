import pandas as pd
from collections import defaultdict, Counter
from config import Config

class ReportDataProcessor:
    def __init__(self):
        # Classifications to process for details with proper mapping
        self.classification_mapping = {
            'JUMBO': 'JUMBO',
            'BOX': 'BOXN',      # BOX in intermediate maps to BOXN in final
            'BOXN': 'BOXN',     # Support both formats
            'BTPN': 'BTPN',
            'BTPG': 'BTPG',     
            'SHRA': 'SHRA'
        }
        
        # Classifications we want in details
        self.detail_classifications = ['JUMBO', 'BOX', 'BOXN', 'BTPN', 'BTPG', 'SHRA', 'CONT']  # Add 'CONT'
    
    def process_handedover_data(self, df):
        """Process handedover data grouped by IC STTN (Copy)"""
        handedover_data = {}
        
        # Group by IC STTN (Copy)
        grouped = df.groupby('IC STTN (Copy)')
        
        for station, station_data in grouped:
            station_info = {
                'ic_sttn': station,
                'details': self._calculate_handedover_details(station_data)
            }
            handedover_data[station] = station_info
        
        return handedover_data
    
    def process_takenover_data(self, df):
        """Process takenover data grouped by IC STTN"""
        takenover_data = {}
        
        # Group by IC STTN
        grouped = df.groupby('IC STTN')
        
        for station, station_data in grouped:
            station_info = {
                'ic_sttn': station,
                'details': self._calculate_takenover_details(station_data)
            }
            takenover_data[station] = station_info
        
        return takenover_data
    
    def _calculate_handedover_details(self, station_data):
        """Calculate detailed breakdown for handedover section"""
        details = {
            'JUMBO': [],
            'BOXN': [],  # This will contain both BOX and BOXN from intermediate
            'BTPN': [],
            'BTPG': [],  # Added BTPG for completeness
            'SHRA': [],
            'CONT': [],  # Add this line
            'OTHERS': [] , # For any other classifications not in detail_classifications
            'EMPTIES': [] , # For empty stations
            'JUMBO_LE': [],
            'BOXN_LE': [],  # This will contain BOXN from intermediate
            'BTPN_LE': [],
            'DIESEL':0,
            'NO_OF_TRAINS': '',
            'CONT_COUNT': 0
        }
        
        # # Debug: Print what classifications we have
        # print(f"Handedover classifications available: {station_data['HANDEDOVER CLASSIFICATION'].unique()}")
        # print(f"Handedover L/E values: {station_data['HANDED OVER L/E'].unique()}")
        
        for classification in self.detail_classifications:
            # Filter by classification and L/E = "L"
            if classification == 'CONT':
                # For CONT, include both L and E
                filtered_data = station_data[
                    (station_data['HANDEDOVER CLASSIFICATION'] == classification) &
                    (station_data['HANDED OVER L/E'].isin(['L', 'E']))
                ]
            else:
                # For others, only L
                filtered_data = station_data[
                    (station_data['HANDEDOVER CLASSIFICATION'] == classification) &
                    (station_data['HANDED OVER L/E'] == 'L')
                ]
            
            # print(f"For {classification}: found {len(filtered_data)} rows")
            
            if not filtered_data.empty:
                # Collect HANDED OVER STTN TO values
                sttn_to_values = filtered_data['HANDED OVER STTN TO'].tolist()
                # print(f"Stations for {classification}: {sttn_to_values}")
                
                # Count occurrences of each station
                sttn_counts = Counter(sttn_to_values)
                
                # Format as "STTN" or "STTN(count)"
                formatted_sttns = []
                for sttn, count in sttn_counts.items():
                    if count == 1:
                        formatted_sttns.append(str(sttn))
                    else:
                        formatted_sttns.append(f"{sttn}({count})")
                
                # Map to correct final report category
                if classification in ['BOX', 'BOXN']:
                    details['BOXN'].extend(formatted_sttns)
                elif classification == 'JUMBO':
                    details['JUMBO'].extend(formatted_sttns)
                elif classification == 'BTPN':
                    details['BTPN'].extend(formatted_sttns)
                elif classification == 'BTPG':
                    details['BTPG'].extend(formatted_sttns)
                elif classification == 'SHRA':
                    details['SHRA'].extend(formatted_sttns)
                elif classification == 'CONT':
                    details['CONT'].extend(formatted_sttns)
        
        # Calculate OTHERS - all classifications not in main categories
        others_classifications = []
        for classification in station_data['HANDEDOVER CLASSIFICATION'].unique():
            if classification not in ['JUMBO', 'BOX', 'BOXN', 'BTPN', 'BTPG', 'CONT', 'SHRA']:
                others_classifications.append(classification)

        for classification in others_classifications:
            filtered_data = station_data[
                (station_data['HANDEDOVER CLASSIFICATION'] == classification) &
                (station_data['HANDED OVER L/E'] == 'L')
            ]
            
            if not filtered_data.empty:
                sttn_to_values = filtered_data['HANDED OVER STTN TO'].tolist()
                sttn_counts = Counter(sttn_to_values)
                
                for sttn, count in sttn_counts.items():
                    if count == 1:
                        details['OTHERS'].append(f"{classification}[{sttn}]")
                    else:
                        details['OTHERS'].append(f"{classification}[{sttn}]-{count}")
        # Filter for empties BUT exclude CONT wagon types
        empties_data = station_data[
            (station_data['HANDED OVER L/E'] == 'E') & 
            (station_data['HANDEDOVER CLASSIFICATION'] != 'CONT')  # Exclude CONT
            ]

        if not empties_data.empty:
            type_counts = Counter(empties_data['HANDED OVER TYPE'])
            for wagon_type, count in type_counts.items():
                if count == 1:
                    details['EMPTIES'].append(wagon_type)
                else:
                    details['EMPTIES'].append(f"{wagon_type}-{count}")
        # Calculate L+E counts for handedover
        details['JUMBO_LE'] = self._calculate_le_counts(station_data, 'JUMBO', is_handedover=True)
        details['BOXN_LE'] = self._calculate_le_counts(station_data, 'BOX', is_handedover=True)  # Use BOX from intermediate
        details['BTPN_LE'] = self._calculate_le_counts(station_data, 'BTPN', is_handedover=True)
        # Calculate CONT count
        details['CONT_COUNT'] = self._calculate_cont_count(station_data, is_handedover=True)
        # Calculate DIESEL count
        details['DIESEL'] = self._calculate_diesel_count(station_data, is_handedover=True)
        # Calculate NO_OF_TRAINS in A/B format
        details['NO_OF_TRAINS'] = self._calculate_trains_count(station_data, is_handedover=True)
        
        return details
    
    def _calculate_takenover_details(self, station_data):
        """Calculate detailed breakdown for takenover section"""
        details = {
            'JUMBO': [],
            'BOXN': [],  # This will contain both BOX and BOXN from intermediate
            'BTPN': [],
            'BTPG': [],  # Added BTPG for completeness
            'SHRA': [],
            'CONT': [],  # Add this line
            'OTHERS': [],  # For any other classifications not in detail_classifications
            'EMPTIES': [],  # For empty stations
            'JUMBO_LE':[],
            'BTPN_LE':[],
            'BOXN_PH_OTH': '',  # Add this line
            'DIESEL':0,
            'NO_OF_TRAINS': '',
            'CONT_COUNT': 0
        }
        
        # # Debug: Print what classifications we have
        # print(f"Takenover classifications available: {station_data['TAKENOVER CLASSIFICATION'].unique()}")
        # print(f"Takenover L/E values: {station_data['TAKEN OVER L/E'].unique()}")
        
        for classification in self.detail_classifications:
            # Filter by classification and L/E = "L"
            filtered_data = station_data[
                (station_data['TAKENOVER CLASSIFICATION'] == classification) &
                (station_data['TAKEN OVER L/E'] == 'L')
            ]
            
            # print(f"For {classification}: found {len(filtered_data)} rows")
            
            if not filtered_data.empty:
                # Collect TAKEN OVER STTN TO values
                sttn_to_values = filtered_data['TAKEN OVER STTN TO'].tolist()
                # print(f"Stations for {classification}: {sttn_to_values}")
                
                # Count occurrences of each station
                sttn_counts = Counter(sttn_to_values)
                
                # Format as "STTN" or "STTN(count)"
                formatted_sttns = []
                for sttn, count in sttn_counts.items():
                    if count == 1:
                        formatted_sttns.append(str(sttn))
                    else:
                        formatted_sttns.append(f"{sttn}({count})")
                
                # Map to correct final report category
                if classification in ['BOX', 'BOXN']:
                    details['BOXN'].extend(formatted_sttns)
                elif classification == 'JUMBO':
                    details['JUMBO'].extend(formatted_sttns)
                elif classification == 'BTPN':
                    details['BTPN'].extend(formatted_sttns)
                elif classification == 'BTPG':
                    details['BTPG'].extend(formatted_sttns)
                elif classification == 'SHRA':
                    details['SHRA'].extend(formatted_sttns)
                elif classification == 'CONT':
                    details['CONT'].extend(formatted_sttns)
        
        # Calculate OTHERS - all classifications not in main categories
        others_classifications = []
        for classification in station_data['TAKENOVER CLASSIFICATION'].unique():
            if classification not in ['JUMBO', 'BOX', 'BOXN', 'BTPN', 'BTPG', 'CONT', 'SHRA']:
                others_classifications.append(classification)

        for classification in others_classifications:
            filtered_data = station_data[
                (station_data['TAKENOVER CLASSIFICATION'] == classification) &
                (station_data['TAKEN OVER L/E'] == 'L')
            ]
            
            if not filtered_data.empty:
                sttn_to_values = filtered_data['TAKEN OVER STTN TO'].tolist()
                sttn_counts = Counter(sttn_to_values)
                
                for sttn, count in sttn_counts.items():
                    if count == 1:
                        details['OTHERS'].append(f"{classification}[{sttn}]")
                    else:
                        details['OTHERS'].append(f"{classification}[{sttn}]-{count}")
        
        # Calculate EMPTIES - group by TAKEN OVER TYPE with L/E = E
        empties_data = station_data[(station_data['TAKEN OVER L/E'] == 'E') &
                                    (station_data['TAKENOVER CLASSIFICATION'] != 'CONT')]  # Exclude CONT
        if not empties_data.empty:
            type_counts = Counter(empties_data['TAKEN OVER TYPE'])
            for wagon_type, count in type_counts.items():
                if count == 1:
                    details['EMPTIES'].append(wagon_type)
                else:
                    details['EMPTIES'].append(f"{wagon_type}-{count}")
        
        # Calculate L+E counts for takenover (exclude BOXN)
        details['JUMBO_LE'] = self._calculate_le_counts(station_data, 'JUMBO', is_handedover=False)
        details['BTPN_LE'] = self._calculate_le_counts(station_data, 'BTPN', is_handedover=False)
        # Calculate CONT count
        details['CONT_COUNT'] = self._calculate_cont_count(station_data, is_handedover=False)
        # Calculate BOXN_PH_OTH - this will contain BOXN from intermediate
        details['BOXN_PH_OTH'] = self._calculate_boxn_ph_oth_counts(station_data)  # Use BOX from intermediate
        # Calculate DIESEL count
        details['DIESEL'] = self._calculate_diesel_count(station_data, is_handedover=False)
        # Calculate NO_OF_TRAINS in A/B format
        details['NO_OF_TRAINS'] = self._calculate_trains_count(station_data, is_handedover=False)
        return details
    
    def _calculate_le_counts(self, station_data, classification, is_handedover=True):
        """Calculate L+E count for a specific classification"""
        if is_handedover:
            class_col = 'HANDEDOVER CLASSIFICATION'
            le_col = 'HANDED OVER L/E'
        else:
            class_col = 'TAKENOVER CLASSIFICATION'
            le_col = 'TAKEN OVER L/E'
        
        # Get data for this classification
        class_data = station_data[station_data[class_col] == classification]
        
        if class_data.empty:
            return "0+0"
        
        # Count L and E separately
        l_count = len(class_data[class_data[le_col] == 'L'])
        e_count = len(class_data[class_data[le_col] == 'E'])
        
        return f"{l_count}+{e_count}"
    
    def get_stations_in_order(self, df):
        """Get stations in the order they appear in the intermediate file"""
        # Get handedover stations in order of appearance
        handedover_stations = []
        seen_handed = set()
        for station in df['IC STTN (Copy)'].dropna():
            if station not in seen_handed:
                handedover_stations.append(station)
                seen_handed.add(station)
        
        # Get takenover stations in order of appearance
        takenover_stations = []
        seen_taken = set()
        for station in df['IC STTN'].dropna():
            if station not in seen_taken:
                takenover_stations.append(station)
                seen_taken.add(station)
        
        return handedover_stations, takenover_stations
    
    def calculate_totals(self, data_dict, stations_list, is_handedover=True):
        """Calculate totals for given stations"""
        totals = {
            'NO_OF_TRAINS': [0,0],      # Set to 0 until logic is implemented
            'DIESEL': 0,            # Set to 0 until logic is implemented
            'JUMBO_LE': [0, 0],
            'BOXN_LE': [0, 0],
            'BOXN_PH_OTH': [0, 0],
            'BTPN_LE': [0, 0],
            'CONT': 0               # Set to 0 until logic is implemented
        }
        
        for station in stations_list:
            if station in data_dict:
                details = data_dict[station]['details']
                
                # TODO: Add NO_OF_TRAINS logic when ready
                # totals['NO_OF_TRAINS'] += 1  # Remove this line
                
                # Count DIESEL
                if 'DIESEL' in details:
                    totals['DIESEL'] += details['DIESEL']  # Uncomment this line
                
                # Sum L+E counts
                if 'JUMBO_LE' in details and details['JUMBO_LE']:
                    le_parts = details['JUMBO_LE'].split('+')
                    if len(le_parts) == 2:
                        totals['JUMBO_LE'][0] += int(le_parts[0])
                        totals['JUMBO_LE'][1] += int(le_parts[1])
                
                if is_handedover:
                    if 'BOXN_LE' in details and details['BOXN_LE']:
                        le_parts = details['BOXN_LE'].split('+')
                        if len(le_parts) == 2:
                            totals['BOXN_LE'][0] += int(le_parts[0])
                            totals['BOXN_LE'][1] += int(le_parts[1])
                else:
                    if 'BOXN_PH_OTH' in details and details['BOXN_PH_OTH']:
                        ph_oth_parts = details['BOXN_PH_OTH'].split('+')
                        if len(ph_oth_parts) == 2:
                            totals['BOXN_PH_OTH'][0] += int(ph_oth_parts[0])  # PH count
                            totals['BOXN_PH_OTH'][1] += int(ph_oth_parts[1])  # OTH count
                
                if 'BTPN_LE' in details and details['BTPN_LE']:
                    le_parts = details['BTPN_LE'].split('+')
                    if len(le_parts) == 2:
                        totals['BTPN_LE'][0] += int(le_parts[0])
                        totals['BTPN_LE'][1] += int(le_parts[1])
                
                
                if 'CONT_COUNT' in details:
                     totals['CONT'] += (details['CONT_COUNT'])
        
                # Count NO OF TRAINS (sum the A and B parts separately)
                if 'NO_OF_TRAINS' in details and details['NO_OF_TRAINS']:
                    train_parts = details['NO_OF_TRAINS'].split('/')
                    if len(train_parts) == 2:
                        totals['NO_OF_TRAINS'][0] += int(train_parts[0])  # A total
                        totals['NO_OF_TRAINS'][1] += int(train_parts[1])  # B total
    
        return totals
    
    def _calculate_diesel_count(self, station_data, is_handedover=True):
        """Calculate diesel count for a station based on loco type starting with WD"""
        if is_handedover:
            loco_col = 'HANDED OVER LOCO TYPE'
        else:
            loco_col = 'TAKEN OVER LOCO TYPE'  # Changed from 'TAKENOVER LOCO TYPE'
    
        # Check if column exists
        if loco_col not in station_data.columns:
            print(f"Warning: Column '{loco_col}' not found. Available columns: {list(station_data.columns)}")
            return 0
    
        # Count locos that start with "WD"
        diesel_count = 0
        for loco_type in station_data[loco_col].dropna():
            if str(loco_type).startswith('WDG'):
                diesel_count += 1
    
        return diesel_count
    
    def _calculate_trains_count(self, station_data, is_handedover=True):
        """Calculate trains count in A/B format"""
        if is_handedover:
            sttn_col = 'HANDED OVER STTN TO'
            loco_col = 'HANDED OVER LOCO TYPE'
        else:
            sttn_col = 'TAKEN OVER STTN TO'
            loco_col = 'TAKEN OVER LOCO TYPE'
    
        # Count non-blank values in STTN TO column
        a_count = station_data[sttn_col].notna().sum()
    
        # Count non-blank values in LOCO TYPE column  
        b_count = station_data[loco_col].notna().sum()
    
        return f"{a_count}/{b_count}"
    
    def _calculate_cont_count(self, station_data, is_handedover=True):
        """Calculate total CONT count (L+E combined) for a station"""
        if is_handedover:
            class_col = 'HANDEDOVER CLASSIFICATION'
            le_col = 'HANDED OVER L/E'
        else:
            class_col = 'TAKENOVER CLASSIFICATION'
            le_col = 'TAKEN OVER L/E'
        
        # Get data for CONT classification
        cont_data = station_data[station_data[class_col] == 'CONT']
        
        if cont_data.empty:
            return 0
        
        # Count both L and E together
        total_count = len(cont_data[cont_data[le_col].isin(['L', 'E'])])
        
        return total_count
    
    def _load_ph_stations(self):
        """Load PH stations from CSV file"""
        import os
        config_path = Config.PH_STATIONS_FILE 
        
        if not os.path.exists(config_path):
            # Create default if doesn't exist
            default_stations = ['AEMD','TPHS','TSWS','GETS','AECS','GES','NSPN','SPNG','USD','WKB','DRD','GNC','EPH']
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            
            with open(config_path, 'w', newline='', encoding='utf-8') as f:
                f.write('STATION_CODE\n')
                for station in default_stations:
                    f.write(f'{station}\n')
            # print(f"Created default PH stations file: {config_path}")
        
        ph_df = pd.read_csv(config_path)
        return set(ph_df['STATION_CODE'].str.strip().str.upper())
    
    def _calculate_boxn_ph_oth_counts(self, station_data):
        """Calculate PH+OTH count for BOXN classification in takenover section"""
        class_col = 'TAKENOVER CLASSIFICATION'
        le_col = 'TAKEN OVER L/E'
        sttn_col = 'TAKEN OVER STTN TO'
        
        # Get PH stations set
        ph_stations = self._load_ph_stations()
        # print(f"Loaded PH stations: {ph_stations}")
        
        # Get data for BOXN classification
        boxn_data = station_data[station_data[class_col] == 'BOX']  # Use BOX from intermediate
        # print(f"BOXN data found: {len(boxn_data)} rows")
        
        if boxn_data.empty:
            return "0+0"
        
        # Count PH: specific stations with L/E = "L"
        ph_data = boxn_data[
            (boxn_data[sttn_col].isin(ph_stations)) & 
            (boxn_data[le_col] == 'L')
        ]
        ph_count = len(ph_data)
        
        # Count OTH: all other stations with both L and E
        other_stations = boxn_data[~boxn_data[sttn_col].isin(ph_stations)]
        oth_count = len(other_stations[other_stations[le_col].isin(['L', 'E'])])
        
        # print(f"PH count: {ph_count}, OTH count: {oth_count}")
        return f"{ph_count}+{oth_count}"