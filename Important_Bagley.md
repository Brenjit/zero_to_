# Bagley et al. 2023 — CEERS NIRCam Reduction Master Workflow

## Paper

**Bagley et al. 2023, ApJL, 946, L12**
**Title:** *CEERS Epoch 1 NIRCam Imaging: Reduction Methods and Simulations Enabling Early JWST Science Results*

This is the principal reduction paper for CEERS Epoch 1 NIRCam imaging. It describes how the CEERS team reduced JWST/NIRCam imaging from raw data to public science-ready mosaics using the official JWST Calibration Pipeline plus custom corrections.

---

# 1. Why this paper matters for my workflow

This paper is not only a science-result paper. It is a practical reduction-method paper for CEERS NIRCam data.

The main point is:

> CEERS NIRCam images were not reduced by simply running the default JWST pipeline once. The CEERS team used the JWST Calibration Pipeline, but inserted custom steps to handle real detector/instrument effects such as snowballs, wisps, 1/f striping, persistence, astrometric offsets, variance-map problems, drizzle-related issues, and residual background structure.

For my high-redshift galaxy / UVLF work, this matters because small systematic errors in background, astrometry, noise, or artifacts can create false dropout candidates or bias photometry.

---

# 2. CEERS Epoch 1 observations covered by this paper

The paper focuses on the first CEERS NIRCam epoch, observed in 2022 June.

The relevant NIRCam pointings are:

* NIRCam1
* NIRCam2
* NIRCam3
* NIRCam6

The filters are:

## Short-wavelength filters

* F115W
* F150W
* F200W

## Long-wavelength filters

* F277W
* F356W
* F410M
* F444W

The filter pairs used in CEERS Epoch 1 were:

* F115W + F277W
* F115W + F356W
* F150W + F410M
* F200W + F444W

Important high-redshift point:

The filters were observed in an order designed to reduce the risk that fading persistence from previous observations would mimic a Lyman break. This is directly relevant for z ≳ 9 galaxy selection, where a false non-detection or false red color can affect dropout selection.

---

# 3. Pipeline version and calibration context used in the paper

For the CEERS DR0.5 reduction described in the paper:

* JWST Calibration Pipeline version: **jwst 1.7.2**
* CRDS pmap: **0989**
* NIRCam imap: **0232**

The CRDS pmap 0989 included in-flight NIRCam dark, distortion, bad-pixel mask, read-noise, and superbias reference files. It also included ground flats corrected for in-flight performance and updated photometric calibration reference files.

For my own workflow, I must always record:

* `jwst` version
* `CRDS_CONTEXT`
* `CRDS_PATH`
* `CRDS_SERVER_URL`
* Python environment name
* Git commit of any CEERS/custom scripts
* Date of processing
* Which files were processed
* Which stages were completed
* Which steps deviate from Bagley et al.

If I use a newer JWST pipeline version, I should not pretend that I reproduced DR0.5 exactly. I should write:

> Reduction philosophy follows Bagley et al. 2023, but pipeline version and CRDS context are updated.

---

# 4. Reduction-script map from Bagley et al. Table 2

This is the core script map from the paper.

| Reduction step                                             | Script / parameter file              |
| ---------------------------------------------------------- | ------------------------------------ |
| Stage 1 + snowball correction                              | `snowball_wrapper.py`                |
| Wisp subtraction                                           | `wispsub.py`                         |
| 1/f noise removal                                          | `remstriping.py`                     |
| Stage 2                                                    | `image2_1.7.2.asdf`                  |
| SkyMatch + outlier detection                               | `image3_part1.asdf`                  |
| Astrometric alignment                                      | `run_tweakreg.py`                    |
| Individual background subtraction + variance map rescaling | `skywcsvar.py`                       |
| Mosaic creation                                            | `image3_nircam[pointing]_[chn].asdf` |
| Mosaic background subtraction                              | `mosaic_background.py`               |

The paper states that the team provides parameter files, custom Python routines, and batch scripts for running the steps on all four NIRCam pointings.

For my workflow, this table is the authoritative order to keep in mind.

---

# 5. Full conceptual workflow

The paper’s reduction flow can be written as:

```text
raw *_uncal.fits
   ↓
Stage 1 detector-level correction + snowball correction
   ↓
*_rate.fits
   ↓
wisp subtraction
   ↓
1/f noise removal
   ↓
corrected *_rate.fits
   ↓
Stage 2 individual image calibration
   ↓
*_cal.fits
   ↓
Stage 3 preparation: SkyMatch + outlier detection
   ↓
astrometric alignment
   ↓
individual pedestal/background subtraction
   ↓
variance map rescaling
   ↓
bad variance correction
   ↓
drizzle / resample mosaic creation
   ↓
mosaic-level background subtraction
   ↓
final multiextension science mosaic
```

My directory mapping can be:

```text
raw_uncal/
   ↓
stage1_rate/
   ↓
corrected_rate/
   ↓
stage2_cal/
   ↓
skymatch_cal/
   ↓
stage3_i2d/
   ↓
bkgsub/
```

But I should remember: this directory structure is mine. The paper gives the scientific order and scripts, not necessarily my exact folder names.

---

# 6. Stage 1 — Detector-level corrections

## Purpose

Stage 1 converts raw ramps into count-rate images.

Input:

```text
*_uncal.fits
```

Output:

```text
*_rate.fits
```

Units:

```text
counts / second
```

## Standard Stage 1 operations

According to Bagley et al., Stage 1 includes:

* data-quality array initialization
* saturated-pixel identification
* superbias subtraction
* reference-pixel correction
* nonlinearity correction
* dark-current subtraction
* cosmic-ray jump detection
* ramp fitting to determine average count rate per pixel

The CEERS team adopted default parameter values for these Stage 1 steps, but they ran Stage 1 together with their custom snowball correction.

---

# 7. Snowball correction

## What snowballs are

Snowballs are large cosmic-ray events in NIRCam images. They can affect hundreds of pixels and have a roughly circular morphology.

Bagley et al. report roughly 25–30 snowballs per detector in a ~900 s exposure.

The default JWST pipeline often flags the central core of a snowball but can leave diffuse wings in the Stage 1 count-rate maps.

This matters because the CEERS dithering is limited; the paper explicitly notes that three dithers are not enough to remove snowballs reliably from the final coadded mosaics.

## Paper method

The CEERS team identifies snowballs using the `GROUPDQ` arrays.

Detailed method:

1. Identify large contiguous sets of pixels flagged as jumps, i.e. `JUMP_DET`.
2. Divide snowballs into two classes:

   * larger snowballs needing larger masks
   * smaller snowballs needing less aggressive masks
3. Median-filter the `GROUPDQ` arrays using two-dimensional top-hat kernels.
4. Use kernel radii:

   * 7 pixels
   * 15 pixels
5. Include saturated pixels inside the large snowball groups.
6. Grow the snowball masks by binary dilation.
7. Use a two-stage top-hat growing kernel with radii:

   * 7 pixels
   * 35 pixels
8. Add this updated snowball mask to the `GROUPDQ` array.
9. Re-run ramp fitting.
10. The affected-pixel flux is determined from the unflagged ramp samples, excluding the newly identified cosmic-ray jump.

## Script

```text
snowball_wrapper.py
```

The script:

* runs Stage 1 once
* saves ramps from the first ramp-fitting run
* identifies snowballs
* grows their footprints
* flags them as cosmic rays
* runs ramp fitting again
* creates corrected count-rate images

## My workflow rule

Do not go to Stage 2 until Stage 1 has completed for all intended raw files and the resulting rate files have been inspected.

For high-redshift science, I should inspect candidate regions in individual exposures, because snowballs and snowball persistence can create false compact detections.

---

# 8. Wisp subtraction

## What wisps are

Wisps are stray-light features caused by reflected light from secondary mirror supports.

In CEERS, wisps are most relevant for:

```text
Filters: F150W and F200W
Detectors: A3, A4, B3, B4
```

They are variable in brightness from exposure to exposure.

## Paper method

The CEERS team used NIRCam team wisp templates.

The method:

1. Use the updated wisp templates released on 2022 August 26.
2. Apply the flat field to the science image so that it matches the flat-fielded wisp templates.
3. Perform a very cold source detection using Photutils.
4. Use high detection threshold:

   ```text
   5.5 sigma
   ```
5. This masks large bright sources while avoiding masking the wisp itself.
6. Smooth the wisp template with a Gaussian kernel:

   ```text
   sigma = 2 pixels
   ```
7. For a set of coefficients `a`, minimize the median absolute deviation of:

   ```text
   I - aW
   ```

   where:

   * `I` = flat-fielded masked image
   * `W` = smoothed wisp template
   * `a` = scale factor
8. In most cases the best scale factor is less than 1.
9. Scale the original unsmoothed wisp template by `a`.
10. Subtract the scaled original template from the original un-flat-fielded and unmasked image.

## Script

```text
wispsub.py
```

## Caveats from the paper

The paper says the wisp subtraction was still preliminary.

Important caveats:

* early wisp templates contained ghost images of bright sources
* this can create local oversubtraction
* oversubtraction level is about 3–4%
* weak wisps may exist in F115W, but no F115W template was available at that time, so F115W was left uncorrected

## My workflow rule

For F150W and F200W, wisp correction must be considered before Stage 2.

For my F150W work, this is directly relevant.

I should visually compare:

```text
rate image before wisp subtraction
rate image after wisp subtraction
difference image
```

If a region contains high-z candidates, I should inspect whether the candidate lies near a wisp residual or oversubtraction region.

---

# 9. 1/f noise subtraction

## What 1/f noise is

1/f noise is correlated detector readout noise. It appears as horizontal and vertical striping patterns that vary row-to-row and column-to-column.

This is an additive effect.

Because it is additive, Bagley et al. note that it should be removed before applying the multiplicative flat-field correction. However, the pattern is easier to measure on flat-fielded images.

## Paper method

The CEERS method:

1. Temporarily apply the flat field to the count-rate map to measure the striping pattern.
2. Subtract the measured pattern from the original count-rate image.
3. Mask all bad pixels where DQ flag > 0.
4. Mask source flux using a tiered Photutils source-detection method.
5. Use four Gaussian kernels:

   ```text
   sigma = 25, 15, 5, 2 pixels
   ```
6. These kernels are used to detect and mask both extended and compact sources.
7. Fit a Gaussian to the masked pixel distribution to estimate the sky pedestal.
8. Measure the striping pattern using sigma-clipped median values.
9. Use 2 sigma clipping.
10. Measure first along rows, then along columns.
11. For horizontal striping, measure and remove the pattern amplifier-by-amifier.
12. If too many pixels are masked in a given amplifier-row, use the full-row median instead.

## Script

```text
remstriping.py
```

## Why amplifier-by-amplifier matters

The paper notes that in some images, especially SW filters, amplifier-to-amplifier differences can vary by about 3–5%.

Therefore amplifier-level correction is better than using a single full-row median for the whole detector.

## My workflow rule

For every Stage 1 F150W rate image, I should run or at least evaluate 1/f correction before Stage 2.

I should check:

```text
before 1/f correction
row-median profile
column-median profile
horizontal model
vertical model
after 1/f correction
```

The final catalog should not be based on mosaics with visible striping residuals.

---

# 10. Persistence issue

## Paper case

In NIRCam2, the repeated F200W+F444W observations were affected by strong persistence on SW detector A3.

Bagley et al. traced the pattern to earlier observations of Jupiter from Program 1022. They used earlier detector images to build a mask and also manually masked the wings of the affected region.

## Method used in the paper

1. Search earlier MAST observations to identify possible source of persistence.
2. Use earlier images to construct a mask of affected pixels.
3. Use thresholds:

   * > 20 MJy/sr in the first exposure
   * > 10 MJy/sr in the second exposure
4. Manually mask a wider polygon around the affected region.
5. Apply the mask to snowball-corrected count-rate maps.
6. Set affected science pixels to zero.
7. Set affected DQ values to `DO_NOT_USE`.
8. Then continue with wisp correction and 1/f correction.

## High-redshift warning

Persistence can mimic high-redshift dropout behavior.

Therefore:

> A compact source that appears in only a subset of filters must be checked in individual exposures and against detector-fixed persistence patterns.

For my work, this matters especially for z ~ 9 candidates.

---

# 11. Stage 2 — Individual image calibration

## Purpose

Stage 2 converts Stage 1 count-rate images into calibrated individual exposures.

Input:

```text
corrected *_rate.fits
```

Output:

```text
*_cal.fits
```

Units:

```text
MJy / sr
```

## Main Stage 2 operations

Bagley et al. state that Stage 2 includes:

* flat-fielding
* flux calibration
* conversion from counts/s to MJy/sr

The CEERS DR0.5 reduction used default Stage 2 values.

## Parameter file

```text
image2_1.7.2.asdf
```

## Important caveat

The paper emphasizes that the NIRCam flats and flux calibration reference files were still early Cycle 1 products.

Therefore, detector-to-detector relative calibration was not perfect.

The paper later finds residual detector-to-detector photometric offsets at approximately the 2–4% level, with some residuals up to about 5%.

## My workflow rule

When I compare my photometry to CEERS public catalogs, I must remember that early JWST calibration uncertainty is part of the error budget.

If I use newer CRDS reference files, I should record that my calibration may differ from Bagley DR0.5.

---

# 12. Stage 3 — Ensemble processing

## Purpose

Stage 3 combines calibrated individual exposures into final mosaics.

Bagley et al. do not run Stage 3 as one black box. They split it into several controlled operations.

The Stage 3 operations include:

* astrometric alignment
* background matching
* outlier detection
* individual-image background/pedestal subtraction
* variance-map corrections
* resampling/drizzling
* mosaic-level background subtraction

---

# 13. SkyMatch + outlier detection

## Parameter file

```text
image3_part1.asdf
```

The paper says that after customized astrometric correction, they run the `OutlierDetection` step of JWST Stage 3 with default parameter values.

Outlier detection is meant to identify bad pixels or cosmic rays that survived Stage 1 jump detection.

For my workflow, I must be careful because CEERS has limited dithers. Limited overlap means some outliers can survive and some real sources can be affected if parameters are too aggressive.

---

# 14. Astrometric alignment

## Why it matters

Astrometric alignment is crucial for:

* photometry
* colors
* morphology
* photometric redshifts
* high-z dropout selection

If the images are misaligned, small-aperture colors become biased.

## Paper method

Bagley et al. used a modified version of `TweakReg`.

The modifications allowed:

* more fitting parameters
* custom input catalogs

They created SourceExtractor catalogs for each individual input image.

They used:

```text
SourceExtractor windowed coordinates
```

because these improve centroiding, especially for compact sources.

The absolute reference catalog was derived from:

```text
HST F160W 0.03 arcsec/pixel mosaic in EGS
```

The HST reference frame was tied to:

```text
Gaia-EDR3
```

## Alignment sequence

1. First align images relative to each other.
2. Determine x and y shifts between images of the same detector.
3. Then align images to the HST F160W reference catalog.
4. Allow x/y shifts and rotations.
5. For LW images, also allow a scale factor to account for additional distortion across the larger detectors.

## Alignment quality reported

The paper reports:

```text
relative astrometry: ~3–6 mas per source
HST-to-NIRCam absolute alignment: ~12–15 mas
NIRCam-to-NIRCam alignment: ~5–10 mas
```

There was one exception in part of NIRCam3, where alignment relative to HST F160W was worse in a ~1 arcmin region. For that case, they aligned F277W to F160W excluding problematic sources, then used F277W as the reference for the other filters.

## Script

```text
run_tweakreg.py
```

## My workflow rule

For any final mosaic or catalog, I must check inter-filter astrometry.

For high-z candidates, I should inspect cutouts in all bands after alignment.

A visually clean detection is not enough if the astrometry is not verified.

---

# 15. Individual background subtraction and variance-map rescaling

## Script

```text
skywcsvar.py
```

Before making mosaics, Bagley et al. apply three extra corrections to calibrated individual images.

---

## 15.1 Pedestal subtraction

Problem:

`SkyMatch` did not successfully match the background across all detectors, likely because the small CEERS dithers produce little or no overlap between detectors.

Method:

1. Mask bad pixels.
2. Mask source flux using the tiered masks from the 1/f correction.
3. Fit a Gaussian to the distribution of unmasked, sigma-clipped pixel fluxes.
4. Take the Gaussian peak as the image pedestal.
5. Subtract this single pedestal value from each image.
6. Update headers to record the subtracted value.

---

## 15.2 Sky variance estimation and VAR_RNOISE rescaling

Method:

1. Mask sources in four tiers.
2. Block-sum the image in 7 × 7 pixel blocks.
3. Use `astropy` `biweight_midvariance` to estimate robust variance in blocks where no pixels were masked.
4. Convert to equivalent per-pixel variance by dividing by 49.
5. Scale the `VAR_RNOISE` array to reproduce this measured variance.

Reason:

`VAR_RNOISE` contributes to the inverse-variance weighting during drizzle. Rescaling helps the final error arrays predict sky RMS better, at least on scales large enough to avoid pixel-to-pixel drizzle correlations.

---

## 15.3 Zero-variance correction

Problem:

Some known bad pixels had exactly zero values in variance arrays.

If left uncorrected, these pixels can produce artificially low RMS regions in the final error map, causing spurious source detections.

Method:

For each individual image, replace pixels that are exactly zero in the variance arrays with:

```python
numpy.inf
```

Reason:

This ensures those pixels are properly down-weighted during drizzling.

## My workflow rule

When building mosaics, never ignore variance arrays.

I must check:

```text
VAR_POISSON
VAR_RNOISE
VAR_FLAT
ERR
WHT
```

and make sure there are no zero-variance holes causing fake high-significance detections.

---

# 16. Mosaic creation / drizzle / resampling

## Parameter file

```text
image3_nircam[pointing]_[chn].asdf
```

where `chn` refers to SW or LW.

## Paper method

Bagley et al. create individual mosaics for each pointing using Stage 3 `Resample`.

This uses the drizzle algorithm with inverse-variance weighting.

They drizzle all mosaics onto a common WCS aligned with HST mosaics in the EGS field.

## Output pixel scale

```text
0.03 arcsec / pixel
```

## Pixfrac

```text
pixfrac = 1
```

## Why pixfrac = 1?

The paper chooses `pixfrac = 1` because most CEERS regions have at most three exposures. With too small a pixfrac, the output pixels would be poorly sampled.

## Cost of pixfrac = 1

The cost is stronger correlated noise in the final mosaics.

This matters because photometric uncertainties derived directly from pixel RMS or pipeline ERR maps can be underestimated.

## My workflow rule

For source detection and photometry, I must remember:

> The final mosaic pixels are correlated because of drizzle. Therefore empirical empty-aperture noise is necessary for reliable photometric errors.

---

# 17. Mosaic-level background subtraction

## Script

```text
mosaic_background.py
```

This is the final background-subtraction step applied after mosaics are created.

The goal is to remove residual background structure from the coadded images.

---

## 17.1 Rough background removal

Bagley et al. first remove large-scale fluctuations.

The Figure 7 flowchart gives the rough background setup:

```text
background2d
box_size = 100
filter_size = 3
sigma_clip = 3
bkg_estimator = BiweightLocationBackground
exclude_percentile = 90
interpolator = BkgZoomInterpolator
```

This rough background is subtracted first.

---

## 17.2 Ring-median filtering

After rough background removal:

1. Estimate RMS using `biweight_scale`.
2. Mask pixels in the original image that are more than 5 × RMS above the rough background level.
3. Apply a ring-median filter to the masked original image.

The Figure 7 flowchart gives:

```text
inner_radius = 80
ring_width = 4
```

This gives the first good estimate of background while preserving wings of most galaxies except the largest ones.

---

## 17.3 Four-tier source masking

The paper masks sources in four tiers.

Purpose:

* Tier 1: most extended galaxies
* Later tiers: progressively smaller galaxies

The image is convolved with Gaussian kernels and sources above a fixed threshold are detected and masked.

The threshold is:

```text
1.5 sigma
```

The masks are grown by circular top-hat dilation.

The Figure 7 flowchart lists tier parameters:

```text
sigma = 25, 15, 5, 2
N     = 15, 10, 3, 1
r     = 33, 25, 21, 19
```

where:

* `sigma` = Gaussian convolution width
* `N` = minimum number of connected pixels
* `r` = top-hat dilation radius in pixels

The CEERS team constructs masks for each filter and includes pixel-aligned HST filters:

```text
F606W
F814W
F105W
F125W
F140W
F160W
```

They then merge masks from all filters into one combined mask.

Reason:

A source may be below detection threshold in one filter but visible in another. Merging all masks prevents source flux from biasing the background in any band.

---

## 17.4 Final background model

The final background is measured in unmasked regions using Photutils `Background2D`.

Figure 7 gives:

```text
box_size = 10
filter_size = 5
sigma_clip = 3
bkg_estimator = BiweightLocationBackground
exclude_percentile = 90
mask = mask all filters
interpolator = BkgZoomInterpolator
```

Then the final background model is subtracted from the mosaic.

## Important scientific caveat

The paper says this background subtraction does very well at removing residual wisps and other background variations, but it intentionally suppresses the wings of bright galaxies to improve detection of faint neighbors.

## My workflow rule

For faint high-z candidates near bright galaxies, I must inspect:

```text
SCI
SCI_BKSUB
BKGD
BKGMASK
```

A candidate near a bright object may be affected by background subtraction or source-wing suppression.

---

# 18. Depth estimation

Bagley et al. estimate 5σ limiting magnitudes on the background-subtracted mosaics.

Method:

1. Place apertures across each image.
2. Avoid source flux and bad pixels.
3. Use aperture radii from:

   ```text
   r = 0.05 arcsec to r = 1.5 arcsec
   ```
4. Estimate robust 1σ noise in each aperture.
5. Fit a second-order polynomial to noise as a function of aperture size.
6. Estimate the noise in:

   ```text
   r = 0.1 arcsec aperture
   ```
7. Use stacked PSFs to measure enclosed flux fraction in that aperture.
8. Correct the noise estimate to total flux using the PSF aperture correction.
9. Report 5σ depths.

The CEERS Epoch 1 NIRCam depths are approximately:

```text
F115W  ~29.1 AB
F150W  ~29.0 AB
F200W  ~29.2 AB
F277W  ~29.2 AB
F356W  ~29.2 AB
F410M  ~28.4 AB
F444W  ~28.6 AB
```

Exact values vary slightly by pointing.

## My workflow rule

For my own catalog, I should not simply trust the pipeline ERR image for final limiting depth.

I should estimate empirical aperture noise from the reduced mosaics, avoiding sources and bad pixels.

---

# 19. Flux calibration check

Bagley et al. evaluate relative detector-to-detector flux calibration.

They use two methods.

## Method 1

Compare NIRCam photometry to HST/WFC3 and Spitzer/IRAC photometry using bright galaxies.

Examples:

* NIRCam F115W compared to HST F125W
* NIRCam F150W compared to HST F160W
* NIRCam F356W compared to IRAC 3.6 μm
* NIRCam F444W compared to IRAC 4.5 μm

They PSF-match images and use SourceExtractor dual-image mode.

## Method 2

For filters without direct comparable imaging data, they use synthetic NIRCam magnitudes from best-fit SPS models in the CANDELS catalog.

Used for:

* F200W
* F277W
* F410M

## Result

With CRDS pmap 0989, residual detector-to-detector offsets remain at the few-percent level.

Approximate statement:

```text
relative and absolute NIRCam calibration uncertainty: ~2–4%, sometimes up to ~5%
```

## My workflow rule

When comparing my photometry to CEERS catalogs or doing SED fitting, remember that early calibration uncertainty is real.

---

# 20. Final CEERS mosaic structure

The released NIRCam mosaics have 12 FITS extensions.

## NIRCam mosaic extensions

1. `SCI_BKSUB`
   Background-subtracted science data, units MJy/sr.

2. `SCI`
   Science data before final mosaic background subtraction, units MJy/sr.

3. `ERR`
   Resampled uncertainty estimate as standard deviation.

4. `CON`
   Context image encoding which input images contribute to each output pixel.

5. `WHT`
   Weight image giving relative pixel weights.

6. `VAR_POISSON`
   Resampled Poisson variance map.

7. `VAR_RNOISE`
   Resampled read-noise variance map, rescaled to include robust sky variance estimate.

8. `VAR_FLAT`
   Resampled flat-field variance.

9. `BKGD`
   Background model subtracted from the science image.

10. `BKGMASK`
    Tiered source mask used to create the background.

11. `HDRTAB`
    Table of FITS keyword values from input images.

12. `ASDF`
    JWST data-model metadata.

## My photometry usage

For photometry:

```text
Use SCI_BKSUB as the main science image.
Use SCI to check what changed after background subtraction.
Use ERR and WHT for weight/error context, but do not rely on them alone.
Use BKGD to inspect background subtraction.
Use BKGMASK to check whether candidate regions were included/excluded in background estimation.
Use empirical empty-aperture RMS for final photometric errors.
```

---

# 21. Known issues from the paper

The paper explicitly says DR0.5 is a best-effort early JWST reduction.

Known issues:

## 21.1 Early reference files

Some calibration reference files were still preliminary.

This affects:

* flats
* flux calibration
* detector-to-detector zero-points

Residuals remain at the few-percent level.

---

## 21.2 Wisp-template limitations

Wisp templates contained some source ghosts because early observations did not have enough dithers to fully remove all input sources from the template stacks.

This can cause:

```text
local oversubtraction at ~3–4%
```

---

## 21.3 More cosmic rays in NIRCam3 and NIRCam6

NIRCam3 and NIRCam6 have more cosmic rays because exposures in those pointings are longer.

The same reduction parameters were used for all four pointings in DR0.5, but the paper notes that future reductions would tune jump detection and outlier detection more carefully.

---

## 21.4 Persistence not fully checked everywhere

The strong NIRCam2 persistence case was masked, but the paper states that a careful persistence check had not yet been done for the majority of images.

For high-z work, this is very important.

---

## 21.5 Correlated noise not corrected

The paper says the mosaics do not include a correction for correlated noise introduced by drizzle.

Because `pixfrac = 1`, pixel-to-pixel correlations are strong.

Photometric uncertainties can therefore be underestimated unless empirical noise is measured.

---

## 21.6 F115W depth issue

CEERS planned F115W to be deeper than other SW filters, but the measured F115W depth is comparable to F150W and F200W.

Reason:

* F115W is more read-noise dominated than expected.
* NIRCam sensitivity in other SW filters is better than prelaunch predictions.

This matters for z ≳ 9.5 dropout selection because the dynamic range between F115W and F150W is smaller than originally expected.

---

# 22. Rules for my CEERS reduction workflow

## Rule 1

Do not treat JWST pipeline output as automatically science-ready.

## Rule 2

Complete Stage 1 for all raw files before going to Stage 2.

## Rule 3

For F150W and F200W, consider wisp subtraction before Stage 2.

## Rule 4

Run or evaluate 1/f noise subtraction on individual count-rate images before Stage 2.

## Rule 5

Inspect individual exposures for high-z candidates, not only final mosaics.

## Rule 6

Check astrometry across filters before trusting colors.

## Rule 7

Use empirical aperture noise for final catalog errors.

## Rule 8

Inspect `SCI`, `SCI_BKSUB`, `BKGD`, and `BKGMASK` near important candidates.

## Rule 9

Record all pipeline versions, CRDS contexts, scripts, and deviations.

## Rule 10

If using newer JWST pipeline or newer CRDS than Bagley DR0.5, label the reduction as Bagley-inspired, not exact Bagley DR0.5 reproduction.

---

# 23. Antigravity / coding-agent instruction

When using Antigravity or any coding assistant, give it this rule:

> Follow Bagley et al. 2023 as the principal CEERS NIRCam reduction workflow. Do not invent a new pipeline order. Implement or inspect the steps in this order: Stage 1 with snowball correction, wisp subtraction, 1/f noise removal, Stage 2 calibration, SkyMatch/outlier detection, astrometric alignment, individual pedestal subtraction and variance-map correction, drizzle/resample mosaic creation, final mosaic background subtraction, then photometric QC.

For every generated script, Antigravity should include:

* input directory
* output directory
* expected input suffix
* expected output suffix
* log file path
* skip-existing-file logic
* pipeline version printout
* CRDS context printout
* exception handling
* final count summary
* before/after QC suggestion

No script should silently overwrite existing products unless explicitly requested.

---

# 24. My immediate current status mapping

Current directory:

```text
/home/iit-t/pegasus_mount/Brenjit/Level_zero
```

Current state:

```text
raw_uncal/       = 8 files
stage1_rate/     = 2 files
corrected_rate/  = 0 files
stage2_cal/      = 0 files
stage3_i2d/      = 0 files
bkgsub/          = 0 files
```

According to the Bagley workflow, I am still at the beginning:

```text
raw *_uncal.fits
   ↓
Stage 1 + snowball correction
   ↓
*_rate.fits
```

Therefore, my immediate target is:

```text
stage1_rate/ = 8 rate files
```

Only after that should I move to:

```text
wisp subtraction + 1/f correction
```

Then:

```text
Stage 2 calibration
```

Then:

```text
Stage 3 mosaic construction
```

---

# 25. Final memory sentence

Bagley et al. 2023 is my principal CEERS NIRCam reduction reference. The core lesson is:

> For CEERS high-redshift photometry, the science-ready mosaic is not just the output of the default JWST pipeline. It is the result of controlled detector correction, artifact removal, astrometric alignment, variance-map treatment, drizzle choices, and careful background subtraction. Every one of these choices can affect dropout colors, photometric redshifts, completeness, and UVLF measurements.
