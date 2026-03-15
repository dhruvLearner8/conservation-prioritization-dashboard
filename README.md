# Saskatchewan Habitat Prioritization Project

## What this project is (in simple terms)

This project is a **practice version of what a Habitat Analyst might do** for conservation planning in Saskatchewan.

It takes map-based data, scores each area for conservation value, and shows:
- which areas are **high priority** for protection,
- which are **medium priority**,
- which are **low priority**.

You can also open an interactive dashboard and test different policy scenarios by changing weights (for example, biodiversity-first vs low-disturbance).

---

## Main goal

The goal is to build a transparent, repeatable workflow that can answer:

**"If we had to prioritize land for conservation, which places should we consider first, and why?"**

This matches the type of work in the Habitat Analyst job description:
- spatial analysis,
- ecological-style suitability scoring,
- prioritization maps,
- decision support outputs for technical and non-technical audiences.

---

## How the project works (end-to-end)

1. Define a pilot region (Swift Current area) and split it into grid cells.
2. Collect open geospatial layers.
3. Create per-cell feature values (wetland signal, disturbance signal, biodiversity proxy, etc.).
4. Compute a habitat score using weighted factors.
5. Convert scores into `High / Medium / Low` classes.
6. Export maps, tables, and briefing outputs.
7. Provide an interactive dashboard for scenario testing.

---

## Where the data comes from

### Data used right now (operational in this repo)

This project currently uses **open Natural Earth datasets** as transparent proxy layers:

- Lakes: `https://naturalearth.s3.amazonaws.com/10m_physical/ne_10m_lakes.zip`
- Roads: `https://naturalearth.s3.amazonaws.com/10m_cultural/ne_10m_roads.zip`
- Populated Places: `https://naturalearth.s3.amazonaws.com/10m_cultural/ne_10m_populated_places.zip`
- Urban Areas: `https://naturalearth.s3.amazonaws.com/10m_cultural/ne_10m_urban_areas.zip`
- Parks and Protected Lands: `https://naturalearth.s3.amazonaws.com/10m_cultural/ne_10m_parks_and_protected_lands.zip`

Why these were used:
- They are open and easy to access.
- They let the full workflow run on any machine.
- They are good for learning and portfolio demonstration.

### Data planned for policy-grade upgrade

The project also documents official-relevant sources for future replacement (see `docs/data_catalog.md`), including:
- Saskatchewan digital landcover,
- Ramsar wetlands,
- provincial/federal protected and conserved areas context,
- Saskatchewan GeoHub style layers,
- climate and species-risk sources.

---

## What each feature means

For each grid cell, the pipeline creates values in the range `0-1`:

- `biodiversity` (proxy): higher when wetland/protected signals are stronger.
- `forest_cover` (proxy): naturalness and low-disturbance influenced signal.
- `wetland_density` (proxy): lake area share + proximity to lakes.
- `low_disturbance`: inverse of disturbance pressure.
- `disturbance_index`: roads, populated places, and proximity pressure.

These are proxies, not official ecological field measurements.

---

## Scoring model

The default weighted score is:

- biodiversity: `0.35`
- forest cover: `0.25`
- wetland density: `0.20`
- low disturbance: `0.20`

Then cells are ranked by score and classified by quantiles:
- `High`: top 20%
- `Medium`: middle 50%
- `Low`: bottom 30%

All weights and thresholds are configurable in `configs/project_config.yaml`.

---

## Interactive dashboard (what you can do)

Dashboard file: `outputs/decision_dashboard.html`

In the dashboard you can:
- move sliders to change weights live,
- apply presets (`Baseline`, `Biodiversity-first`, `Low-disturbance`),
- view top candidate cells and map updates instantly,
- compare scenarios in a table,
- see Top-20 overlap with baseline,
- export current ranking CSV.

---

## Folder guide

- `src/run_pipeline.py` - main scoring and output pipeline.
- `src/build_real_features.py` - downloads and processes open source layers into `real_features.csv`.
- `src/build_dashboard.py` - generates dashboard HTML.
- `configs/project_config.yaml` - region, CRS, model weights, thresholds.
- `data/raw/` - downloaded raw files + manifest.
- `data/processed/` - feature and score tables.
- `outputs/` - maps, dashboard, summaries, GeoJSON.
- `docs/` - methods, workflow, validation, and dashboard guide.

---

## How to run (step-by-step)

From project root:

1. Install dependencies:
   - `python -m pip install -r requirements.txt`
2. Build real feature table:
   - `python src/build_real_features.py`
3. Run prioritization pipeline:
   - `python src/run_pipeline.py`
4. Build dashboard:
   - `python src/build_dashboard.py`
5. Open dashboard:
   - `outputs/decision_dashboard.html`

---

## Outputs you get

- `outputs/decision_dashboard.html` - interactive scenario tool.
- `outputs/priority_map.png` - static map snapshot.
- `outputs/priority_map.html` - interactive map output.
- `outputs/priority_summary.csv` - class summary stats.
- `outputs/top_candidate_sites.geojson` - top candidate polygons.
- `outputs/sensitivity_results.csv` - weight perturbation checks.
- `docs/briefing_note.md` - plain-language briefing output.

---

## Important limitations

- This is a **learning and portfolio implementation**.
- Current ecological inputs are **proxy-based**, not full official program datasets.
- Before real policy use, replace proxies with official Saskatchewan layers and run expert review.

---

## Why this is useful for your career

This project shows that you can:
- build geospatial pipelines,
- translate ecology/policy goals into a transparent model,
- communicate results to decision-makers,
- create interactive decision support tools.

That is exactly the direction of the Habitat Analyst role.
