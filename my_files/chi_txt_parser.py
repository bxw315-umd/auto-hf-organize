"""
Parser that takes in CHI .txt files and parses the data into a dict
"""

# EVOLVE-BLOCK START
def parse_chi_txt(file_path: str) -> dict[str, float]:
    # read the file
    with open(file_path, "r") as f:
        lines = f.read().splitlines()
        
    # Parse metadata headers
    metadata_keys = ["Init E (V)", "High E (V)", "Low E (V)", "Init P/N", "Scan Rate (V/s)", 
                     "Segment", "Sample Interval (V)", "Quiet Time (sec)", "Sensitivity (A/V)"]
    metadata = {}
    data_start_idx = 0
    for i, line in enumerate(lines):
        # Check for header lines with '=' or ':'
        if '=' in line:
            for key in metadata_keys:
                if line.startswith(key):
                    # Parse key-value
                    parts = line.split('=')
                    if len(parts) == 2:
                        key_name = parts[0].strip()
                        val = parts[1].strip()
                        # Convert to float or int where possible
                        try:
                            val_converted = float(val)
                            if val_converted.is_integer():
                                val_converted = int(val_converted)
                            metadata[key_name] = val_converted
                        except:
                            metadata[key_name] = val
        elif line.strip().startswith("Potential/V") or line.strip().startswith("Potential/V,"):
            # Found the header of data table
            data_start_idx = i
            break
    # Determine delimiter based on header line
    header_line = lines[data_start_idx]
    delimiter = "," if "," in header_line else "\t"
    column_names = [name.strip() for name in header_line.split(delimiter)]
    
    # Check for multi-channel data by presence of multiple potential columns
    # and handle accordingly.
    # Collect data rows
    data_rows = lines[data_start_idx+1:]
    
    # Initialize dictionary for data
    data_dict = {}
    
    # Identify all potential columns (assumed to end with /V or /A or similar)
    channel_columns = []
    for col in column_names:
        # Handle potential multiple channels: e.g., i1/A, i2/A, etc.
        if col.startswith("Potential") or col.startswith("Potential/V"):
            data_dict[col] = []
            potential_col = col
        elif col.startswith("i") or col.startswith("C") or col.startswith("Time"):
            data_dict[col] = []
            channel_columns.append(col)
        else:
            data_dict[col] = []
    # Parse each data row
    for row in data_rows:
        if not row.strip():
            continue
        parts = [part.strip() for part in row.split(delimiter)]
        if len(parts) != len(column_names):
            continue  # skip malformed lines
        for col, val in zip(column_names, parts):
            try:
                value = float(val)
            except:
                value = val
            data_dict[col].append(value)
    return metadata | data_dict
# EVOLVE-BLOCK END