# MVP Boundary and Analysis Design

## Pilot Region
- **Region name:** South Saskatchewan / Swift Current pilot
- **Reason:** Matches one of the role locations in the JD and contains mixed grassland-agriculture-wetland dynamics that make prioritization meaningful.
- **Approximate extent (WGS84):**
  - Min longitude: `-109.5`
  - Max longitude: `-105.0`
  - Min latitude: `49.0`
  - Max latitude: `51.0`

## Coordinate Reference System
- **Working CRS:** `EPSG:3348` (Statistics Canada Lambert)
- **Display CRS:** `EPSG:4326` for web mapping output.

## Analysis Unit
- **Primary unit:** `10 km x 10 km` square grid cells over pilot extent.
- **Rationale:** Coarse enough for rapid MVP, interpretable for policy reporting, and fast to compute on a laptop.

## MVP Inputs
- Land cover quality proxy (`forest_cover_pct`)
- Wetland density proxy (`wetland_pct`)
- Disturbance proxy (`disturbance_index`) from roads/settlement pressure
- Climate resilience proxy (`climate_resilience`)
- Optional biodiversity proxy (`species_richness_proxy`)

## Priority Model (MVP)
- Habitat score is normalized to `[0, 1]` using weighted linear combination:
  - `0.35 * biodiversity`
  - `0.25 * forest_cover`
  - `0.20 * wetland_density`
  - `0.20 * low_disturbance`
- Priority classes:
  - `High`: top 20%
  - `Medium`: middle 50%
  - `Low`: bottom 30%

## Outputs
- `outputs/priority_map.png`
- `outputs/priority_map.html`
- `outputs/priority_summary.csv`
- `outputs/top_candidate_sites.geojson`
