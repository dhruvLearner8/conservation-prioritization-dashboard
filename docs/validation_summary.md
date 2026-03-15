# Sensitivity and Interpretability Notes

## Sensitivity Test Result
- Base scenario compared with three +10% reweighting scenarios.
- Top-20 overlap with base:
  - biodiversity_plus10: 20/20
  - wetland_plus10: 20/20
  - disturbance_plus10: 17/20

## Interpretation
- Core high-priority areas remain mostly stable when weights are perturbed.
- Biodiversity and wetland perturbations preserve the top candidate set in this pilot run.
- Disturbance emphasis shifts a small portion of the top-ranked cells, which is expected for development-conflict scenarios.
- Model behavior is explainable at cell level because score components are explicit and bounded `[0, 1]`.
- Phase 2 real-data workflow now uses open geospatial proxy layers instead of fully synthetic inputs.

## Refinement Decision for MVP
- Keep baseline weights for the MVP release:
  - biodiversity: `0.35`
  - forest_cover: `0.25`
  - wetland_density: `0.20`
  - low_disturbance: `0.20`
- Rationale: stable rankings and balanced ecological narrative for non-technical briefings.

## Recommended Future Refinement
- Introduce scenario-specific weight profiles:
  - biodiversity-first planning,
  - connectivity-first planning,
  - low-conflict (low disturbance) planning.
- Replace proxy layers with Saskatchewan official landcover/wetland/species layers and re-run sensitivity.
- Compare scenario maps with overlap statistics and stakeholder review.
