"""Frozen paired synthetic stress study. No threshold selection on test data."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import statistics

from anomaly_lab import SpatialNormal, calibrate, max_score, specimen

ROOT = Path(__file__).resolve().parent
ARTIFACT = ROOT / "results/robustness.json"
OFFSETS = (100000, 200000, 300000)
CONDITIONS = (
    ("normal", 0.0, 0.0, 4),
    ("brightness_shift", 0.0, .08, 4),
    ("weak_quiet", .04, 0.0, 4),
    ("weak_noisy", .04, 0.0, 16),
    ("strong_quiet", .12, 0.0, 4),
    ("strong_noisy", .12, 0.0, 16),
)


def perturb(base, strength, brightness, x):
    """Apply a 4x4 spot at row 8, preserving all other pixels except global shift."""
    if not all(math.isfinite(v) for v in (strength, brightness)):
        raise ValueError("finite perturbations required")
    if abs(strength) > .5 or abs(brightness) > .15 or x not in (4, 16):
        raise ValueError("perturbation outside frozen study bounds")
    mask = [[bool(strength and 8 <= y < 12 and x <= i < x+4)
             for i in range(24)] for y in range(24)]
    image = [[min(1.0, max(0.0, v+brightness+(strength if mask[y][i] else 0)))
              for i, v in enumerate(row)] for y, row in enumerate(base)]
    return image, mask


def observation(scores, truth, threshold):
    """Raw evidence row: maximum score, mask intersection and union counts."""
    predicted = [s > threshold for row in scores for s in row]
    target = [bool(v) for row in truth for v in row]
    return [max_score(scores),
            sum(a and b for a, b in zip(predicted, target)),
            sum(a or b for a, b in zip(predicted, target))]


def summarize(rows, threshold, has_defect):
    if not rows or not math.isfinite(threshold) or threshold < 0:
        raise ValueError("nonempty evidence and valid threshold required")
    for score, intersection, union in rows:
        if not math.isfinite(score) or score < 0:
            raise ValueError("invalid score")
        if (type(intersection) is not int or type(union) is not int or
                not 0 <= intersection <= union <= 576):
            raise ValueError("invalid mask counts")
        if has_defect and union == 0:
            raise ValueError("nonempty true defect has nonempty union")
    accepted = sum(score > threshold for score, _, _ in rows)
    return {"samples": len(rows),
            "tp": accepted if has_defect else 0,
            "fn": len(rows)-accepted if has_defect else 0,
            "fp": accepted if not has_defect else 0,
            "tn": len(rows)-accepted if not has_defect else 0,
            "detection_rate": accepted/len(rows),
            "defect_mean_iou": statistics.mean(i/u for _, i, u in rows)
            if has_defect else None}


def run_study():
    runs = []
    for offset in OFFSETS:
        train = list(range(offset+1000, offset+1048))
        calibration = list(range(offset+10000, offset+10032))
        test = list(range(offset+30000, offset+30032))
        model = SpatialNormal.fit([specimen(s)[0] for s in train])
        normals = [specimen(s)[0] for s in calibration]
        thresholds = {"raw_residual": calibrate(model, normals, standardized=False),
                      "standardized": calibrate(model, normals)}
        conditions = []
        for name, strength, brightness, x in CONDITIONS:
            variants = {}
            for variant, threshold in thresholds.items():
                rows = []
                for seed in test:
                    image, mask = perturb(specimen(seed)[0], strength, brightness, x)
                    scores = model.heatmap(image, standardized=variant == "standardized")
                    rows.append(observation(scores, mask, threshold))
                variants[variant] = {"observations": rows,
                                     "summary": summarize(rows, threshold, strength != 0)}
            conditions.append({"name": name, "strength": strength,
                               "brightness": brightness, "x": x, "y": 8,
                               "width": 4, "height": 4, "variants": variants})
        runs.append({"offset": offset, "train_seeds": train,
                     "calibration_seeds": calibration, "test_seeds": test,
                     "thresholds": thresholds, "conditions": conditions})
    aggregate = []
    for index, (name, *_rest) in enumerate(CONDITIONS):
        variants = {}
        for variant in ("raw_residual", "standardized"):
            summaries = [r["conditions"][index]["variants"][variant]["summary"] for r in runs]
            rates = [s["detection_rate"] for s in summaries]
            ious = [s["defect_mean_iou"] for s in summaries]
            variants[variant] = {"detection_rate_mean": statistics.mean(rates),
                                 "detection_rate_sample_stddev": statistics.stdev(rates),
                                 "defect_mean_iou": statistics.mean(ious)
                                 if ious[0] is not None else None}
        aggregate.append({"name": name, "variants": variants})
    return {"schema_version": 1,
            "source_sha256": {name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
                              for name in ("anomaly_lab.py", "robustness_study.py")},
            "protocol": {"alpha": .05, "scale_floor": .01, "image_size": 24,
                         "offsets": list(OFFSETS), "calibration": "normal-only, once per run",
                         "observation_fields": ["maximum_score", "intersection", "union"],
                         "pairing": "same 32 test images reused across conditions and variants",
                         "scope": "aligned original synthetic textures, no real-data claim"},
            "runs": runs, "aggregate": aggregate}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--write", action="store_true", help="regenerate committed evidence")
    group.add_argument("--check", action="store_true", help="independently rerun and compare all bytes")
    args = parser.parse_args()
    report = run_study()
    canonical = json.dumps(report, sort_keys=True, separators=(",", ":"), allow_nan=False)+"\n"
    if args.write:
        ARTIFACT.parent.mkdir(exist_ok=True)
        ARTIFACT.write_text(canonical, encoding="utf-8")
    elif args.check:
        if ARTIFACT.read_text(encoding="utf-8") != canonical:
            raise SystemExit("stress evidence differs from exact source/protocol recomputation")
        print("verified three-run paired robustness evidence")
    else:
        print(json.dumps(report["aggregate"], indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
