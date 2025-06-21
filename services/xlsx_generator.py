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

            # Remove duplicate rows where TAKEN OVER and HANDED OVER have same STTN TO and TYPE
            ordered_df = self._remove_duplicate_rows(ordered_df)  # Add this line

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
    
    def _remove_duplicate_rows(self, df):
        """
        Remove rows where the same station appears as both TAKEN OVER STTN TO and HANDED OVER STTN TO
        for matching IC STTN and IC STTN (Copy), even if they're in different rows.
        
        Example: If IC STTN "JL" has TAKEN OVER STTN TO "TWS" in one row and 
        another row has IC STTN (Copy) "JL" with HANDED OVER STTN TO "TWS", both rows should be deleted.
        """
        if all(col in df.columns for col in ['IC STTN', 'IC STTN (Copy)', 'TAKEN OVER STTN TO', 'HANDED OVER STTN TO']):
            # Original row count for reporting
            original_count = len(df)
            
            # Create a temporary column to track which rows to delete
            df['delete_row'] = False
            
            # Get unique station names that appear in either IC STTN or IC STTN (Copy)
            all_stations = set(df['IC STTN'].dropna().unique()) | set(df['IC STTN (Copy)'].dropna().unique())
            print("\n=== DUPLICATE STATION DETECTION ===")
            
            for station in all_stations:
                # Get all takenover rows for this station
                takenover_rows = df[df['IC STTN'] == station]
                
                # Get all handedover rows for this station
                handedover_rows = df[df['IC STTN (Copy)'] == station]
                
                # If this station appears in both sections
                if not takenover_rows.empty and not handedover_rows.empty:
                    # Get all TAKEN OVER STTN TO values for this station
                    taken_over_stations = set(takenover_rows['TAKEN OVER STTN TO'].dropna())
                    
                    # Get all HANDED OVER STTN TO values for this station  
                    handed_over_stations = set(handedover_rows['HANDED OVER STTN TO'].dropna())
                    
                    # Find stations that appear in both lists
                    duplicate_stations = taken_over_stations.intersection(handed_over_stations)
                    
                    if duplicate_stations:
                        print(f"IC STTN '{station}' has duplicate destinations:")
                        # Mark rows for deletion where station is in both columns
                        for dup_station in duplicate_stations:
                            print(f"  - STTN TO '{dup_station}' appears in both TAKEN OVER and HANDED OVER")
                            # Mark taken over rows with this station
                            taken_mask = (df['IC STTN'] == station) & (df['TAKEN OVER STTN TO'] == dup_station)
                            taken_rows = df[taken_mask]
                            df.loc[taken_mask, 'delete_row'] = True

                            for idx, row in taken_rows.iterrows():
                             print(f"    * Deleting TAKEN OVER row: {row['IC STTN']} → {row['TAKEN OVER STTN TO']} ({row['TAKEN OVER TYPE']})")
                            
                            # Mark handed over rows with this station
                            handed_mask = (df['IC STTN (Copy)'] == station) & (df['HANDED OVER STTN TO'] == dup_station)
                            handed_rows = df[handed_mask]
                            df.loc[handed_mask, 'delete_row'] = True

                            for idx, row in handed_rows.iterrows():
                                print(f"    * Deleting HANDED OVER row: {row['IC STTN (Copy)']} → {row['HANDED OVER STTN TO']} ({row['HANDED OVER TYPE']})")
            
            # Remove rows marked for deletion
            df_filtered = df[~df['delete_row']].drop('delete_row', axis=1)
            
            deleted_count = original_count - len(df_filtered)
            print(f"Deleted {deleted_count} rows where the same station appears in both TAKEN OVER and HANDED OVER sections")
            
            return df_filtered
        
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