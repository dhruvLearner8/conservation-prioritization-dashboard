# Real-Data Workflow (Phase 2)

This project now supports a real-data proxy workflow built from open geospatial sources.

## Data Sources Used
- Natural Earth 10m Lakes
- Natural Earth 10m Roads
- Natural Earth 10m Populated Places
- Natural Earth 10m Urban Areas
- Natural Earth 10m Parks and Protected Lands

All are downloaded automatically by `src/build_real_features.py`.

## Pipeline Steps
1. Create analysis grid from configured Saskatchewan pilot bbox.
2. Download and extract Natural Earth source layers into `data/raw/natural_earth/`.
3. Clip layers to pilot bbox.
4. Engineer cell-level proxies:
   - `wetland_density`: lake area share + distance-to-lakes proximity.
   - `disturbance_index`: road length, populated-place count, and proximity pressures.
   - `forest_cover` proxy: naturalness + low disturbance + wetland support.
   - `biodiversity` proxy: wetland signal + protected-land intersection/proximity.
5. Save `data/processed/real_features.csv`.
6. Run prioritization model via `src/run_pipeline.py` (auto-detects real features).

## Run Commands
- Build real features:
  - `python src/build_real_features.py`
- Run prioritization:
  - `python src/run_pipeline.py`

## Feature Mode Options
Configured in `configs/project_config.yaml`:
- `features.mode: auto` -> use real file when present; otherwise synthetic.
- `features.mode: real` -> require real file; fail if missing.
- `features.mode: synthetic` -> always use synthetic generation path.
