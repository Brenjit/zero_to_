# JWST CEERS Reduction Pipeline Setup

Welcome to the JWST CEERS Reduction Pipeline repository! This repository contains the batch scripts, HPC submission files, and environment configurations needed to successfully run the Bagley et al. (2023) CEERS pipeline on high-performance computing (HPC) clusters (specifically configured for Pegasus).

## Overview

Running the official CEERS reduction pipeline (`jwst==1.8.5`) on modern systems causes significant dependency conflicts due to deprecated modules and updated API structures in newer Python astronomy packages. 

This repository solves these issues by providing a strictly pinned `environment.yml` and a set of automated batch processing scripts that interface with the CEERS pipeline safely.

## Repository Contents

* **`environment.yml`**: The exact Conda environment configuration needed to avoid compilation errors and API breakages.
* **`JWST_CEERS_Stage1_Documentation.md`**: 📖 **READ THIS FIRST**. Comprehensive, step-by-step documentation on the dependency challenges, environment setup, and the pipeline execution workflow.
* **`Important_Bagley.md`**: Reference notes and architectural context regarding the Bagley et al. (2023) CEERS reduction parameters.
* **`scripts/`**:
  * `run_ceers_stage1_batch.py`: Python script that safely loops over `raw_uncal` directories, handles skipped files, and executes the CEERS snowball wrappers.
  * `submit_ceers_stage1_batch.pbs`: The PBS job submission script for HPC queues.
  * `test_imports.py`: A diagnostic script to verify that your environment dependencies are perfectly aligned before submitting a 12-hour job.

## Quick Start (For New Interns/Researchers)

**1. Clone this repository to your HPC workspace:**
```bash
git clone <your-github-repo-url>
cd <repo-name>
```

**2. Clone the official CEERS repository (Do NOT skip this):**
Our Python scripts expect the Bagley code to be available locally.
```bash
mkdir Bagley_git
cd Bagley_git
git clone https://github.com/ceers/ceers-nircam
cd ..
```

**3. Build the Conda Environment:**
This will automatically install Python 3.10 and all correctly downgraded dependencies (`asdf`, `crds`, `photutils`, etc.).
```bash
conda env create -f environment.yml
conda activate jwst_pipeline_185
```

**4. Execute the Pipeline:**
Please read `JWST_CEERS_Stage1_Documentation.md` for full instructions on where to place your raw `.fits` files and how to submit the `.pbs` script to the compute queue.

---
**⚠️ Important Note on Data:** 
Never commit raw `*_uncal.fits` or processed `*_rate.fits` files to this repository. They are enormous and will break the git history. Always keep your FITS files in dedicated data directories outside of version control!
