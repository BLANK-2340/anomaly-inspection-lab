# Anomaly Inspection Lab

An original, dependency-free anomaly-inspection research workbench. Learn only
normal aligned textures, inject a controlled defect, and inspect the spatial
residual, thresholded mask and failure cases. This is a statistical CPU baseline,
not a neural network or industrial benchmark reproduction.

**[Open the public interactive demo](https://blank-2340.github.io/anomaly-inspection-lab/)**
It was deployed and its core controls verified on November 13, 2026.

## Run

Python 3.10+; no packages, downloads or accounts required for local inference.

```bash
python -W error anomaly_lab.py --self-test
python anomaly_lab.py
python anomaly_lab.py --html inspection.html
```

For the interactive browser demo, serve the repository root:

```bash
python -m http.server 8000
```

Open `http://localhost:8000/docs/`. Change position, intensity, defect footprint,
residual variant and global brightness. Click **Run inspection** or **Remove
defect**. Inference is computed in JavaScript using frozen Python-fitted
statistics, not prerecorded predictions. The CLI-generated HTML is instead a
saved-result visualization and is explicitly labeled as such.

The static site lives in `docs/` and can be hosted by this repository's GitHub
Pages configuration, with no additional source repository or paid infrastructure.
Source publication alone does not establish that a demo URL works; the linked
public deployment above has been separately opened and interaction-tested.

## Method and question

Does spatial standardization improve localization compared with raw residuals
when normal texture noise varies across the image?

1. Fit per-pixel sample mean and standard deviation on 48 normal images.
2. Clamp standard deviation below 0.01. Score each pixel with either absolute
   residual or absolute residual divided by its spatial standard deviation.
3. On 32 separate normal images, select the nearest-rank empirical 95th percentile
   of image maximum scores. Classify with a strict `score > threshold` comparison.
4. Freeze this threshold for 32 normal and 32 defect test images. Report confusion
   counts and mean defect-mask intersection-over-union, including missed defects.

The browser bundle binds the Python source hash and exact seed protocol. Browser
and Python residuals are compared at every pixel on 30 perturbed variant cases.
The demo exposes only three held-out synthetic base images. It is not a full
experiment runner and its per-image IoU is not benchmark accuracy.

## Initial measured result

The fixed 24 × 24 synthetic protocol in `python anomaly_lab.py` produced the same
result for both variants: 32/32 defects detected, 1/32 normal false positives,
mean defect IoU 1.0. **There is no demonstrated standardization advantage on
this easy task.** All train, normal-calibration and test seed sets are disjoint.
No externally collected data or pretrained weights are used.

## Harder paired evaluation

The [three-run frozen robustness study](STUDY.md) tests lower-contrast defects
and a brightness shift without adjusting normal-only thresholds. It finds a
region-dependent trade-off, not a universal gain: weak/quiet mean IoU improves
from 0 to 0.5137, while strong/noisy IoU decreases from 0.3849 to 0.3250.
Both variants falsely flag 100% of brightness-shifted normal images. Recorded
normal false-alarm rates also exceed the nominal 5% calibration setting.

```bash
python -W error robustness_study.py
python -W error robustness_study.py --check
python -W error -m unittest discover -s tests -p 'test_*.py' -v
```

## Brightness-compensation extension

The [separate CPU brightness study](BRIGHTNESS.md) tests a global-mean residual
compensator on fresh, fixed held-out identities. Shifted-normal false alarms fall
from 96/96 to 3/96, but broad-defect mean IoU collapses from 0.68166 to 0.00424.
Uniform brightness-like defects can be erased along with harmless brightness.
This is a measured application-assumption trade-off, not a universal improvement.
**The frozen public demo still uses the original, uncompensated model.**

```bash
python -W error brightness_study.py
python -W error brightness_study.py --check
```

## Checks and regeneration

Python 3.10+ and Node 22+ for cross-language tests; no npm dependencies.

```bash
python -W error anomaly_lab.py --self-test
python -W error scripts/build_demo.py --check
node --test tests/browser_engine.test.cjs
```

Regenerate frozen demo assets after changing training or calibration code:

```bash
python scripts/build_demo.py
```

CI runs the same checks. `--check` rejects source/protocol or asset drift.

## Limitations and attribution

- Alignment-dependent, grayscale, tiny original synthetic textures only.
- The empirical quantile is not a guaranteed future false-positive rate.
- The image-level threshold is reused for segmentation, not separately optimized.
- Global brightness changes cause false alarms in the recorded stress test.
  The separate compensated CPU variant reduces those alarms but can erase broad
  defects; it does not update the public demo. Registration changes and real-data
  validation remain untested.
- Not evidence for industrial deployment, anomaly-detection state of the art,
  neural-model quality, GPU acceleration or real-world generalization.
- Statistical reference: [NIST normal distribution and parameter estimation](https://www.itl.nist.gov/div898/handbook/eda/section3/eda3661.htm).
- All implementation, textures and masks are original; no third-party source
  or assets are incorporated. MIT license.

See [continuity, bounded acceptance and remaining work](PROGRESS.md).
