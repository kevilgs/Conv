import pandas as pd
import re

# Read your test CSV
df = pd.read_csv('test_headers.csv', skiprows=2)
df.columns = df.columns.str.strip()

columns_to_extract = [
    'ZONE FROM', 'STATION TO', 'LOAD L/E', 'LOAD TYPE', 'LOCO NO', 'LOCO TYPE', 'ZN-STTN',
    'ZONE FROM', 'STATION TO', 'LOAD L/E', 'LOAD TYPE', 'LOCO NO', 'LOCO TYPE'
]

def get_all_matching_columns(df_columns, base_name):
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
        ['TAKEN OVER ZONE FROM', 'TAKEN OVER STTN TO', 'TAKEN OVER L/E', 'TAKEN OVER TYPE', 'TAKEN OVER LOCO', 'TAKEN OVER LOCO TYPE']
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
    'ZONE TO','IC STTN', 'TAKEN OVER ZONE FROM', 'TAKEN OVER STTN TO', 'TAKEN OVER L/E', 'TAKEN OVER TYPE', 'TAKEN OVER LOCO', 'TAKEN OVER LOCO TYPE',
    'HANDED OVER ZONE TO', 'HANDED OVER STTN TO', 'HANDED OVER L/E', 'HANDED OVER TYPE', 'HANDED OVER LOCO', 'HANDED OVER LOCO TYPE'
]

final_df = pd.DataFrame()
for col in final_columns:
    final_df[col] = extracted_df[col] if col in extracted_df.columns else None

# Save to Excel
output_path = "extracted_columns.xlsx"
final_df.to_excel(output_path, index=False)
print(f"\nExtracted columns saved as {output_path}")