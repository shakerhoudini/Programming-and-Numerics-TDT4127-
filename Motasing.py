import re
import sys
import pandas as pd

# =========================================
# Input and output file names
# =========================================
input_file = "Yggdrasil_state0_07.07.2025_18-23_D_13HCV2627TargetPosition.csv"
output_file = "Yggdrasil_state0_07.07.2025_18-23_D_13HCV2627TargetPosition_upgraded.csv"

###################################################################################################################################################################################################################
################################################################################################ Differential Pressure (Δp) — same units check ##################################################################
###################################################################################################################################################################################################################

def parse_two_indices(input_str: str):
    """Parse exactly two integer indices from user input like '3,7' or '3 7'."""
    parts = re.split(r"[,\s]+", input_str.strip())
    parts = [p for p in parts if p != ""]
    if len(parts) != 2:
        raise ValueError("Please provide exactly two indices (e.g. 3,7).")
    return [int(parts[0]), int(parts[1])]

def extract_unit_from_colname(col_name: str):
    """
    Extract unit string from a column name, looking for:
    - [unit]
    - (unit)
    - ' unit' at end
    Returns unit in lowercase without brackets, or None if not found.
    """
    patterns = [
        r"\[(?P<u>[^\]]+)\]",   # [bar]
        r"\((?P<u>[^)]+)\)",    # (kPa)
        r"\b(?P<u>(?:mbar|kpa|mpa|psi|bar|pa))\b"  # token in name
    ]
    name = col_name.lower()
    for pat in patterns:
        m = re.search(pat, name)
        if m:
            return m.group("u").strip().lower()
    return None

###################################################################################################################################################################################################################
################################################################################################ Processing #######################################################################################################
###################################################################################################################################################################################################################

# Read CSV
try:
    df = pd.read_csv(input_file)
except FileNotFoundError:
    print(f"Error: File '{input_file}' not found.")
    sys.exit(1)
except Exception as e:
    print(f"Error reading file: {e}")
    sys.exit(1)

# List columns
print("Available columns:")
for i, col in enumerate(df.columns):
    print(f"  {i}: {col}")

# Get indices
user_input = input("\nEnter TWO column indices for Δp (first - second): ")
try:
    idx_first, idx_second = parse_two_indices(user_input)
except Exception as e:
    print(f"Invalid input: {e}")
    sys.exit(1)

# Validate
ncols = len(df.columns)
for idx in (idx_first, idx_second):
    if idx < 0 or idx >= ncols:
        print(f"Index {idx} is out of range (0–{ncols-1}).")
        sys.exit(1)

col_first = df.columns[idx_first]
col_second = df.columns[idx_second]

print("\nSelected columns:")
print(f"  first  = {idx_first} ({col_first})")
print(f"  second = {idx_second} ({col_second})")

# Extract units from column names
unit_first = extract_unit_from_colname(col_first)
unit_second = extract_unit_from_colname(col_second)

print("\nDetected units:")
print(f"  {col_first} → {unit_first or 'UNKNOWN'}")
print(f"  {col_second} → {unit_second or 'UNKNOWN'}")

# Check match
if not unit_first or not unit_second:
    print("\nERROR: Could not detect unit for one or both columns. Make sure units are in column names.")
    sys.exit(1)

if unit_first != unit_second:
    print("\nERROR: Units do not match between the two columns. Try again with matching units.")
    sys.exit(1)

# Name for new column
new_column_name = input("\nEnter the name of the new Δp column: ").strip()
if not new_column_name:
    new_column_name = "DP"

header_dp = f"{new_column_name} [{unit_first}]"

# Compute Δp row-wise
try:
    s_first  = pd.to_numeric(df[col_first], errors="coerce")
    s_second = pd.to_numeric(df[col_second], errors="coerce")
except Exception as e:
    print(f"Error: Non-numeric data encountered. {e}")
    sys.exit(1)

df[header_dp] = s_first - s_second

# Save
try:
    df.to_csv(output_file, index=False)
    print(f"\nFile saved successfully as: {output_file}")
except Exception as e:
    print(f"Error saving file: {e}")
    sys.exit(1)

# Show final headers
print("Updated column headers:")
for col in df.columns:
    print(" ", col)
