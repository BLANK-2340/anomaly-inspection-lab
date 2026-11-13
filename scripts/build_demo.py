"""Rebuild the frozen, synthetic-only browser bundle; no downloads required."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from anomaly_lab import SpatialNormal, calibrate, specimen


def bundle():
    model = SpatialNormal.fit([specimen(s)[0] for s in range(1000, 1048)])
    normal = [specimen(s)[0] for s in range(10000, 10032)]
    return {"schema_version": 1,
            "provenance": {"source_sha256": hashlib.sha256(
                (ROOT / "anomaly_lab.py").read_bytes()).hexdigest(),
                "train_seeds": list(range(1000, 1048)),
                "calibration_seeds": list(range(10000, 10032)),
                "alpha": .05, "scale_floor": .01,
                "scope": "original aligned synthetic textures only"},
            "model": {"height": model.height, "width": model.width,
                      "means": model.means, "scales": model.scales},
            "thresholds": {"standardized": calibrate(model, normal),
                           "raw_residual": calibrate(model, normal, standardized=False)},
            "samples": [{"seed": s, "image": specimen(s)[0]} for s in range(30000, 30003)]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    raw = json.dumps(bundle(), sort_keys=True, indent=2, allow_nan=False) + "\n"
    destination = ROOT / "docs/model.json"
    if args.check:
        if destination.read_text(encoding="utf-8") != raw:
            raise SystemExit("demo bundle differs from current Python source/protocol")
        print("frozen browser model matches Python source and protocol")
    else:
        destination.write_text(raw, encoding="utf-8")


if __name__ == "__main__":
    main()
