# Brightness compensation and the defects it can erase

Research question: can subtracting a global nuisance offset prevent brightness
false alarms without destroying useful defect evidence? This separate CPU
extension studies that trade-off. **It is not installed in the public demo.**
The original implementation, frozen browser model and prior study are unchanged.

## Algorithm and assumption

Let `r_i = image_i - normal_mean_i`. The existing standardized score is
`abs(r_i) / normal_scale_i`. The new mean-compensated score is
`abs(r_i - mean(r)) / normal_scale_i`. The offset estimator sees only the input
image and frozen normal means, not the defect mask, injected brightness or labels.
The original spatial scales are shared; they are not refitted after centering.
Each variant receives its own normal-only calibration threshold.

Subtracting the residual mean removes a spatially constant additive brightness
change, apart from floating-point roundoff, **provided no pixels saturate**.
This encodes an application assumption: global brightness is harmless. It cannot
discover whether that assumption is correct from an image alone.

In an otherwise exact normal image, a constant positive defect of magnitude `d`
covering fraction `f` of pixels adds `f*d` to the estimated offset. Its residual
becomes `(1-f)*d` inside the defect and `-f*d` outside. Broad defects can therefore
be suppressed or localized to the wrong region. A full-frame brightness-like
defect is removed entirely in this noiseless example. Pixel scales then affect
which remaining residuals cross the threshold.

## Frozen protocol

`brightness_study.py` fixes three new, disjoint runs with offsets
400000/500000/600000. Each uses 48 normal fitting identities, 32 separate normal
calibration identities and 32 held-out base identities. All identities are also
disjoint from the earlier robustness study. Per-pixel mean/sample standard
deviation and floor 0.01 are unchanged. Each variant is calibrated once per run
using rank 31 of 32 normal image-maximum scores, with strict `score > threshold`.
No shifted examples or test labels enter calibration; no test threshold tuning,
test-based early stopping or policy selection is performed.

All nine conditions reuse each held-out base and compare both variants. There
are **96 unique held-out bases, 864 paired condition inputs and 1728 variant
observations**, not 1728 independent images. Every image is 24 by 24. Additive
perturbations outside [0,1] raise an error; none occur on this fixed protocol.
No clipping is used to conceal saturation or break the shift-invariance check.

- Normal: no perturbation.
- Brightness up/down: uniform +0.08/-0.08, designated harmless, empty defect mask.
- Quiet spot: +0.08 in a 4 by 4 box at x=4, y=8; with and without +0.08 brightness.
- Noisy spot: +0.08 in a 4 by 4 box at x=16, y=8, without brightness shift.
- Broad defect: +0.08 in x=0..17, all 24 rows, covering 432/576 pixels;
  with and without +0.08 brightness.
- Uniform defect: +0.08 over the entire frame, designated defective. Its image
  pixels are **exactly identical** to the brightness-up normal condition.
  Only the ground-truth interpretation differs. This is an intentional
  identifiability diagnostic, not another independent observation.

## Measured CPU results

Executed November 20, 2026. Every row has 96 samples, paired across variants.
For normal rows, flagged means false alarm; for defect rows, it means image-level
detection. A defect detection can come from a wrongly localized pixel. IoU is the
mean per-image mask intersection/union, including missed defects. Normal IoU is
undefined and omitted. Results are rounded here; full values and raw evidence
are in `results/brightness.json`.

| Condition | Standardized flagged | Compensated flagged | Standardized defect IoU | Compensated defect IoU |
|---|---:|---:|---:|---:|
| Normal | 3/96 | 3/96 | n/a | n/a |
| Brightness +0.08, normal | 96/96 | 3/96 | n/a | n/a |
| Brightness -0.08, normal | 96/96 | 3/96 | n/a | n/a |
| Quiet spot | 96/96 | 96/96 | 0.99751 | 0.99812 |
| Quiet spot + brightness | 96/96 | 96/96 | 0.05314 | 0.99812 |
| Noisy spot | 47/96 | 46/96 | 0.04607 | 0.04289 |
| Broad defect | 96/96 | 78/96 | 0.68166 | 0.00424 |
| Broad defect + brightness | 96/96 | 78/96 | 0.85394 | 0.00424 |
| Uniform defect | 96/96 | 3/96 | 0.52309 | 0.00005 |

Compensation reduced shifted-normal false alarms from 100% to 3.125%, matching
the unshifted rate on these same bases. This is not a future-risk guarantee.
It preserved small quiet-defect localization under shift, but slightly worsened
noisy-spot results and catastrophically degraded broad-defect localization.
The observed uniform-defect detections after compensation match normal noise
alarms, not recovery of the removed uniform signal. No variant can distinguish
the two pixel-identical, differently labeled uniform conditions from image
values alone. Operational use requires a defensible nuisance/defect definition.

The JSON records per-run thresholds, all seed identities, estimated offsets,
maximum scores, pixel TP/FP/FN and summaries. It includes the sample standard
deviation of image detection rates over three runs, not confidence intervals.
Seeds vary synthetic noise only, not a population of texture families. Large
run differences occur on the noisy and broad cases. No statistical significance,
universal improvement, real-data generalization or industrial claim is made.

## Reproduce and audit

Python 3.10+, standard library only:

```bash
python -W error brightness_study.py
python -W error brightness_study.py --check
python -W error -m unittest discover -s tests -p 'test_brightness.py' -v
```

`--check` recomputes all three runs and compares exact canonical artifact bytes,
including SHA256 identities of the original core and this study source.
`--write` regenerates the task-owned evidence file after an intentional change.
Hashes establish source/artifact consistency, not external attestation.

Seven test groups cover an analytic area-attenuation example, no mutation,
constant-shift invariance, pixel-identical nuisance/defect ambiguity, exact
geometry and saturation rejection, known confusion/IoU/threshold ties, independent
normal-only quantiles, disjoint identities, held-out-pixel poisoning that leaves
thresholds unchanged, scalar reconstruction of every observation, independent
aggregation and exact artifact regeneration. Existing core, earlier study and
browser parity checks remain required.

All added algorithms, images, masks and tests are original and MIT licensed.
No external code, data, assets or private research were incorporated. The model
remains alignment-dependent and synthetic; nonuniform illumination, registration,
saturation handling and real-world inspection remain unvalidated.
