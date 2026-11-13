# Project continuity

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
