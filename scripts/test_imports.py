import sys
from pathlib import Path

print("Testing JWST and CEERS imports...")

# 1. Test basic JWST pipeline imports
try:
    import jwst
    print(f"[OK] JWST Pipeline Version: {jwst.__version__}")
except Exception as e:
    print(f"[FAIL] Failed to import jwst: {e}")
    sys.exit(1)

# 2. Test ASDF compatibility (the error you just saw)
try:
    import asdf
    import asdf.fits_embed
    print(f"[OK] ASDF version {asdf.__version__} is compatible.")
except Exception as e:
    print(f"[FAIL] ASDF compatibility issue (likely version too new): {e}")
    print("       Fix by running: pip install 'asdf<3.0.0'")
    sys.exit(1)

# 3. Test CEERS snowball wrapper imports
try:
    SCRIPT_DIR = Path(__file__).resolve().parent
    CEERS_REPO = SCRIPT_DIR.parent / "Bagley_git" / "ceers-nircam"
    sys.path.append(str(CEERS_REPO))
    
    from snowball_wrapper import run_detector1_and_snowballs
    print("[OK] Successfully imported CEERS snowball_wrapper!")
except Exception as e:
    print(f"[FAIL] Failed to import CEERS snowball_wrapper: {e}")
    sys.exit(1)

print("\nAll imports successful! The environment is ready for the batch job.")
