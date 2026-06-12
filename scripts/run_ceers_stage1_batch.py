import os
import sys
import glob
from pathlib import Path
import jwst
import crds

# ---------------------------------------------------------
# 1. PATH SETUP AND IMPORTS
# ---------------------------------------------------------
# Determine base directory (Level_zero) relative to this script
SCRIPT_DIR = Path(__file__).resolve().parent
LEVEL_ZERO_DIR = SCRIPT_DIR.parent

# Add Bagley ceers-nircam repo to path to import official CEERS functions
CEERS_REPO_DIR = LEVEL_ZERO_DIR / "Bagley_git" / "ceers-nircam"
sys.path.append(str(CEERS_REPO_DIR))

try:
    from snowball_wrapper import run_detector1_and_snowballs
except ImportError as e:
    print(f"CRITICAL ERROR: Failed to import CEERS snowball_wrapper.py from {CEERS_REPO_DIR}")
    print(f"Error details: {e}")
    sys.exit(1)

# ---------------------------------------------------------
# 2. CONFIGURATION
# ---------------------------------------------------------
INPUT_DIR = LEVEL_ZERO_DIR / "raw_uncal"
OUTPUT_DIR = LEVEL_ZERO_DIR / "stage1_rate_ceers_snowball"
MAX_CORES = "half"  # Fraction of available cores to use

def main():
    print("=" * 80)
    print("CEERS STAGE 1 BATCH REDUCTION (Bagley et al. 2023)")
    print("=" * 80)
    
    # Print environment and pipeline versions
    print(f"JWST Pipeline Version: {jwst.__version__}")
    # print(f"CRDS Context: {crds.get_default_context()}") # Causing error with older CRDS
    print(f"CRDS Path: {os.environ.get('CRDS_PATH', 'NOT SET')}")
    print("-" * 80)

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Gather input files
    uncal_files = sorted(INPUT_DIR.glob("*_uncal.fits"))
    total_files = len(uncal_files)
    
    if total_files == 0:
        print(f"No *_uncal.fits files found in {INPUT_DIR}")
        sys.exit(0)
        
    print(f"Found {total_files} raw _uncal.fits files to process.")
    
    processed_count = 0
    skipped_count = 0
    failed_count = 0

    # ---------------------------------------------------------
    # 3. PROCESSING LOOP
    # ---------------------------------------------------------
    for i, uncal_path in enumerate(uncal_files, start=1):
        filename = uncal_path.name
        dataset = filename.replace("_uncal.fits", "")
        expected_output = OUTPUT_DIR / f"{dataset}_rate.fits"
        
        print(f"\n[{i}/{total_files}] Processing: {filename}")
        
        # Skip logic
        if expected_output.exists():
            print(f"  -> Skipping. Output already exists: {expected_output.name}")
            skipped_count += 1
            continue
            
        try:
            # Change CWD because the CEERS wrapper expects to run from the base directory
            os.chdir(LEVEL_ZERO_DIR)
            
            # The official CEERS wrapper API: run_detector1_and_snowballs(dataset, inputdir, outputdir, maxcores)
            # Note: the wrapper expects directory names relative to where it's executed, or absolute strings
            run_detector1_and_snowballs(
                dataset=dataset,
                inputdir=str(INPUT_DIR),
                outputdir=str(OUTPUT_DIR),
                maxcores=MAX_CORES
            )
            processed_count += 1
            print(f"  -> Successfully generated: {expected_output.name}")
            
        except Exception as e:
            print(f"  -> ERROR processing {filename}: {e}")
            failed_count += 1

    # ---------------------------------------------------------
    # 4. FINAL SUMMARY
    # ---------------------------------------------------------
    print("=" * 80)
    print("BATCH PROCESSING COMPLETE")
    print(f"Total Input Files: {total_files}")
    print(f"Processed:         {processed_count}")
    print(f"Skipped (Exists):  {skipped_count}")
    print(f"Failed:            {failed_count}")
    print("=" * 80)
    print("RECOMMENDED QC: Visually inspect the generated *_rate.fits files")
    print("in the stage1_rate_ceers_snowball/ directory. Specifically look for")
    print("circular regions where snowballs should have been masked as NaN/DQ.")

if __name__ == "__main__":
    main()
