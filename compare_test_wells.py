import os
import glob
import pandas as pd
import numpy as np
from scipy.stats import pearsonr

# Import shared cleaner and columns
from well_common import (
    FEATURE_COLUMNS,
    LABEL_COLUMN,
    load_and_clean_well,
)

TEST_DIR = "data/test"

def main() -> None:
    test_files = sorted(glob.glob(os.path.join(TEST_DIR, "*.csv")))
    if not test_files:
        print(f"Error: No test CSV files found in {TEST_DIR}!")
        return

    summary_lines = []
    summary_lines.append("=" * 80)
    summary_lines.append("               TEST WELL DATA COMPARISON AND DIAGNOSTICS")
    summary_lines.append("=" * 80)

    print("Analyzing test wells...")

    for file_path in test_files:
        df = load_and_clean_well(file_path)
        well_name = df.loc[0, "Well"]
        
        summary_lines.append(f"\n[ WELL NAME: {well_name} ]")
        summary_lines.append(f"  - Total Data Points: {len(df)}")
        summary_lines.append(f"  - Depth Range:       {df['Depth'].min():.2f}m to {df['Depth'].max():.2f}m (Thickness: {df['Depth'].max() - df['Depth'].min():.2f}m)")

        # Target CNL Statistics
        cnl = df[LABEL_COLUMN].to_numpy()
        summary_lines.append(f"  - Target CNL (Porosity) Distribution:")
        summary_lines.append(f"    * Mean:   {cnl.mean():.4f}")
        summary_lines.append(f"    * Std:    {cnl.std():.4f}")
        summary_lines.append(f"    * Min:    {cnl.min():.4f}")
        summary_lines.append(f"    * 25%:    {np.percentile(cnl, 25):.4f}")
        summary_lines.append(f"    * 50%:    {np.percentile(cnl, 50):.4f}")
        summary_lines.append(f"    * 75%:    {np.percentile(cnl, 75):.4f}")
        summary_lines.append(f"    * Max:    {cnl.max():.4f}")

        # Features Correlation with CNL
        summary_lines.append(f"  - Pearson Correlations with CNL (Target):")
        for col in FEATURE_COLUMNS:
            if col in df.columns:
                feature_vals = df[col].to_numpy()
                # Check for zero variance to avoid pearsonr error
                if feature_vals.std() == 0 or cnl.std() == 0:
                    r = 0.0
                else:
                    r, _ = pearsonr(feature_vals, cnl)
                
                # Highlight CAL or noisy features if necessary
                summary_lines.append(f"    * {col:5s} Correlation R: {r:+.4f} (Mean: {feature_vals.mean():.2f}, Std: {feature_vals.std():.2f})")

        summary_lines.append("-" * 80)

    # Print summary to console
    full_summary = "\n".join(summary_lines)
    print(full_summary)

    # Save to file
    output_path = "well_comparison_summary.txt"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(full_summary)
    print(f"\nComparison report saved to: {output_path}")

if __name__ == "__main__":
    main()
