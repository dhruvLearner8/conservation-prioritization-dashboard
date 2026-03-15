# Saskatchewan Habitat Prioritization Briefing Note

## Purpose
Provide a transparent MVP prioritization of candidate conservation areas in a Swift Current pilot region.

## Key Findings
- Total analysis cells: **136**
- High-priority cells: **28**
- Mean habitat score: **0.513**
- High-priority cells cluster where biodiversity and wetland/forest proxies are high and disturbance is lower.

## Top Candidate Cells
  grid_id  habitat_score priority
CELL_0080       0.741657     High
CELL_0071       0.704765     High
CELL_0079       0.692612     High
CELL_0063       0.672737     High
CELL_0096       0.672284     High
CELL_0088       0.647647     High
CELL_0072       0.645078     High
CELL_0055       0.632975     High
CELL_0087       0.610584     High
CELL_0064       0.609244     High

## Priority Class Statistics
priority  cells  avg_score  min_score  max_score  avg_forest  avg_wetland  avg_disturbance
    High     28   0.611872   0.560662   0.741657    0.839702     0.268827         0.234464
  Medium     68   0.517132   0.477749   0.560226    0.728446     0.153804         0.261372
     Low     40   0.437798   0.233394   0.476420    0.558604     0.140746         0.410806

## Sensitivity Check
Weight perturbation scenarios maintained substantial overlap with the base top-20 set, indicating a relatively stable ranking for MVP decision support.

           scenario  high_cells  medium_cells  low_cells  top20_overlap_with_base  mean_habitat_score
               base          28            68         40                       20            0.513304
biodiversity_plus10          28            68         40                       17            0.489847
     wetland_plus10          28            68         40                       18            0.472287
 disturbance_plus10          28            68         40                       18            0.551273

## Caveats
- This run uses real open geospatial layers and proxy engineering for habitat factors.
- Proxies should be replaced with official Saskatchewan landcover/ecological layers for policy decisions.