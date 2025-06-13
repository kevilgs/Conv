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
        self.saus_zones = ['WR', 'CR', 'KR', 'SW', 'SR', 'SEC', 'ECO']
    
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
        if 'IC STTN (Copy)' in df.columns and 'HANDED OVER ZONE TO' in df.columns:
            # Rule: IC STTN (Copy) = SAU, check HANDED OVER ZONE TO
            mask = df['IC STTN (Copy)'] == 'SAU'
            saus_mask = mask & df['HANDED OVER ZONE TO'].isin(self.saus_zones)
            saun_mask = mask & ~df['HANDED OVER ZONE TO'].isin(self.saus_zones)
            
            df.loc[saus_mask, 'IC STTN (Copy)'] = 'SAUS'
            df.loc[saun_mask, 'IC STTN (Copy)'] = 'SAUN'
        
        return df
    
    def _remove_duplicate_rows(self, df):
        """Remove rows where TAKEN OVER and HANDED OVER have same STTN TO and TYPE"""
        if all(col in df.columns for col in ['TAKEN OVER STTN TO', 'HANDED OVER STTN TO', 
                                            'TAKEN OVER TYPE', 'HANDED OVER TYPE']):
            
            # Create mask for rows to keep (opposite of what we want to delete)
            same_sttn = df['TAKEN OVER STTN TO'] == df['HANDED OVER STTN TO']
            same_type = df['TAKEN OVER TYPE'] == df['HANDED OVER TYPE']
            
            # Rows to delete are where BOTH conditions are true
            rows_to_delete = same_sttn & same_type
            
            # Keep rows where condition is NOT true
            df_filtered = df[~rows_to_delete].copy()
            
            deleted_count = len(df) - len(df_filtered)
            print(f"Deleted {deleted_count} duplicate rows (same STTN TO and TYPE)")
            
            return df_filtered
        
        return df