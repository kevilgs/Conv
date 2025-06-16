import pandas as pd
import os
from config import Config
from services.wagon_classifier import WagonClassifier

class CSVProcessor:
    def __init__(self):
        self.required_columns = [
            'ZONE TO', 'IC STTN', 'TAKEN OVER ZONE FROM','TAKEN OVER STTN TO', 'TAKEN OVER L/E',
            'TAKEN OVER TYPE', 'TAKEN OVER LOCO', 'TAKEN OVER LOCO TYPE',
            'HANDED OVER ZONE TO', 'HANDED OVER STTN TO', 'HANDED OVER L/E',
            'HANDED OVER TYPE', 'HANDED OVER LOCO', 'HANDED OVER LOCO TYPE'
        ]
        
        # Station ordering for grouping - FIXED: DFC matches DFCR
        self.zone_order = ['CR', 'WC', 'NW', 'DFCR']  # Changed DFC to DFCR
        self.station_order = {
            'CR': ['BSR', 'JL', 'KNW'],
            'WC': ['SHRN', 'NAD', 'MKC', 'MTA', 'CNA'],
            'NW': ['BEC', 'AII', 'HMT', 'BLDI', 'PNU'],
            'DFCR': ['BHU', 'CECC', 'GGM', 'MSH', 'SAUN', 'SAUS', 'MPR', 'GTX', 'PAO', 'NOL', 'BHET', 'SAH', 'SJN']
        }
        
        # Zones that convert SAU to SAUS
        self.saus_zones = ['WR', 'CR', 'KR', 'SW', 'SR', 'SEC', 'ECO','SC',]
        
        # Initialize wagon classifier
        self.wagon_classifier = WagonClassifier()
    
    def process_csv(self, filename):
        """Extract specific columns from row 3 onwards and group by ZONE TO and IC STTN"""
        try:
            file_path = os.path.join(Config.UPLOAD_FOLDER, filename)
            
            # Read CSV starting from row 3 (index 2)
            df = pd.read_csv(file_path, skiprows=2)
            
            # Extract only required columns
            missing_columns = [col for col in self.required_columns if col not in df.columns]
            if missing_columns:
                raise ValueError(f"Missing columns: {missing_columns}")
            
            extracted_df = df[self.required_columns].copy()
            
            # Remove rows with NaN in ZONE TO or IC STTN
            extracted_df = extracted_df.dropna(subset=['ZONE TO', 'IC STTN'])
            
            # Add classification columns
            extracted_df = self._add_classification_columns(extracted_df)
            
            # Convert CNA of NW zone to AII
            extracted_df = self._convert_nw_cna_to_aii(extracted_df)
            
            # Convert SAU in IC STTN based on TAKEN OVER ZONE FROM (for taken over section only)
            extracted_df = self._convert_sau_in_taken_over_section(extracted_df)
            
            # Create IC STTN (Copy) for handedover section
            extracted_df = self._create_ic_sttn_copy(extracted_df)
            
            # Group and sort data
            grouped_df = self._group_and_sort(extracted_df)
            
            return grouped_df
            
        except Exception as e:
            raise Exception(f"Error processing CSV: {str(e)}")
    
    def _add_classification_columns(self, df):
        """Add TAKENOVER CLASSIFICATION and HANDEDOVER CLASSIFICATION columns"""
        # Add TAKENOVER CLASSIFICATION based on TAKEN OVER TYPE
        df['TAKENOVER CLASSIFICATION'] = df['TAKEN OVER TYPE'].apply(self.wagon_classifier.classify_wagon)
        
        # Add HANDEDOVER CLASSIFICATION based on HANDED OVER TYPE
        df['HANDEDOVER CLASSIFICATION'] = df['HANDED OVER TYPE'].apply(self.wagon_classifier.classify_wagon)
        
        return df
    
    def _convert_nw_cna_to_aii(self, df):
        """Convert CNA to AII only for NW zone"""
        mask = (df['ZONE TO'] == 'NW') & (df['IC STTN'] == 'CNA')
        df.loc[mask, 'IC STTN'] = 'AII'
        return df
    
    def _convert_sau_in_taken_over_section(self, df):
        """Convert SAU in IC STTN based on TAKEN OVER ZONE FROM"""
        # Rule: IC STTN = SAU, check TAKEN OVER ZONE FROM
        mask = df['IC STTN'] == 'SAU'
        saus_mask = mask & df['TAKEN OVER ZONE FROM'].isin(self.saus_zones)
        saun_mask = mask & ~df['TAKEN OVER ZONE FROM'].isin(self.saus_zones)
        
        df.loc[saus_mask, 'IC STTN'] = 'SAUS'
        df.loc[saun_mask, 'IC STTN'] = 'SAUN'
        
        return df
    
    def _create_ic_sttn_copy(self, df):
        """Create IC STTN (Copy) for handedover section with different logic"""
        # Start with original IC STTN before any conversions (except CNA->AII)
        df['IC STTN (Copy)'] = df['IC STTN'].copy()
        
        # Handle CNA conversion for IC STTN (Copy) as well
        mask_cna = (df['ZONE TO'] == 'NW') & (df['IC STTN (Copy)'] == 'CNA')
        df.loc[mask_cna, 'IC STTN (Copy)'] = 'AII'
        
        # For handedover section, we need to start from original SAU values
        # Reset any SAU conversions that might have been applied
        mask_sau_reset = (df['IC STTN (Copy)'].isin(['SAUS', 'SAUN']))
        # Find original SAU entries by checking if they were converted
        original_sau_mask = mask_sau_reset
        df.loc[original_sau_mask, 'IC STTN (Copy)'] = 'SAU'
        
        # Now apply SAU conversion for IC STTN (Copy) using HANDED OVER ZONE TO
        mask = df['IC STTN (Copy)'] == 'SAU'
        
        # Use HANDED OVER ZONE TO for handedover section conversion
        if 'HANDED OVER ZONE TO' in df.columns:
            saus_mask = mask & df['HANDED OVER ZONE TO'].isin(self.saus_zones)
            saun_mask = mask & ~df['HANDED OVER ZONE TO'].isin(self.saus_zones)
        else:
            # Fallback logic - default to SAUN first (priority)
            saun_mask = mask  
            saus_mask = pd.Series([False] * len(df))
        
        # Apply conversions with SAUN having priority
        df.loc[saun_mask, 'IC STTN (Copy)'] = 'SAUN'
        df.loc[saus_mask, 'IC STTN (Copy)'] = 'SAUS'
        
        return df
    
    def _convert_sau_in_handed_over_section(self, df):
        """Convert SAU in IC STTN (Copy) based on HANDED OVER ZONE TO"""
        if 'IC STTN (Copy)' in df.columns and 'HANDED OVER ZONE TO' in df.columns:
            mask = df['IC STTN (Copy)'] == 'SAU'
            
            # Debug prints
            print(f"SAU rows found: {mask.sum()}")
            print(f"HANDED OVER ZONE TO values: {df.loc[mask, 'HANDED OVER ZONE TO'].unique()}")
            print(f"SAUS zones configured: {self.saus_zones}")
            
            saus_mask = mask & df['HANDED OVER ZONE TO'].isin(self.saus_zones)
            saun_mask = mask & ~df['HANDED OVER ZONE TO'].isin(self.saus_zones)
            
            print(f"SAUS conversions: {saus_mask.sum()}")
            print(f"SAUN conversions: {saun_mask.sum()}")
            
            df.loc[saus_mask, 'IC STTN (Copy)'] = 'SAUS'
            df.loc[saun_mask, 'IC STTN (Copy)'] = 'SAUN'
        
        return df
    
    def _group_and_sort(self, df):
        """Group by ZONE TO first, then sort IC STTN within each zone for both columns"""
        
        def get_zone_priority(zone):
            if zone in self.zone_order:
                return self.zone_order.index(zone)
            else:
                return len(self.zone_order)
        
        def get_station_priority(zone, station):
            if zone in self.station_order and station in self.station_order[zone]:
                return self.station_order[zone].index(station)
            else:
                return 1000
        
        # Add sorting columns for IC STTN (takenover section)
        df['zone_priority'] = df['ZONE TO'].apply(get_zone_priority)
        df['station_priority'] = df.apply(lambda row: get_station_priority(row['ZONE TO'], row['IC STTN']), axis=1)
        
        # Add sorting columns for IC STTN (Copy) (handedover section) 
        df['station_copy_priority'] = df.apply(lambda row: get_station_priority(row['ZONE TO'], row['IC STTN (Copy)']), axis=1)
        
        # Sort primarily by IC STTN (Copy) order for handedover section
        # This ensures handedover section follows the SAUN->SAUS order
        sorted_df = df.sort_values(['zone_priority', 'station_copy_priority', 'station_priority']).drop([
            'zone_priority', 'station_priority', 'station_copy_priority'
        ], axis=1)
        
        return sorted_df
    
    def get_original_ic_sttn(self, filename):
        """Get original IC STTN column before any conversion for handed over section"""
        try:
            file_path = os.path.join(Config.UPLOAD_FOLDER, filename)
            df = pd.read_csv(file_path, skiprows=2)
            extracted_df = df[self.required_columns].copy()
            extracted_df = extracted_df.dropna(subset=['ZONE TO', 'IC STTN'])
            
            # Add classification columns before any conversions
            extracted_df = self._add_classification_columns(extracted_df)
            
            # Only convert CNA to AII, don't convert SAU yet
            extracted_df = self._convert_nw_cna_to_aii(extracted_df)
            
            return extracted_df['IC STTN']
            
        except Exception as e:
            raise Exception(f"Error getting original IC STTN: {str(e)}")