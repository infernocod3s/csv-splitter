import pandas as pd
import os
from pathlib import Path

def split_csv(input_file, chunk_size=49999):
    """
    Split a CSV file into multiple files with specified number of records per file.
    
    Args:
        input_file (str): Path to the input CSV file
        chunk_size (int): Number of records per output file (default: 49999)
    """
    # Get the input file name without extension
    input_path = Path(input_file)
    base_name = input_path.stem
    output_dir = input_path.parent
    
    # Read the CSV file in chunks
    chunk_number = 1
    for chunk in pd.read_csv(input_file, chunksize=chunk_size):
        # Create output filename
        output_file = output_dir / f"{base_name}_part{chunk_number}.csv"
        
        # Write chunk to new CSV file
        chunk.to_csv(output_file, index=False)
        print(f"Created {output_file} with {len(chunk)} records")
        
        chunk_number += 1

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Split a CSV file into multiple files with 49,999 records each')
    parser.add_argument('input_file', help='Path to the input CSV file')
    parser.add_argument('--chunk-size', type=int, default=49999, help='Number of records per output file (default: 49999)')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input_file):
        print(f"Error: Input file '{args.input_file}' does not exist")
        exit(1)
        
    split_csv(args.input_file, args.chunk_size) 