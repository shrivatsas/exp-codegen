import pandas as pd
import argparse

# Set up command line argument parsing
parser = argparse.ArgumentParser(description='Split a large CSV file into smaller chunks')
parser.add_argument('input_file', help='Input CSV file to split')
parser.add_argument('--rows', type=int, default=10000, help='Number of rows per output file (default: 10000)')
args = parser.parse_args()

# Read the large CSV file
df = pd.read_csv(args.input_file)

# Define the number of rows per split
rows_per_file = args.rows
# Extract the header separately
header = df.columns

# Loop through the DataFrame in chunks and save to new CSVs with headers
for i in range(0, len(df), rows_per_file):
    chunk = df.iloc[i:i + rows_per_file]
    chunk.to_csv(f'split_{i // rows_per_file + 1}.csv', index=False, header=True)

print("CSV file split successfully with headers in each file!")
