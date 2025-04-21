import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from utils import load_csv, find_missing_data

def analyze_missing_data(file_path):
    """Analyze missing data patterns in a CSV file."""
    print(f"Loading CSV file: {file_path}")
    df = load_csv(file_path)
    
    # Basic dataset info
    print(f"\nDataset shape: {df.shape}")
    print("\nColumns in dataset:")
    for col in df.columns:
        print(f"- {col}")
    
    # Calculate missing values per column
    missing_values = df.isna().sum()
    print("\nMissing values per column:")
    for col, count in missing_values.items():
        print(f"- {col}: {count} ({count/len(df)*100:.2f}%)")
    
    # Find rows with missing data
    missing_data_map = find_missing_data(df)
    print(f"\nFound {len(missing_data_map)} rows with missing data")
    
    # Analyze patterns of missing data
    print("\nMissing data patterns (first 10):")
    missing_patterns = {}
    for idx, missing_cols in missing_data_map.items():
        pattern = tuple(sorted(missing_cols))
        missing_patterns[pattern] = missing_patterns.get(pattern, 0) + 1
    
    for i, (pattern, count) in enumerate(sorted(missing_patterns.items(), key=lambda x: x[1], reverse=True)):
        if i >= 10:
            break
        print(f"- {pattern}: {count} rows")
    
    # Check for correlations between columns with missing data
    print("\nCorrelations between missing columns:")
    missing_df = df.isna()
    corr_matrix = missing_df.corr()
    
    # Find high correlations
    high_corr = []
    for col1 in corr_matrix.columns:
        for col2 in corr_matrix.columns:
            if col1 != col2 and corr_matrix.loc[col1, col2] > 0.5:
                high_corr.append((col1, col2, corr_matrix.loc[col1, col2]))
    
    if high_corr:
        for col1, col2, corr in sorted(high_corr, key=lambda x: x[2], reverse=True):
            print(f"- {col1} and {col2}: {corr:.2f}")
    else:
        print("No strong correlations found between missing values")
    
    return df, missing_data_map

if __name__ == "__main__":
    analyze_missing_data("duimp_202502.csv") 