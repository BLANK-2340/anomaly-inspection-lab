"""Global-mean residual compensation: a fixed CPU brightness/defect trade-off.

Original implementation, SPDX-License-Identifier: MIT. No external data/code.
This research extension does not change the frozen browser model or demo.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import statistics

from anomaly_lab import SpatialNormal, max_score, specimen, validate

ROOT = Path(__file__).resolve().parent
ARTIFACT = ROOT / "results/brightness.json"
OFFSETS = (400000, 500000, 600000)
VARIANTS = ("standardized", "mean_compensated")
# Freeze geometry/strength before evaluating. Boxes are (x, y, width, height).
CONDITIONS = (
    ("normal", 0.0, 0.0, None),
    ("brightness_up", 0.0, .08, None),
    ("brightness_down", 0.0, -.08, None),
    ("spot_quiet", .08, 0.0, (4, 8, 4, 4)),
    ("spot_quiet_shift", .08, .08, (4, 8, 4, 4)),
    ("spot_noisy", .08, 0.0, (16, 8, 4, 4)),
    ("broad", .08, 0.0, (0, 0, 18, 24)),
    ("broad_shift", .08, .08, (0, 0, 18, 24)),
    ("uniform_defect", .08, 0.0, (0, 0, 24, 24)),
)


def score(model, image, variant):
    """Subtract unweighted mean residual BEFORE dividing by spatial scales.

    No test labels, mask, brightness or defect size enter this estimator.
    Model means/scales stay fixed. Centered residuals are not clipped images.
    """
    if variant not in VARIANTS:
        raise ValueError("unknown scoring variant")
    if validate(image) != (model.height, model.width):
        raise ValueError("inference shape differs from training")
    residuals = [x - mu for x, mu in zip((v for r in image for v in r), model.means)]
    offset = statistics.fmean(residuals) if variant == "mean_compensated" else 0.0
    values = [abs(r-offset)/s for r, s in zip(residuals, model.scales)]
    return [values[y*model.width:(y+1)*model.width] for y in range(model.height)], offset


def fit_calibrate(train_seeds, calibration_seeds):
    """Normal-only fit and separate per-variant 95% nearest-rank calibration."""
    if set(train_seeds) & set(calibration_seeds):
        raise ValueError("fit and calibration identities must be disjoint")
    if not calibration_seeds:
        raise ValueError("normal calibration cannot be empty")
    model = SpatialNormal.fit([specimen(s)[0] for s in train_seeds])
    normals = [specimen(s)[0] for s in calibration_seeds]
    thresholds = {}
    for variant in VARIANTS:
        maxima = sorted(max_score(score(model, image, variant)[0]) for image in normals)
        thresholds[variant] = maxima[math.ceil(.95*len(maxima))-1]
    return model, thresholds


def inject(base, strength, brightness, box):
    """Add controlled signals, rejecting saturation rather than clipping it away."""
    if validate(base) != (24, 24):
        raise ValueError("study images must be 24 by 24")
    if any(isinstance(v, bool) or not isinstance(v, (int, float)) or
           not math.isfinite(v) or abs(v) > .16 for v in (strength, brightness)):
        raise ValueError("bounded finite perturbations required")
    if box is None:
        if strength != 0:
            raise ValueError("nonzero defect needs a box")
    elif (not isinstance(box, tuple) or len(box) != 4 or
          any(type(v) is not int for v in box) or
          not (0 <= box[0] < 24 and 0 <= box[1] < 24 and
               1 <= box[2] <= 24-box[0] and 1 <= box[3] <= 24-box[1]) or strength == 0):
        raise ValueError("nonempty bounded integer box and nonzero strength required")
    mask = [[bool(box is not None and box[0] <= x < box[0]+box[2] and
                  box[1] <= y < box[1]+box[3]) for x in range(24)] for y in range(24)]
    image = [[v+brightness+(strength if mask[y][x] else 0.0)
              for x, v in enumerate(row)] for y, row in enumerate(base)]
    validate(image)  # Guarantees no clipping or range escape in this protocol.
    return image, mask


def observe(heatmap, mask, threshold, offset):
    """Evidence columns: max score, estimated offset, pixel TP, FP and FN."""
    if (not heatmap or not heatmap[0] or len(heatmap) != len(mask) or
            any(len(row) != len(heatmap[0]) for row in heatmap) or
            any(len(row) != len(heatmap[0]) for row in mask) or
            any(type(v) is not bool for row in mask for v in row) or
            not math.isfinite(threshold) or threshold < 0 or not math.isfinite(offset) or
            any(not math.isfinite(v) or v < 0 for row in heatmap for v in row)):
        raise ValueError("invalid score/mask evidence")
    pairs = [(s > threshold, t) for rs, rt in zip(heatmap, mask) for s, t in zip(rs, rt)]
    return [max_score(heatmap), offset, sum(p and t for p, t in pairs),
            sum(p and not t for p, t in pairs), sum(not p and t for p, t in pairs)]


def summarize(rows, threshold, has_defect):
    detected = sum(row[0] > threshold for row in rows)
    return {"samples": len(rows), "detected_images": detected,
            "detection_rate": detected/len(rows),
            "defect_mean_iou": statistics.fmean(tp/(tp+fp+fn) for _, _, tp, fp, fn in rows)
            if has_defect else None,
            "mean_estimated_offset": statistics.fmean(row[1] for row in rows)}


def run_study():
    runs = []
    for offset in OFFSETS:
        train = list(range(offset+1000, offset+1048))
        calibration = list(range(offset+10000, offset+10032))
        test = list(range(offset+30000, offset+30032))
        model, thresholds = fit_calibrate(train, calibration)
        conditions = []
        for name, strength, brightness, box in CONDITIONS:
            variants = {}
            for variant in VARIANTS:
                rows = []
                for seed in test:
                    image, mask = inject(specimen(seed)[0], strength, brightness, box)
                    heatmap, estimate = score(model, image, variant)
                    rows.append(observe(heatmap, mask, thresholds[variant], estimate))
                variants[variant] = {"observations": rows,
                                     "summary": summarize(rows, thresholds[variant], box is not None)}
            conditions.append({"name": name, "strength": strength, "brightness": brightness,
                               "box": box, "variants": variants})
        runs.append({"offset": offset, "train_seeds": train, "calibration_seeds": calibration,
                     "test_seeds": test, "thresholds": thresholds, "conditions": conditions})
    aggregate = []
    for i, (name, *_rest) in enumerate(CONDITIONS):
        variants = {}
        for variant in VARIANTS:
            summaries = [r["conditions"][i]["variants"][variant]["summary"] for r in runs]
            rates = [s["detection_rate"] for s in summaries]
            ious = [s["defect_mean_iou"] for s in summaries]
            variants[variant] = {"detected_images": sum(s["detected_images"] for s in summaries),
                                 "samples": sum(s["samples"] for s in summaries),
                                 "detection_rate_mean": statistics.fmean(rates),
                                 "detection_rate_sample_stddev": statistics.stdev(rates),
                                 "defect_mean_iou": statistics.fmean(ious) if ious[0] is not None else None}
        aggregate.append({"name": name, "variants": variants})
    return {"schema_version": 1,
            "source_sha256": {n: hashlib.sha256((ROOT/n).read_bytes()).hexdigest()
                              for n in ("anomaly_lab.py", "brightness_study.py")},
            "protocol": {"alpha": .05, "scale_floor": .01, "image_size": 24,
                         "offsets": list(OFFSETS), "fit_count": 48, "calibration_count": 32,
                         "test_count": 32, "observation_fields": ["maximum_score", "estimated_offset",
                             "pixel_tp", "pixel_fp", "pixel_fn"],
                         "calibration": "normal-only, separately once per variant/run",
                         "pairing": "same 32 held-out bases across all nine conditions and two variants",
                         "scales": "same uncentered normal-fit scales; not refitted after compensation",
                         "saturation": "reject out-of-range perturbations; never clip",
                         "scope": "original aligned synthetic textures; not real-data validation"},
            "runs": runs, "aggregate": aggregate}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    flags = parser.add_mutually_exclusive_group()
    flags.add_argument("--write", action="store_true")
    flags.add_argument("--check", action="store_true")
    args = parser.parse_args()
    report = run_study()
    canonical = json.dumps(report, sort_keys=True, separators=(",", ":"), allow_nan=False)+"\n"
    if args.write:
        ARTIFACT.parent.mkdir(exist_ok=True)
        ARTIFACT.write_text(canonical, encoding="utf-8")
    elif args.check:
        if ARTIFACT.read_text(encoding="utf-8") != canonical:
            raise SystemExit("brightness evidence differs from exact source/protocol recomputation")
        print("verified three-run paired brightness/defect evidence")
    else:
        print(json.dumps(report["aggregate"], indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
