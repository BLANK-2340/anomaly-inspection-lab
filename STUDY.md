# Frozen robustness study

Question: when does per-pixel standardization help or hurt a normal-only residual
detector? This deliberately bounded experiment uses original, aligned 24 × 24
synthetic grayscale textures, not an industrial dataset or a paper reproduction.

## Protocol, fixed before this run

Three independent run offsets: 100000, 200000, 300000. For each offset:

- Fit on normal seeds offset + 1000 through 1047 (48 images).
- Calibrate once on normal seeds offset + 10000 through 10031 (32 images).
- Freeze the empirical 95th-percentile image-maximum thresholds separately for
  raw and spatially standardized residuals; retain strict `>` decision ties.
- Test seeds offset + 30000 through 30031 (32 images), reused in all six
  conditions and both variants for paired comparison. All seed sets across
  training, calibration, test and independent run offsets are disjoint.
- Conditions: normal, normal with +0.08 brightness shift, and 4 × 4 positive
  spots of intensity +0.04 or +0.12 at row 8, column 4 (quiet region) or column
  16 (noisy region). Clamp pixels to [0,1]. No test-dependent threshold tuning.

There are 96 unique held-out base images, not 576 independent images. Applying
six paired conditions produces 576 inspected inputs; evaluating both variants
produces 1,152 score/overlap observations. Within-run conditions are correlated.

## Measured results

Mean over the three runs; rates and IoUs are arithmetic means, not confidence
intervals. The committed JSON also records run-wise values and sample standard
deviations of detection rates. Localization uses the fixed image-level threshold.

| Condition | Raw detection rate | Standardized detection rate | Raw mean IoU | Standardized mean IoU |
|---|---:|---:|---:|---:|
| Normal (false alarms) | 8.33% | 9.38% | n/a | n/a |
| Brightness +0.08, no defect (false alarms) | 100% | 100% | n/a | n/a |
| Weak +0.04, quiet region | 8.33% | 100% | 0.0000 | 0.5137 |
| Weak +0.04, noisy region | 17.71% | 19.79% | 0.0065 | 0.0085 |
| Strong +0.12, quiet region | 80.21% | 100% | 0.1868 | 0.9939 |
| Strong +0.12, noisy region | 100% | 98.96% | 0.3849 | 0.3250 |

Interpretation:

- Spatial standardization helps in the quieter region by avoiding a threshold
  dominated by noisier pixels elsewhere. It does not solve low signal-to-noise
  localization in the noisier region.
- An image detection can be caused by an unrelated noisy pixel. The weak/quiet
  raw detector's nonzero detection rate with zero IoU is an example: image recall
  alone would be misleading. IoU includes all defect images, including misses.
- Standardization is not uniformly better: raw residuals have higher recall
  and mean IoU for strong spots in the noisy region in this protocol.
- Brightness shift is a clear failure case for both variants. The nominal 5%
  calibration setting does not guarantee a 5% held-out false-alarm rate; the
  observed normal false-alarm rates are higher even without brightness shift.
- Three synthetic runs do not establish statistical significance, industrial
  generalization, robustness to arbitrary shifts or competitive performance.

## Evidence and regeneration

```bash
python -W error robustness_study.py
python -W error robustness_study.py --check
python -W error -m unittest discover -s tests -p 'test_*.py' -v
```

`results/robustness.json` is canonical compact JSON. It binds both source files
with SHA-256, includes exact train/calibration/test seed lists, thresholds,
condition parameters, per-image observations and summaries. Observation triples
are `[maximum_score, mask_intersection_count, mask_union_count]` in test-seed
order. This is reproducible content identity, not authenticated provenance.

`--check` reruns fitting, calibration, all inspected images and aggregation and
requires byte-identical output. `--write` deliberately regenerates the committed
artifact. Independent test calculations cover known confusion/IoU cases, strict
ties, invalid evidence, mask footprint, seed separation and sample variance.

The [public interactive demo](https://blank-2340.github.io/anomaly-inspection-lab/)
uses the original frozen model, not these three newly fitted models. Changing its
controls is exploratory inference, not a rerun of this study. No test data was
used to refit the public demo or its calibration threshold.
