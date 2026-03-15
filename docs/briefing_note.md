# Saskatchewan Habitat Prioritization Briefing Note

## Purpose
Provide a transparent MVP prioritization of candidate conservation areas in a Swift Current pilot region.

## Key Findings
- Total analysis cells: **1150**
- High-priority cells: **231**
- Mean habitat score: **0.472**
- High-priority cells cluster where biodiversity and wetland/forest proxies are high and disturbance is lower.

## Top Candidate Cells
  grid_id  habitat_score priority
CELL_0782       0.789346     High
CELL_0641       0.765770     High
CELL_0666       0.756150     High
CELL_0665       0.736685     High
CELL_0618       0.732346     High
CELL_0595       0.717945     High
CELL_0525       0.700900     High
CELL_0548       0.699273     High
CELL_0571       0.670368     High
CELL_0667       0.661259     High

## Priority Class Statistics
priority  cells  avg_score  min_score  max_score  avg_forest  avg_wetland  avg_disturbance
    High    231   0.539480   0.504510   0.789346    0.702178     0.265409         0.243741
  Medium    574   0.475201   0.449850   0.504384    0.619964     0.168556         0.265887
     Low    345   0.421264   0.194902   0.449836    0.524612     0.131897         0.342019

## Sensitivity Check
Weight perturbation scenarios maintained substantial overlap with the base top-20 set, indicating a relatively stable ranking for MVP decision support.

           scenario  high_cells  medium_cells  low_cells  top20_overlap_with_base  mean_habitat_score
               base         231           574        345                       20            0.471932
biodiversity_plus10         231           574        345                       20            0.446157
     wetland_plus10         231           574        345                       20            0.439037
 disturbance_plus10         231           574        345                       17            0.519843

## Caveats
- This run uses real open geospatial layers and proxy engineering for habitat factors.
- Proxies should be replaced with official Saskatchewan landcover/ecological layers for policy decisions.