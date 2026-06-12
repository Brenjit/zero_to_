# JWST CEERS Stage 1 Reduction Documentation

> [!NOTE]
> This document serves as a guide for current Project. It outlines the exact dependencies, environment setup, and HPC batch scripts required to run the Bagley et al. (2023) CEERS Stage 1 reduction pipeline with snowball corrections on Pegasus.


## 1. The Dependency Challenge
The CEERS pipeline relies on an older version of the JWST pipeline (`jwst==1.8.5`). Attempting to install this on newer Python versions (e.g., 3.14) or allowing `pip` to freely upgrade sub-dependencies results in severe breakages:
* **Compilation Errors**: Modern Python lacks pre-compiled wheels for older `astropy`/`asdf`.
* **API Breakages**: Newer versions of `asdf` (v3.0+) removed `asdf.fits_embed`, crashing `snowball_wrapper.py`.
* **Missing Functions**: Newer `photutils` (v2.0+) restructured its API, breaking the CEERS wrapper.
* **CRDS Issues**: Modern `crds` looks for modules in `stdatamodels` that did not exist in older versions.

## 2. Environment Setup (The Solution)

> [!IMPORTANT]
> To avoid compilation errors, you **must** use **Python 3.10**. This ensures that pre-compiled binary wheels are downloaded instantly for older packages.

Run the following commands on the Pegasus login node to create a perfectly aligned, bulletproof environment:

```bash
# 1. Create a fresh environment with Python 3.10
conda create -y -n jwst_pipeline_185 python=3.10
conda activate jwst_pipeline_185

# 2. Install the core JWST package and CRDS
pip install jwst==1.8.5 crds

# 3. Strictly downgrade sub-dependencies to match the 1.8.5 era
pip install "asdf<3.0.0" "stdatamodels<1.0.0" "stpipe<0.5.0" "gwcs<0.19.0" "specutils<1.11.0" "astropy<6.0.0"

# 4. Downgrade CRDS to prevent API crashes, and fix photutils
pip install "crds<12.0.0" "photutils<1.7.0"

# 5. Install OpenCV for snowball shape detection, and pin numpy to prevent astropy conflicts
pip install opencv-python-headless
pip install "numpy<2"
```

## 3. HPC Execution Scripts

Two scripts were created in the `Level_zero/scripts/` directory to automate the processing.

### A. The Python Wrapper: `run_ceers_stage1_batch.py`
This script acts as the bridge between the raw files and the CEERS `snowball_wrapper.py`.
* **Input Directory**: `Level_zero/raw_uncal/`
* **Output Directory**: `Level_zero/stage1_rate_ceers_snowball/`
* **Logic**: It automatically detects `*_uncal.fits` files, checks if their corresponding `*_rate.fits` already exists in the output directory (skipping if true), and calls the official `run_detector1_and_snowballs` function.

### B. The PBS Job Script: `submit_ceers_stage1_batch.pbs`
Since this is a heavy reduction, it should never be run on the login node using `nohup`. 

> [!TIP]
> Always submit using the PBS queue system to allocate dedicated compute nodes and prevent getting banned from the login node!

```bash
# Example PBS directives used:
#PBS -P hpc2601012
#PBS -q project
#PBS -l select=1:ncpus=4:mem=64gb
#PBS -l walltime=12:00:00
```
This script handles activating the `jwst_pipeline_185` conda environment, setting the critical `CRDS_PATH` environment variables so JWST knows where to find calibration files, and executing the Python wrapper.

## 4. Execution Workflow
When a new intern needs to run Stage 1:
1. SSH into Pegasus.
2. Place the raw `*_uncal.fits` files in `Level_zero/raw_uncal/`.
3. Navigate to `Level_zero/scripts/`.
4. Submit the job: `qsub submit_ceers_stage1_batch.pbs`.
5. Check the logs: `tail -f stage1_job.err` and `stage1_job.out`.
6. Retrieve outputs from `Level_zero/stage1_rate_ceers_snowball/`.
