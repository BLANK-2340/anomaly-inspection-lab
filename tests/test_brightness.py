import copy
import json
import math
import unittest
from unittest.mock import patch

from anomaly_lab import SpatialNormal, specimen
import brightness_study as study


def independent_map(model, image, centered):
    # Independent scalar implementation, deliberately not calling study.score.
    residuals = [image[y][x]-model.means[y*model.width+x]
                 for y in range(model.height) for x in range(model.width)]
    offset = math.fsum(residuals)/len(residuals) if centered else 0.0
    return [abs(residuals[i]-offset)/model.scales[i] for i in range(len(residuals))], offset


class BrightnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = study.run_study()

    def test_analytic_offset_area_attenuation_and_no_mutation(self):
        # Four equal pixels with an exactly representable one-pixel defect:
        # offset=d/4, inside residual=3d/4, outside residual=-d/4.
        model = SpatialNormal.fit([[[.25]*4], [[.25]*4]], floor=.125)
        image = [[.375, .25, .25, .25]]
        before = copy.deepcopy(image)
        scores, offset = study.score(model, image, "mean_compensated")
        self.assertEqual(offset, .03125)
        self.assertEqual(scores, [[.75, .25, .25, .25]])
        self.assertEqual(image, before)
        for variant in study.VARIANTS:
            actual, estimate = study.score(model, image, variant)
            expected, expected_offset = independent_map(model, image, variant == "mean_compensated")
            self.assertEqual(actual[0], expected)
            self.assertEqual(estimate, expected_offset)
        self.assertEqual(study.score(model, image, "standardized")[0], model.heatmap(image))
        uniform, estimate = study.score(model, [[.375]*4], "mean_compensated")
        self.assertEqual((uniform, estimate), ([[0.0]*4], .125))

    def test_shift_invariance_and_uniform_defect_ambiguity(self):
        model = SpatialNormal.fit([specimen(s)[0] for s in range(1000, 1048)])
        base, _ = specimen(430000)
        shifted, no_defect = study.inject(base, 0, .08, None)
        full_defect, all_defect = study.inject(base, .08, 0, (0, 0, 24, 24))
        self.assertEqual(shifted, full_defect)  # Same pixels, incompatible labels.
        self.assertEqual(sum(map(sum, no_defect)), 0)
        self.assertEqual(sum(map(sum, all_defect)), 576)
        normal_map, normal_offset = study.score(model, base, "mean_compensated")
        for delta in (-.08, .08):
            image, _ = study.inject(base, 0, delta, None)
            result, offset = study.score(model, image, "mean_compensated")
            self.assertAlmostEqual(offset-normal_offset, delta, places=14)
            for ra, rb in zip(result, normal_map):
                for a, b in zip(ra, rb):
                    self.assertAlmostEqual(a, b, places=12)

    def test_injection_bounds_exact_regions_and_invalid_inputs(self):
        base = [[.5]*24 for _ in range(24)]
        before = copy.deepcopy(base)
        image, mask = study.inject(base, .08, -.08, (4, 8, 4, 4))
        self.assertEqual(sum(map(sum, mask)), 16)
        self.assertAlmostEqual(image[8][4], .5)
        self.assertAlmostEqual(image[0][0], .42)
        self.assertEqual(base, before)
        for strength, brightness, box in ((.1, 0, None), (0, 0, (0, 0, 1, 1)),
                (.08, 0, (True, 0, 1, 1)), (.08, 0, (23, 23, 2, 1)),
                (.08, 0, (0, 0, 0, 1)), (.08, 0, [0, 0, 1, 1]),
                (math.nan, 0, None), (0, math.inf, None), (0, True, None), (0, .17, None)):
            with self.assertRaises(ValueError):
                study.inject(base, strength, brightness, box)
        with self.assertRaises(ValueError):
            study.inject([[.95]*24 for _ in range(24)], 0, .08, None)
        with self.assertRaises(ValueError):
            study.inject([[.5]], 0, 0, None)
        model = SpatialNormal.fit([[[.25]], [[.25]]])
        for image, variant in (([[.3]], "unknown"), ([[.3, .3]], "standardized"),
                               ([[math.nan]], "mean_compensated")):
            with self.assertRaises(ValueError):
                study.score(model, image, variant)
        for train, calibration in (([1, 2], [2]), ([1, 2], [])):
            with self.assertRaises(ValueError):
                study.fit_calibrate(train, calibration)

    def test_known_pixel_metrics_and_strict_threshold_ties(self):
        mask = [[True, True], [False, False]]
        row = study.observe([[2, 1], [0, 3]], mask, 1, .125)
        self.assertEqual(row, [3, .125, 1, 1, 1])
        summary = study.summarize([row, [1, -.125, 0, 0, 2]], 1, True)
        self.assertEqual(summary["detected_images"], 1)
        self.assertEqual(summary["detection_rate"], .5)
        self.assertEqual(summary["defect_mean_iou"], 1/6)
        self.assertEqual(summary["mean_estimated_offset"], 0)
        self.assertIsNone(study.summarize([row], 1, False)["defect_mean_iou"])
        for scores, truth, threshold, offset in (([], [], 1, 0), ([[1]], [], 1, 0),
                ([[1, 2]], [[True]], 1, 0), ([[1]], [[1]], 1, 0),
                ([[math.nan]], [[True]], 1, 0), ([[-1]], [[True]], 1, 0),
                ([[1]], [[True]], math.inf, 0), ([[1]], [[True]], 1, math.nan)):
            with self.assertRaises(ValueError):
                study.observe(scores, truth, threshold, offset)

    def test_disjoint_identities_and_normal_only_calibration(self):
        seen = set()
        # Earlier fixed stress study used offsets 100000, 200000, 300000.
        for offset in (100000, 200000, 300000):
            for start, count in ((1000, 48), (10000, 32), (30000, 32)):
                seen.update(range(offset+start, offset+start+count))
        self.assertEqual(study.OFFSETS, (400000, 500000, 600000))
        self.assertEqual(len(study.CONDITIONS), 9)
        self.assertEqual(len(self.report["runs"]), 3)
        for run in self.report["runs"]:
            for name, count in (("train_seeds", 48), ("calibration_seeds", 32), ("test_seeds", 32)):
                identities = run[name]
                self.assertEqual(len(identities), count)
                self.assertEqual(len(set(identities)), count)
                self.assertFalse(set(identities) & seen)
                seen.update(identities)
            model = SpatialNormal.fit([specimen(s)[0] for s in run["train_seeds"]])
            for variant in study.VARIANTS:
                # Independent nearest-rank calculation: rank31 of32, index30.
                maxima = [max(independent_map(model, specimen(s)[0], variant == "mean_compensated")[0])
                          for s in run["calibration_seeds"]]
                self.assertEqual(run["thresholds"][variant], sorted(maxima)[30])
        held_out = {s for r in self.report["runs"] for s in r["test_seeds"]}
        generator = study.specimen

        def poison_test_pixels(seed):
            return ([[.3]*24 for _ in range(24)], None) if seed in held_out else generator(seed)

        with patch.object(study, "specimen", side_effect=poison_test_pixels):
            poisoned = study.run_study()
        for before, after in zip(self.report["runs"], poisoned["runs"]):
            self.assertEqual(before["thresholds"], after["thresholds"])
            self.assertNotEqual(before["conditions"][0]["variants"], after["conditions"][0]["variants"])

    def test_every_evidence_row_recomputed_independently(self):
        for run in self.report["runs"]:
            model = SpatialNormal.fit([specimen(s)[0] for s in run["train_seeds"]])
            for condition, expected in zip(run["conditions"], study.CONDITIONS):
                name, strength, brightness, box = expected
                self.assertEqual((condition["name"], condition["strength"], condition["brightness"],
                                  condition["box"]), expected)
                for variant in study.VARIANTS:
                    data = condition["variants"][variant]
                    threshold = run["thresholds"][variant]
                    self.assertEqual(len(data["observations"]), 32)
                    detections, ious = 0, []
                    for seed, actual in zip(run["test_seeds"], data["observations"]):
                        base, _ = specimen(seed)
                        # Do not use inject, observe or summarize in this reconstruction.
                        truth = [bool(box is not None and box[0] <= x < box[0]+box[2] and
                                      box[1] <= y < box[1]+box[3])
                                 for y in range(24) for x in range(24)]
                        image = [[base[y][x]+brightness+strength*truth[y*24+x]
                                  for x in range(24)] for y in range(24)]
                        values, offset = independent_map(model, image, variant == "mean_compensated")
                        predicted = {i for i, s in enumerate(values) if s > threshold}
                        target = {i for i, t in enumerate(truth) if t}
                        tp, fp, fn = len(predicted & target), len(predicted-target), len(target-predicted)
                        self.assertEqual(actual, [max(values), offset, tp, fp, fn])
                        detections += bool(predicted)
                        if target:
                            ious.append(len(predicted & target)/len(predicted | target))
                    self.assertEqual(data["summary"]["detected_images"], detections)
                    self.assertEqual(data["summary"]["detection_rate"], detections/32)
                    if ious:
                        self.assertAlmostEqual(data["summary"]["defect_mean_iou"], sum(ious)/32)
                    else:
                        self.assertIsNone(data["summary"]["defect_mean_iou"])

    def test_exact_artifact_independent_aggregation_and_paired_equivalence(self):
        canonical = json.dumps(self.report, sort_keys=True, separators=(",", ":"), allow_nan=False)+"\n"
        self.assertEqual(study.ARTIFACT.read_text(encoding="utf-8"), canonical)
        for i, aggregate in enumerate(self.report["aggregate"]):
            self.assertEqual(aggregate["name"], study.CONDITIONS[i][0])
            for variant, data in aggregate["variants"].items():
                summaries = [r["conditions"][i]["variants"][variant]["summary"] for r in self.report["runs"]]
                rates = [s["detection_rate"] for s in summaries]
                mean = sum(rates)/3
                self.assertEqual(data["samples"], 96)
                self.assertEqual(data["detected_images"], sum(s["detected_images"] for s in summaries))
                self.assertAlmostEqual(data["detection_rate_mean"], mean)
                self.assertAlmostEqual(data["detection_rate_sample_stddev"],
                                       math.sqrt(sum((v-mean)**2 for v in rates)/2))
                if i >= 3:
                    self.assertAlmostEqual(data["defect_mean_iou"],
                                           sum(s["defect_mean_iou"] for s in summaries)/3)
        for run in self.report["runs"]:
            up, full = run["conditions"][1], run["conditions"][8]
            for variant in study.VARIANTS:
                for a, b in zip(up["variants"][variant]["observations"], full["variants"][variant]["observations"]):
                    self.assertEqual(a[:2], b[:2])  # Identical inputs => identical scores/offsets.
            centered = [r["variants"]["mean_compensated"]["observations"] for r in run["conditions"]]
            for left, right in ((0, 1), (0, 2), (3, 4), (6, 7)):
                for a, b in zip(centered[left], centered[right]):
                    self.assertAlmostEqual(a[0], b[0], places=12)
                    self.assertEqual(a[2:], b[2:])


if __name__ == "__main__":
    unittest.main()
