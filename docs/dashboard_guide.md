# Decision Dashboard Guide (Phase 3)

The dashboard provides an interactive, policy-friendly interface for exploring conservation-priority outcomes under different weighting scenarios.

## What It Does
- Displays the pilot-region cell map with `High / Medium / Low` priority classes.
- Lets you tune four model weights in real time:
  - biodiversity
  - forest cover
  - wetland density
  - low disturbance
- Recomputes scores and classes live as sliders move.
- Shows a top-20 candidate table for briefing discussions.
- Exports current ranked results to CSV for scenario documentation.
- Includes a scenario comparison panel:
  - Baseline
  - Biodiversity-first
  - Low-disturbance
  - Current sliders
  with Top-20 overlap against Baseline.

## Build Dashboard
From project root:
- `python src/build_dashboard.py`

This generates:
- `outputs/decision_dashboard.html`

## Open Dashboard
- Double-click `outputs/decision_dashboard.html` in file explorer, or open it in any modern browser.

## Controls
- **Normalize Weights to 1.0**: rescales slider values so they sum to 1.
- **Reset to Baseline**: returns to config baseline weights.
- **Export Current Ranking CSV**: saves current scenario ranking from the browser.
- **Apply Baseline / Biodiversity-first / Low-disturbance**: quick preset loading.
- **Refresh Comparison**: recomputes scenario comparison table and overlap metrics.

## Recommended Use in Briefings
1. Start with baseline settings from `configs/project_config.yaml`.
2. Demonstrate a biodiversity-first scenario.
3. Demonstrate a low-disturbance scenario.
4. Export each scenario CSV and compare top candidate overlap.

## Notes
- Dashboard input is whichever feature table is available:
  - `data/processed/real_features.csv` (preferred), else
  - `data/processed/analysis_grid_features.csv`.
- For production decisions, replace proxy layers with official Saskatchewan ecological datasets.
