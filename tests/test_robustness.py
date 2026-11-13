import copy
import json
import math
import unittest

from robustness_study import (ARTIFACT, CONDITIONS, observation, perturb,
                              run_study, summarize)


class RobustnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = run_study()

    def test_known_confusion_iou_and_strict_threshold_ties(self):
        rows = [[2.0, 2, 4], [1.0, 0, 2]]
        self.assertEqual(summarize(rows, 1, True), {
            "samples": 2, "tp": 1, "fn": 1, "fp": 0, "tn": 0,
            "detection_rate": .5, "defect_mean_iou": .25})
        self.assertEqual(summarize(rows, 1, False)["fp"], 1)
        self.assertIsNone(summarize(rows, 1, False)["defect_mean_iou"])
        self.assertEqual(observation([[2, 1], [0, 3]],
                                     [[True, True], [False, False]], 1), [3, 1, 3])

    def test_invalid_metric_evidence_is_rejected(self):
        for rows in ([], [[math.nan, 0, 0]], [[1, 3, 2]], [[1, 1, 577]],
                     [[1, 1.0, 2]], [[1, 0, 0]]):
            with self.assertRaises(ValueError):
                summarize(rows, 1, True)

    def test_perturbation_known_region_and_no_mutation(self):
        base = [[.5]*24 for _ in range(24)]
        before = copy.deepcopy(base)
        image, mask = perturb(base, .04, 0, 4)
        self.assertEqual(sum(map(sum, mask)), 16)
        self.assertEqual(image[8][4], .54)
        self.assertEqual(image[0][0], .5)
        self.assertEqual(base, before)
        shifted, mask = perturb(base, 0, .08, 4)
        self.assertFalse(any(map(any, mask)))
        self.assertEqual(shifted[0][0], .58)
        for strength, brightness, x in ((math.nan, 0, 4), (.6, 0, 4), (0, .2, 4), (0, 0, 5)):
            with self.assertRaises(ValueError):
                perturb(base, strength, brightness, x)

    def test_all_seed_sets_disjoint_and_protocol_frozen(self):
        seen = set()
        for run in self.report["runs"]:
            for name, count in (("train_seeds", 48), ("calibration_seeds", 32), ("test_seeds", 32)):
                seeds = run[name]
                self.assertEqual(len(seeds), count)
                self.assertEqual(len(set(seeds)), count)
                self.assertFalse(seen.intersection(seeds))
                seen.update(seeds)
            self.assertEqual([c["name"] for c in run["conditions"]], [c[0] for c in CONDITIONS])
            for condition in run["conditions"]:
                for variant, value in condition["variants"].items():
                    rows, summary = value["observations"], value["summary"]
                    self.assertEqual(len(rows), 32)
                    # Independent count and overlap calculations, not summarize().
                    detections = len([r for r in rows if r[0] > run["thresholds"][variant]])
                    positive = condition["strength"] != 0
                    self.assertEqual(summary["tp"]+summary["fp"], detections)
                    self.assertEqual(summary["tp"]+summary["tn"]+summary["fp"]+summary["fn"], 32)
                    if positive:
                        self.assertAlmostEqual(summary["defect_mean_iou"],
                                               sum(r[1]/r[2] for r in rows)/32)
                    else:
                        self.assertIsNone(summary["defect_mean_iou"])

    def test_committed_artifact_and_aggregate_statistics(self):
        canonical = json.dumps(self.report, sort_keys=True, separators=(",", ":"), allow_nan=False)+"\n"
        self.assertEqual(ARTIFACT.read_text(encoding="utf-8"), canonical)
        for i, group in enumerate(self.report["aggregate"]):
            for variant, aggregate in group["variants"].items():
                rates = [r["conditions"][i]["variants"][variant]["summary"]["detection_rate"]
                         for r in self.report["runs"]]
                mean = sum(rates)/3
                variance = sum((r-mean)**2 for r in rates)/2
                self.assertAlmostEqual(aggregate["detection_rate_mean"], mean)
                self.assertAlmostEqual(aggregate["detection_rate_sample_stddev"], math.sqrt(variance))


if __name__ == "__main__":
    unittest.main()
