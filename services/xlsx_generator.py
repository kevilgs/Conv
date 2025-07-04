import pandas as pd
import os
from config import Config
from services.csv_processor import CSVProcessor

class XLSXGenerator:
    def __init__(self):
        # Updated column order with classification columns
        self.custom_column_order = [
            'ZONE TO',
            'IC STTN', 
            'TAKEN OVER ZONE FROM',
            'TAKEN OVER STTN TO',
            'TAKEN OVER L/E',
            'TAKEN OVER TYPE',
            'TAKENOVER CLASSIFICATION',  # New column before TAKEN OVER LOCO
            'TAKEN OVER LOCO',
            'TAKEN OVER LOCO TYPE',
            ('IC STTN', 'IC STTN (Copy)'),  
            'HANDED OVER ZONE TO',
            'HANDED OVER STTN TO', 
            'HANDED OVER L/E',
            'HANDED OVER TYPE',
            'HANDEDOVER CLASSIFICATION',  # New column before HANDED OVER LOCO
            'HANDED OVER LOCO',
            'HANDED OVER LOCO TYPE',
        ]
        
        # Zones that convert SAU to SAUS
        self.saus_zones = ['WR', 'CR', 'KR', 'SW', 'SR', 'SEC', 'ECO','SC',]
    
    def generate_intermediate_xlsx(self, df, original_filename, custom_order=None):
        """Generate intermediate XLSX file with custom column order"""
        try:
            # Use custom order if provided, otherwise use default
            column_order = custom_order if custom_order else self.custom_column_order
            
            # Get original IC STTN before SAU conversion for handed over section
            processor = CSVProcessor()
            original_ic_sttn = processor.get_original_ic_sttn(original_filename)
            
            # Create new DataFrame with custom column order (allows repetition)
            ordered_df = pd.DataFrame()
            
            for item in column_order:
                if isinstance(item, tuple):
                    # Handle repeated columns with custom names
                    source_col, new_name = item
                    if source_col == 'IC STTN':
                        # Use original IC STTN values for the copy
                        ordered_df[new_name] = original_ic_sttn
                    elif source_col in df.columns:
                        ordered_df[new_name] = df[source_col]
                else:
                    # Handle regular columns
                    if item in df.columns:
                        ordered_df[item] = df[item]
            
            # Convert SAU in IC STTN (Copy) based on HANDED OVER ZONE TO
            ordered_df = self._convert_sau_in_handed_over_section(ordered_df)

            # Create output filename
            base_name = os.path.splitext(original_filename)[0]
            output_filename = f"{base_name}_processed.xlsx"
            output_path = os.path.join(Config.INTERMEDIATE_FOLDER, output_filename)
            
            # Write to Excel
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                ordered_df.to_excel(writer, sheet_name='Processed Data', index=False)
            
            return output_path
            
        except Exception as e:
            raise Exception(f"Error generating XLSX: {str(e)}")
    
    def _convert_sau_in_handed_over_section(self, df):
        """Convert SAU in IC STTN (Copy) based on HANDED OVER ZONE TO"""
        print("=== SAU CONVERSION DEBUG ===")
        print(f"DataFrame shape: {df.shape}")
        print(f"saus_zones: {self.saus_zones}")
        
        if 'IC STTN (Copy)' in df.columns and 'HANDED OVER ZONE TO' in df.columns:
            sau_rows = df[df['IC STTN (Copy)'] == 'SAU']
            print(f"Found {len(sau_rows)} SAU rows")
            
            if len(sau_rows) > 0:
                print(f"HANDED OVER ZONE TO values for SAU: {sau_rows['HANDED OVER ZONE TO'].unique()}")
                
                # Check SC specifically
                sc_rows = sau_rows[sau_rows['HANDED OVER ZONE TO'] == 'SC']
                print(f"SC rows: {len(sc_rows)}")
                
            # Rule: IC STTN (Copy) = SAU, check HANDED OVER ZONE TO
            mask = df['IC STTN (Copy)'] == 'SAU'
            saus_mask = mask & df['HANDED OVER ZONE TO'].isin(self.saus_zones)
            saun_mask = mask & ~df['HANDED OVER ZONE TO'].isin(self.saus_zones)
            
            df.loc[saus_mask, 'IC STTN (Copy)'] = 'SAUS'
            df.loc[saun_mask, 'IC STTN (Copy)'] = 'SAUN'
        
        return df
     
    def _sort_dataframe_by_zones(self, df):
        """Sort DataFrame by zones and maintain SAUN before SAUS order"""
        
        def get_station_order_key(station):
            """Custom sorting to ensure SAUN comes before SAUS"""
            if station == 'SAUN':
                return (0, station)  # SAUN gets priority 0
            elif station == 'SAUS':
                return (1, station)  # SAUS gets priority 1
            else:
                return (2, station)  # All others get priority 2
        
        # Sort by zone first, then by custom station order
        df['zone_sort_key'] = df['ZONE TO'].map(self.zone_order)
        df['station_sort_key'] = df['IC STTN'].apply(get_station_order_key)
        df['station_copy_sort_key'] = df['IC STTN (Copy)'].apply(get_station_order_key)
        
        # Sort maintaining SAUN before SAUS
        sorted_df = df.sort_values([
            'zone_sort_key',
            'station_sort_key',
            'station_copy_sort_key'
        ])
        
        # Remove helper columns
        sorted_df = sorted_df.drop(['zone_sort_key', 'station_sort_key', 'station_copy_sort_key'], axis=1)
        
        return sorted_df