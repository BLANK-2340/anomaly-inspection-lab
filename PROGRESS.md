# Project continuity

## November 20, 2026 evening: brightness/defect trade-off

Started from public main `c72a31ba99bc29c83e885dbcb5b43fd5ccd6ac21`,
with no open PRs and no concurrent remote changes. The latest cross-project
continuity records four bounded November projects complete and three public
showcases verified on November 17, meeting the November 20 first-three target.
Those records supersede the older portfolio status below. The fifth new project,
softmax-fusion-lab, has experimental CUDA source but no actual GPU validation.
This runtime still has neither nvcc nor nvidia-smi. GPU compilation, numerical
checks, memcheck/racecheck/synccheck and measurements remain pending; the all-five
November 20–22 aspiration / December 1 deadline is at risk. CPU improvements here
do not complete or replace the fifth project. No older portfolio repos changed.

Added a separate original global-mean residual compensator and a fixed study on
three fresh disjoint seed runs. Each fits 48 normals, separately calibrates both
variants on 32 normals, then evaluates 32 held-out bases reused across nine
conditions. That is 96 unique bases, 864 paired condition inputs and 1728 variant
observations. No test-based threshold or hyperparameter tuning. Preserved the
core source, previous study/evidence, frozen model, browser engine and all demo
files byte-for-byte. Public demo behavior is unchanged, and no new browser or
mobile interaction check is claimed in this session.

Actual study: +/-0.08 shifted-normal false alarms fall from 96/96 to 3/96,
matching the compensated unshifted rate. Shifted quiet-spot IoU improves from
0.05314 to 0.99812, but broad-defect IoU collapses from 0.68166 to 0.00424.
Broad-defect detections fall from 96 to 78/96; noisy-spot detections fall from
47 to 46/96. Identical pixels designated either harmless uniform brightness or
a uniform defect necessarily produce identical predictions; compensation removes
both signals. See BRIGHTNESS.md and source-bound results/brightness.json for
denominators, raw observations, assumptions, exact results and limitations.
No real-data, significance, universal-gain or industrial claim.

Local checks passed before publication: eight warning-strict core Python groups,
five earlier study groups, seven new study groups, four Node groups including
all-pixel Python/JavaScript parity, frozen browser bundle check, and exact full
recomputation of both studies. New independent checks reconstruct every new
observation and per-variant normal quantile, verify analytic area attenuation,
shift invariance, saturation rejection, split separation, test-pixel poisoning
invariance of thresholds, known metrics and aggregate sample standard deviations.
Publication also requires final diff review, byte-repeatability, a clean committed
archive rerun and exact remote tested-tree verification. Report actual remote
publication and CI results after observing them, not as presumed successes here.

Today had one earlier task commit, c0b4ff47 in softmax-fusion-lab. This run may
publish at most one, bringing the collective November 20 target to two if the
publication succeeds. Do not make quota-only or further publications today.

Next: actual compatible existing free CUDA hardware remains the highest remaining
acceptance gate. Compile and run full numerical/device sanitizer checks before
any timing if it becomes available. If still unavailable, keep that blocker and
fifth-project acceptance explicit. A useful independent next improvement is a
tracking sensitivity study with genuinely varied trajectories, since the current
three replay seeds change noise/translation only. Read that repository's current
continuity first, preserve its established reference/replay, and do not invent
trajectory diversity or GPU results. No sixth November repository or older-repo
November writes. The approved end date remains August 31, 2027.

## November 13, 2026 evening: frozen stress evidence

Started from public `main` at `030d8d045402d436c712754e988e34d6fcc8bf04`,
with no open PRs and two earlier task commits today. Added a three-run fixed
study of quiet/noisy low-contrast spots and brightness shift, per-image raw
score/overlap evidence, independent metric tests, source identities, exact
regeneration, measured comparisons and CI checks. Existing core Python source,
browser model, demo engine and historical results remain unchanged.

The public demo at https://blank-2340.github.io/anomaly-inspection-lab/ was
opened and its default inference, remove-defect, brightness-shift, sample,
variant, footprint and edge-position controls verified in the afternoon.
Its CI and Pages deployment passed. Desktop heatmaps were visually inspected.
Mobile browser viewport validation remained pending at that check.

The evening live recheck reproduced default inference and remove-defect output.
With no defect and +0.08 brightness, it returned score 10.566225 above threshold
4.079679 and mask IoU 0.0000, confirming a harmless-change false alarm. The
available browser controls did not expose viewport emulation; mobile validation
is still pending. No mobile result is claimed.

Bounded showcase acceptance: public interactive CPU inference, runnable setup,
core/metric/parity tests, architecture explanation, measured ablation, source and
license record, and explicit failure cases are present and verified. This is an
educational synthetic-data showcase, not a validated industrial inspection tool.
One of the five November projects has reached this bounded scope; the other four
are not yet created. The three-showcase November 20 target remains at risk until
the tracking and active-learning projects are implemented, deployed and checked.

Required before this publication: all eight core tests, five new independent
study test groups, four Node groups, exact study recomputation, frozen browser
asset check, committed-archive rerun, final diff and remote-tree verification.
Record the actual new CI/deployment outcome in the completion report.

Scientific outcome: standardization helps weak/quiet localization but is not
uniformly superior; both variants falsely flag all +0.08 brightness-shifted
normal images. See STUDY.md for exact denominators, paired design and failures.

Next concrete milestone: create the second new public project for visual motion
and multi-object tracking, with generated ground truth, original association,
quantitative checks and a public interactive demo. Do not rebuild this anomaly
baseline or spend a session on documentation-only refreshes. Continue maintaining
its bounded synthetic showcase without implying industrial validation.

## November 13, 2026: browser inference and reproducibility

Started from public `main` at `a517524129348ce4d316a3444f71b99a7bd72db5`,
with no open PRs and one earlier task commit today. Original task-owned source
remains unchanged. Added a frozen-source-bound browser bundle, actual client-side
inference and controllable defect/brightness experiments, Python/JavaScript
pixel-parity tests, setup/method/results documentation, MIT license and CI.

Required checks: eight warning-strict Python tests, asset regeneration check,
four Node test groups (including 30 cross-language inference cases), committed
archive rerun, remote tree verification and actual public demo interaction.

Publication or enabling GitHub Pages is not proof of live deployment. Live URL,
CI result and interaction observations must be reported after verification.
Neither this file nor the browser UI adds a new benchmark measurement.

## Remaining work and deadline

First of five November projects. Three showcases are targeted for November 20;
the other four projects have not been created at this milestone. Next: freeze
low-contrast and brightness-shift evaluation across multiple seeds, test failure
modes, record truthful comparisons, and review full showcase acceptance. Do not
call the three-project deadline met before three public demos have been tested.

The initial single-file module docstring contains historical November 13 morning
status; this file supplies subsequent continuity. Preserve real-data/GPU and
industrial-generalization limitations.
