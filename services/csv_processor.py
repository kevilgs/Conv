import pandas as pd
import os
from config import Config
from services.wagon_classifier import WagonClassifier

class CSVProcessor:
    def __init__(self):
        self.required_columns = [
            'ZONE TO', 'IC STTN', 'TAKEN OVER ZONE FROM','TAKEN OVER STTN TO', 'TAKEN OVER ZONE TO', 'TAKEN OVER L/E',
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
        """Extract specific columns from row 3 onwards, handle flexible headers, and group by ZONE TO and IC STTN"""
        try:
            file_path = os.path.join(Config.UPLOAD_FOLDER, filename)
            if "MAFour" in filename:
                # MAFour logic: direct extraction by required columns
                df = pd.read_csv(file_path, skiprows=2)
                missing_columns = [col for col in self.required_columns if col not in df.columns]
                if missing_columns:
                    raise ValueError(f"Missing columns: {missing_columns}")

                extracted_df = df[self.required_columns].copy()
                extracted_df = extracted_df.dropna(subset=['ZONE TO', 'IC STTN'])

                # Add classification columns
                extracted_df = self._add_classification_columns(extracted_df)
                # Convert CNA of NW zone to AII
                extracted_df = self._convert_nw_cna_to_aii(extracted_df)
                
                original_ic_sttn = extracted_df['IC STTN'].copy()
                
                # Convert SAU in IC STTN based on TAKEN OVER ZONE FROM (for taken over section only)
                extracted_df = self._convert_sau_in_taken_over_section(extracted_df)
                
                # Create IC STTN (Copy) for handedover section
                extracted_df = self._create_ic_sttn_copy(extracted_df, original_ic_sttn)
                
                # Group and sort data
                grouped_df = self._group_and_sort(extracted_df)
                return grouped_df

            else:
                # Flexible extraction logic
                df = pd.read_csv(file_path, skiprows=2)
                df.columns = df.columns.str.strip()
                columns_to_extract = [
                    'ZONE FROM', 'STATION TO', 'ZONE TO', 'LOAD L/E', 'LOAD TYPE', 'LOCO NO', 'LOCO TYPE', 'ZN-STTN',
                    'ZONE TO', 'STATION TO', 'LOAD L/E', 'LOAD TYPE', 'LOCO NO', 'LOCO TYPE'
                ]

                def get_all_matching_columns(df_columns, base_name):
                    import re
                    pattern = re.compile(rf"^{re.escape(base_name)}(\.\d+)?$")
                    return [col for col in df_columns if pattern.match(col)]

                extracted_cols = []
                used = [0] * len(df.columns)
                for col_name in columns_to_extract:
                    matches = get_all_matching_columns(df.columns, col_name)
                    for idx, col in enumerate(df.columns):
                        if col in matches and not used[idx]:
                            extracted_cols.append(col)
                            used[idx] = 1
                            break

                extracted_df = df[extracted_cols].copy()

                # Find the index of 'ZN-STTN' in the extracted columns
                zn_sttn_indices = [i for i, col in enumerate(extracted_df.columns) if col.startswith('ZN-STTN')]
                if not zn_sttn_indices:
                    raise Exception("No 'ZN-STTN' column found in extracted columns.")

                # For your case, you have only one ZN-STTN, so:
                takenover_cols = extracted_df.columns[:zn_sttn_indices[0]].tolist()
                zn_sttn_col = extracted_df.columns[zn_sttn_indices[0]]
                handedover_cols = extracted_df.columns[zn_sttn_indices[0]+1:].tolist()

                # Define new names
                takenover_rename = {
                    old: new for old, new in zip(
                        takenover_cols,
                        ['TAKEN OVER ZONE FROM', 'TAKEN OVER STTN TO', 'TAKEN OVER ZONE TO', 'TAKEN OVER L/E', 'TAKEN OVER TYPE', 'TAKEN OVER LOCO', 'TAKEN OVER LOCO TYPE']
                    )
                }
                handedover_rename = {
                    old: new for old, new in zip(
                        handedover_cols,
                        ['HANDED OVER ZONE TO', 'HANDED OVER STTN TO', 'HANDED OVER L/E', 'HANDED OVER TYPE', 'HANDED OVER LOCO', 'HANDED OVER LOCO TYPE']
                    )
                }
                zn_sttn_rename = {zn_sttn_col: 'ZN-STTN'}

                # Combine all renames
                all_renames = {}
                all_renames.update(takenover_rename)
                all_renames.update(zn_sttn_rename)
                all_renames.update(handedover_rename)

                # Rename columns
                extracted_df = extracted_df.rename(columns=all_renames)

                # Split ZN-STTN into "ZONE TO" and "IC STTN" FIRST
                extracted_df[['ZONE TO', 'IC STTN']] = extracted_df['ZN-STTN'].str.split('-', n=1, expand=True)

                # Now build the final DataFrame in the required order
                final_columns = [
                    'ZONE TO', 'IC STTN', 'TAKEN OVER ZONE FROM', 'TAKEN OVER STTN TO', 'TAKEN OVER ZONE TO', 'TAKEN OVER L/E', 'TAKEN OVER TYPE', 'TAKEN OVER LOCO', 'TAKEN OVER LOCO TYPE',
                    'HANDED OVER ZONE TO', 'HANDED OVER STTN TO', 'HANDED OVER L/E', 'HANDED OVER TYPE', 'HANDED OVER LOCO', 'HANDED OVER LOCO TYPE'
                ]

                final_df = pd.DataFrame()
                for col in final_columns:
                    final_df[col] = extracted_df[col] if col in extracted_df.columns else None

                # Drop rows with NaN in ZONE TO or IC STTN
                final_df = final_df.dropna(subset=['ZONE TO', 'IC STTN'])

                # Add classification columns, conversions, grouping, etc.
                final_df = self._add_classification_columns(final_df)
                final_df = self._convert_nw_cna_to_aii(final_df)
                final_df = self._convert_sau_in_taken_over_section(final_df)
                
                # Custom merge logic for flexible format (TAKEN OVER section)
                pnu_merge_stations = ['BHU', 'CECC', 'GGM', 'MSH', 'SAUN']
                mask_taken = final_df['IC STTN'].isin(pnu_merge_stations)
                final_df.loc[mask_taken, 'IC STTN'] = 'PNU'
                final_df.loc[mask_taken, 'ZONE TO'] = 'NW'
                
                final_df = self._create_ic_sttn_copy(final_df)
                grouped_df = self._group_and_sort(final_df)

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
        """Convert SAU and GGM in IC STTN based on TAKEN OVER ZONE FROM"""
        # Rule for SAU
        sau_mask = df['IC STTN'] == 'SAU'
        sau_saus_mask = sau_mask & df['TAKEN OVER ZONE FROM'].isin(self.saus_zones)
        sau_saun_mask = sau_mask & ~sau_saus_mask
        
        df.loc[sau_saun_mask, 'IC STTN'] = 'SAUN'
        df.loc[sau_saus_mask, 'IC STTN'] = 'SAUS'
        
        # Rule for GGM
        ggm_mask = df['IC STTN'] == 'GGM'
        ggm_saus_mask = ggm_mask & df['TAKEN OVER ZONE FROM'].isin(self.saus_zones)
        df.loc[ggm_saus_mask, 'IC STTN'] = 'SAUS'
        
        return df
    
    def _create_ic_sttn_copy(self, df, original_ic_sttn=None):
        """Create IC STTN (Copy) for handedover section with different logic"""
        # Start with original IC STTN before any conversions
        if original_ic_sttn is not None:
            df['IC STTN (Copy)'] = original_ic_sttn.copy()
        else:
            df['IC STTN (Copy)'] = df['IC STTN'].copy()
            
        # Handle CNA conversion for IC STTN (Copy) as well
        mask_cna = (df['ZONE TO'] == 'NW') & (df['IC STTN (Copy)'] == 'CNA')
        df.loc[mask_cna, 'IC STTN (Copy)'] = 'AII'
        
        # Now apply SAU and GGM conversion for IC STTN (Copy) using HANDED OVER ZONE TO
        sau_mask = df['IC STTN (Copy)'] == 'SAU'
        ggm_mask = df['IC STTN (Copy)'] == 'GGM'
        
        # Use HANDED OVER ZONE TO for handedover section conversion
        if 'HANDED OVER ZONE TO' in df.columns:
            sau_base_saus_mask = sau_mask & df['HANDED OVER ZONE TO'].isin(self.saus_zones)
            ggm_base_saus_mask = ggm_mask & df['HANDED OVER ZONE TO'].isin(self.saus_zones)
            
            if 'HANDED OVER STTN TO' in df.columns:
                sau_custom_saus_mask = sau_mask & (df['HANDED OVER ZONE TO'] == 'DFCR') & (df['HANDED OVER STTN TO'].isin(['DGGN', 'SCGN']))
                ggm_custom_saus_mask = ggm_mask & (df['HANDED OVER ZONE TO'] == 'DFCR') & (df['HANDED OVER STTN TO'].isin(['DGGN', 'SCGN']))
            else:
                sau_custom_saus_mask = pd.Series([False] * len(df))
                ggm_custom_saus_mask = pd.Series([False] * len(df))
                
            sau_saus_mask = sau_base_saus_mask | sau_custom_saus_mask
            sau_saun_mask = sau_mask & ~sau_saus_mask
            
            ggm_saus_mask = ggm_base_saus_mask | ggm_custom_saus_mask
        else:
            # Fallback logic - default to SAUN first (priority)
            sau_saun_mask = sau_mask  
            sau_saus_mask = pd.Series([False] * len(df))
            ggm_saus_mask = pd.Series([False] * len(df))
        
        # Apply conversions
        df.loc[sau_saun_mask, 'IC STTN (Copy)'] = 'SAUN'
        df.loc[sau_saus_mask, 'IC STTN (Copy)'] = 'SAUS'
        df.loc[ggm_saus_mask, 'IC STTN (Copy)'] = 'SAUS'
        
        return df
    
    def _convert_sau_in_handed_over_section(self, df):
        """Convert SAU in IC STTN (Copy) based on HANDED OVER ZONE TO"""
        if 'IC STTN (Copy)' in df.columns and 'HANDED OVER ZONE TO' in df.columns:
            mask = df['IC STTN (Copy)'] == 'SAU'

            saus_mask = mask & df['HANDED OVER ZONE TO'].isin(self.saus_zones)
            saun_mask = mask & ~df['HANDED OVER ZONE TO'].isin(self.saus_zones)

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
        
        def get_original_station_priority(zn_sttn):
            if pd.isna(zn_sttn) or not isinstance(zn_sttn, str):
                return 100
            if 'SAU' in zn_sttn and 'SAUN' not in zn_sttn and 'SAUS' not in zn_sttn:
                return 0
            if 'GGM' in zn_sttn:
                return 1
            return 2
            
        # Add zone priority
        df['zone_priority'] = df['ZONE TO'].apply(get_zone_priority)
        
        if 'ZN-STTN' in df.columns:
            df['orig_sttn_priority'] = df['ZN-STTN'].apply(get_original_station_priority)
        else:
            df['orig_sttn_priority'] = 2
        
        # Create combined sorting key for BOTH IC STTN and IC STTN (Copy)
        df['combined_priority'] = df.apply(lambda row: (
            get_station_priority(row['ZONE TO'], row['IC STTN']),
            get_station_priority(row['ZONE TO'], row['IC STTN (Copy)']),
            row['orig_sttn_priority']
        ), axis=1)
        
        # Sort by zone first, then by combined priority
        sorted_df = df.sort_values([
            'zone_priority',
            'combined_priority'
        ]).drop(['zone_priority', 'combined_priority', 'orig_sttn_priority'], axis=1)
        
        return sorted_df
    
    def get_original_ic_sttn(self, filename):
        """Get original IC STTN column before any conversion for handed over section"""
        try:
            file_path = os.path.join(Config.UPLOAD_FOLDER, filename)
            if "MAFour" in filename:
                df = pd.read_csv(file_path, skiprows=2)
                extracted_df = df[self.required_columns].copy()
                extracted_df = extracted_df.dropna(subset=['ZONE TO', 'IC STTN'])

                # Add classification columns before any conversions
                extracted_df = self._add_classification_columns(extracted_df)

                # Only convert CNA to AII, don't convert SAU yet
                extracted_df = self._convert_nw_cna_to_aii(extracted_df)

                return extracted_df['IC STTN']
            else:
                df = pd.read_csv(file_path, skiprows=2)
                df.columns = df.columns.str.strip()

                # --- Flexible extraction and renaming logic (same as process_csv) ---
                columns_to_extract = [
                    'ZONE FROM', 'STATION TO', 'ZONE TO', 'LOAD L/E', 'LOAD TYPE', 'LOCO NO', 'LOCO TYPE', 'ZN-STTN',
                    'ZONE TO', 'STATION TO', 'LOAD L/E', 'LOAD TYPE', 'LOCO NO', 'LOCO TYPE'
                ]

                def get_all_matching_columns(df_columns, base_name):
                    import re
                    pattern = re.compile(rf"^{re.escape(base_name)}(\.\d+)?$")
                    return [col for col in df_columns if pattern.match(col)]

                extracted_cols = []
                used = [0] * len(df.columns)
                for col_name in columns_to_extract:
                    matches = get_all_matching_columns(df.columns, col_name)
                    for idx, col in enumerate(df.columns):
                        if col in matches and not used[idx]:
                            extracted_cols.append(col)
                            used[idx] = 1
                            break

                extracted_df = df[extracted_cols].copy()

                zn_sttn_indices = [i for i, col in enumerate(extracted_df.columns) if col.startswith('ZN-STTN')]
                if not zn_sttn_indices:
                    raise Exception("No 'ZN-STTN' column found in extracted columns.")

                takenover_cols = extracted_df.columns[:zn_sttn_indices[0]].tolist()
                zn_sttn_col = extracted_df.columns[zn_sttn_indices[0]]
                handedover_cols = extracted_df.columns[zn_sttn_indices[0]+1:].tolist()

                takenover_rename = {
                    old: new for old, new in zip(
                        takenover_cols,
                        ['TAKEN OVER ZONE FROM', 'TAKEN OVER STTN TO', 'TAKEN OVER ZONE TO', 'TAKEN OVER L/E', 'TAKEN OVER TYPE', 'TAKEN OVER LOCO', 'TAKEN OVER LOCO TYPE']
                    )
                }
                handedover_rename = {
                    old: new for old, new in zip(
                        handedover_cols,
                        ['HANDED OVER ZONE TO', 'HANDED OVER STTN TO', 'HANDED OVER L/E', 'HANDED OVER TYPE', 'HANDED OVER LOCO', 'HANDED OVER LOCO TYPE']
                    )
                }
                zn_sttn_rename = {zn_sttn_col: 'ZN-STTN'}

                all_renames = {}
                all_renames.update(takenover_rename)
                all_renames.update(zn_sttn_rename)
                all_renames.update(handedover_rename)

                extracted_df = extracted_df.rename(columns=all_renames)
                extracted_df[['ZONE TO', 'IC STTN']] = extracted_df['ZN-STTN'].str.split('-', n=1, expand=True)

                # Drop rows with NaN in ZONE TO or IC STTN
                extracted_df = extracted_df.dropna(subset=['ZONE TO', 'IC STTN'])

                # Add classification columns before any conversions
                extracted_df = self._add_classification_columns(extracted_df)

                # Only convert CNA to AII, don't convert SAU yet
                extracted_df = self._convert_nw_cna_to_aii(extracted_df)

                return extracted_df['IC STTN']

        except Exception as e:
            raise Exception(f"Error getting original IC STTN: {str(e)}")