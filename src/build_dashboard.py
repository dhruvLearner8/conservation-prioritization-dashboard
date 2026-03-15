from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

import pandas as pd
import yaml


REQUIRED_COLUMNS = [
    "grid_id",
    "lon_min",
    "lat_min",
    "lon_max",
    "lat_max",
    "centroid_lon",
    "centroid_lat",
    "forest_cover",
    "wetland_density",
    "disturbance_index",
    "low_disturbance",
    "biodiversity",
]


def load_config(path: Path) -> Dict:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def choose_feature_file(root: Path, cfg: Dict) -> Path:
    preferred = root / cfg.get("features", {}).get("real_features_file", "data/processed/real_features.csv")
    fallback = root / "data" / "processed" / "analysis_grid_features.csv"
    if preferred.exists():
        return preferred
    if fallback.exists():
        return fallback
    raise FileNotFoundError("No feature table found. Run the pipeline first.")


def load_records(path: Path) -> List[Dict]:
    df = pd.read_csv(path)
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Feature table missing columns: {missing}")

    rounded = df[REQUIRED_COLUMNS].copy()
    for col in rounded.columns:
        if col == "grid_id":
            continue
        rounded[col] = rounded[col].astype(float).round(6)
    return rounded.to_dict(orient="records")


def build_html(records: List[Dict], cfg: Dict, feature_file: Path) -> str:
    w = cfg["model"]["weights"]
    high_q = float(cfg["model"]["high_quantile"])
    low_q = float(cfg["model"]["low_quantile"])
    template = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>Saskatchewan Conservation Decision Dashboard</title>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
  <style>
    body { margin: 0; font-family: Arial, sans-serif; background: #f7f7f8; color: #1e1e1e; }
    .container { display: grid; grid-template-columns: 360px 1fr; height: 100vh; }
    .panel { padding: 14px; overflow-y: auto; border-right: 1px solid #ddd; background: #fff; }
    .panel h2 { margin-top: 0; font-size: 18px; }
    .meta { font-size: 12px; color: #444; margin-bottom: 12px; }
    .control { margin: 10px 0; }
    .control label { display: block; font-size: 13px; margin-bottom: 4px; }
    .control input[type=range] { width: 100%; }
    .weights-row { display: grid; grid-template-columns: 1fr auto; gap: 8px; align-items: center; }
    .btn { border: 1px solid #bbb; padding: 8px 10px; background: #fafafa; cursor: pointer; border-radius: 4px; margin-top: 6px; }
    .btn:hover { background: #f0f0f0; }
    .summary { margin-top: 14px; font-size: 13px; }
    .legend { margin-top: 10px; font-size: 12px; }
    .legend span { display: inline-block; width: 10px; height: 10px; margin-right: 6px; border-radius: 50%; }
    .top-table { margin-top: 12px; max-height: 280px; overflow: auto; border: 1px solid #ddd; }
    .scenario-panel { margin-top: 12px; border: 1px solid #ddd; padding: 8px; border-radius: 4px; background: #fcfcfc; }
    .scenario-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; }
    .scenario-table { margin-top: 8px; max-height: 180px; overflow: auto; border: 1px solid #ddd; background: #fff; }
    .small-note { font-size: 11px; color: #555; margin-top: 6px; }
    table { width: 100%; border-collapse: collapse; font-size: 12px; }
    th, td { border-bottom: 1px solid #eee; padding: 6px; text-align: left; }
    #map { height: 100%; width: 100%; }
    .map-wrap { position: relative; }
    .map-title { position: absolute; z-index: 500; top: 10px; left: 12px; background: rgba(255,255,255,.9); padding: 8px 10px; border-radius: 4px; font-size: 13px; border: 1px solid #ddd; }
  </style>
</head>
<body>
  <div class="container">
    <aside class="panel">
      <h2>Saskatchewan Conservation Decision Dashboard</h2>
      <div class="meta">
        <div><b>Feature source:</b> __FEATURE_FILE__</div>
        <div><b>Cells:</b> <span id="cell-count"></span></div>
      </div>

      <h3 style="font-size:15px;margin-bottom:6px;">Weight Scenarios</h3>
      <div class="control">
        <label>Biodiversity (<span id="biodiversity-val"></span>)</label>
        <div class="weights-row">
          <input id="w-biodiversity" type="range" min="0" max="100" step="1"/>
        </div>
      </div>
      <div class="control">
        <label>Forest Cover (<span id="forest-val"></span>)</label>
        <div class="weights-row">
          <input id="w-forest" type="range" min="0" max="100" step="1"/>
        </div>
      </div>
      <div class="control">
        <label>Wetland Density (<span id="wetland-val"></span>)</label>
        <div class="weights-row">
          <input id="w-wetland" type="range" min="0" max="100" step="1"/>
        </div>
      </div>
      <div class="control">
        <label>Low Disturbance (<span id="disturbance-val"></span>)</label>
        <div class="weights-row">
          <input id="w-disturbance" type="range" min="0" max="100" step="1"/>
        </div>
      </div>
      <button class="btn" id="normalize-btn">Normalize Weights to 1.0</button>
      <button class="btn" id="reset-btn">Reset to Baseline</button>
      <button class="btn" id="export-btn">Export Current Ranking CSV</button>
      <div class="scenario-grid">
        <button class="btn" id="preset-baseline-btn">Apply Baseline</button>
        <button class="btn" id="preset-bio-btn">Apply Biodiversity-first</button>
        <button class="btn" id="preset-lowdist-btn">Apply Low-disturbance</button>
        <button class="btn" id="compare-btn">Refresh Comparison</button>
      </div>

      <div class="summary">
        <div><b>High:</b> <span id="high-count"></span></div>
        <div><b>Medium:</b> <span id="medium-count"></span></div>
        <div><b>Low:</b> <span id="low-count"></span></div>
      </div>
      <div class="legend">
        <div><span style="background:#1b9e77"></span>High priority</div>
        <div><span style="background:#7570b3"></span>Medium priority</div>
        <div><span style="background:#d95f02"></span>Low priority</div>
      </div>

      <div class="scenario-panel">
        <div style="font-size:13px;"><b>Scenario Comparison</b></div>
        <div class="small-note">Overlap is Top-20 overlap with Baseline scenario.</div>
        <div class="scenario-table">
          <table>
            <thead>
              <tr>
                <th>Scenario</th>
                <th>High</th>
                <th>Medium</th>
                <th>Low</th>
                <th>Mean</th>
                <th>Top20Overlap</th>
              </tr>
            </thead>
            <tbody id="scenario-body"></tbody>
          </table>
        </div>
      </div>

      <div class="top-table">
        <table>
          <thead>
            <tr><th>Grid ID</th><th>Score</th><th>Priority</th></tr>
          </thead>
          <tbody id="top-body"></tbody>
        </table>
      </div>
    </aside>
    <section class="map-wrap">
      <div class="map-title">Priority map updates live as weights change</div>
      <div id="map"></div>
    </section>
  </div>

  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <script>
    const data = __DATA__;
    const cfg = __CONFIG__;
    const highQ = cfg.highQuantile;
    const lowQ = cfg.lowQuantile;

    const weightInputs = {
      biodiversity: document.getElementById("w-biodiversity"),
      forest_cover: document.getElementById("w-forest"),
      wetland_density: document.getElementById("w-wetland"),
      low_disturbance: document.getElementById("w-disturbance"),
    };
    const labels = {
      biodiversity: document.getElementById("biodiversity-val"),
      forest_cover: document.getElementById("forest-val"),
      wetland_density: document.getElementById("wetland-val"),
      low_disturbance: document.getElementById("disturbance-val"),
    };
    const colors = { High: "#1b9e77", Medium: "#7570b3", Low: "#d95f02" };
    const presetScenarios = {
      baseline: cfg.weights,
      biodiversityFirst: { biodiversity: 0.50, forest_cover: 0.20, wetland_density: 0.20, low_disturbance: 0.10 },
      lowDisturbance: { biodiversity: 0.20, forest_cover: 0.20, wetland_density: 0.10, low_disturbance: 0.50 }
    };
    document.getElementById("cell-count").textContent = data.length;

    const map = L.map("map");
    map.fitBounds([
      [Math.min(...data.map(d => d.lat_min)), Math.min(...data.map(d => d.lon_min))],
      [Math.max(...data.map(d => d.lat_max)), Math.max(...data.map(d => d.lon_max))]
    ]);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 18,
      attribution: "&copy; OpenStreetMap contributors"
    }).addTo(map);

    const rectangles = [];

    function initializeWeights() {
      weightInputs.biodiversity.value = Math.round(cfg.weights.biodiversity * 100);
      weightInputs.forest_cover.value = Math.round(cfg.weights.forest_cover * 100);
      weightInputs.wetland_density.value = Math.round(cfg.weights.wetland_density * 100);
      weightInputs.low_disturbance.value = Math.round(cfg.weights.low_disturbance * 100);
      updateWeightLabels();
    }

    function getRawWeights() {
      return {
        biodiversity: Number(weightInputs.biodiversity.value) / 100,
        forest_cover: Number(weightInputs.forest_cover.value) / 100,
        wetland_density: Number(weightInputs.wetland_density.value) / 100,
        low_disturbance: Number(weightInputs.low_disturbance.value) / 100
      };
    }

    function normalizeWeights(raw) {
      const sum = Object.values(raw).reduce((a, b) => a + b, 0);
      if (sum === 0) {
        return { biodiversity: 0.25, forest_cover: 0.25, wetland_density: 0.25, low_disturbance: 0.25 };
      }
      return {
        biodiversity: raw.biodiversity / sum,
        forest_cover: raw.forest_cover / sum,
        wetland_density: raw.wetland_density / sum,
        low_disturbance: raw.low_disturbance / sum
      };
    }

    function applyWeightsToSliders(norm) {
      weightInputs.biodiversity.value = Math.round(norm.biodiversity * 100);
      weightInputs.forest_cover.value = Math.round(norm.forest_cover * 100);
      weightInputs.wetland_density.value = Math.round(norm.wetland_density * 100);
      weightInputs.low_disturbance.value = Math.round(norm.low_disturbance * 100);
      updateWeightLabels();
    }

    function updateWeightLabels() {
      const raw = getRawWeights();
      labels.biodiversity.textContent = raw.biodiversity.toFixed(2);
      labels.forest_cover.textContent = raw.forest_cover.toFixed(2);
      labels.wetland_density.textContent = raw.wetland_density.toFixed(2);
      labels.low_disturbance.textContent = raw.low_disturbance.toFixed(2);
    }

    function scoreDataWithWeights(weights) {
      const normWeights = normalizeWeights(weights);
      const scored = data.map((d) => {
        const score = (
          normWeights.biodiversity * d.biodiversity +
          normWeights.forest_cover * d.forest_cover +
          normWeights.wetland_density * d.wetland_density +
          normWeights.low_disturbance * d.low_disturbance
        );
        return { ...d, habitat_score: score };
      });

      const sorted = [...scored].sort((a, b) => a.habitat_score - b.habitat_score);
      const n = sorted.length;
      sorted.forEach((row, idx) => { row.rank_pct = (idx + 1) / n; });
      const rankMap = new Map(sorted.map(r => [r.grid_id, r.rank_pct]));

      scored.forEach((row) => {
        const pct = rankMap.get(row.grid_id);
        row.priority = pct >= highQ ? "High" : (pct <= lowQ ? "Low" : "Medium");
      });

      return scored.sort((a, b) => b.habitat_score - a.habitat_score);
    }

    function scoreData() {
      return scoreDataWithWeights(getRawWeights());
    }

    function topSet(scored, n) {
      return new Set(scored.slice(0, n).map((r) => r.grid_id));
    }

    function summarizeScores(scored) {
      const counts = { High: 0, Medium: 0, Low: 0 };
      let sumScore = 0;
      scored.forEach((r) => {
        counts[r.priority] += 1;
        sumScore += r.habitat_score;
      });
      return {
        high: counts.High,
        medium: counts.Medium,
        low: counts.Low,
        mean: sumScore / scored.length
      };
    }

    function overlapCount(setA, setB) {
      let c = 0;
      setA.forEach((v) => { if (setB.has(v)) c += 1; });
      return c;
    }

    function renderScenarioComparison() {
      const baselineScored = scoreDataWithWeights(presetScenarios.baseline);
      const baselineTop20 = topSet(baselineScored, 20);
      const scenarios = [
        { name: "Baseline", weights: presetScenarios.baseline },
        { name: "Biodiversity-first", weights: presetScenarios.biodiversityFirst },
        { name: "Low-disturbance", weights: presetScenarios.lowDisturbance },
        { name: "Current sliders", weights: getRawWeights() }
      ];

      const body = document.getElementById("scenario-body");
      body.innerHTML = "";
      scenarios.forEach((s) => {
        const scored = scoreDataWithWeights(s.weights);
        const sTop20 = topSet(scored, 20);
        const summary = summarizeScores(scored);
        const tr = document.createElement("tr");
        tr.innerHTML =
          "<td>" + s.name + "</td>" +
          "<td>" + summary.high + "</td>" +
          "<td>" + summary.medium + "</td>" +
          "<td>" + summary.low + "</td>" +
          "<td>" + summary.mean.toFixed(3) + "</td>" +
          "<td>" + overlapCount(baselineTop20, sTop20) + "/20</td>";
        body.appendChild(tr);
      });
    }

    function render() {
      updateWeightLabels();
      const scored = scoreData();
      const counts = { High: 0, Medium: 0, Low: 0 };
      scored.forEach(r => { counts[r.priority] += 1; });
      document.getElementById("high-count").textContent = counts.High;
      document.getElementById("medium-count").textContent = counts.Medium;
      document.getElementById("low-count").textContent = counts.Low;

      if (rectangles.length === 0) {
        data.forEach((row) => {
          const rect = L.rectangle(
            [[row.lat_min, row.lon_min], [row.lat_max, row.lon_max]],
            { color: "#777", weight: 1, fillOpacity: 0.45 }
          ).addTo(map);
          rectangles.push(rect);
        });
      }

      const rowMap = new Map(scored.map(r => [r.grid_id, r]));
      rectangles.forEach((rect, idx) => {
        const source = data[idx];
        const row = rowMap.get(source.grid_id);
        rect.setStyle({ color: colors[row.priority], fillColor: colors[row.priority] });
        rect.bindPopup(
          "<b>" + row.grid_id + "</b><br/>" +
          "Score: " + row.habitat_score.toFixed(3) + "<br/>" +
          "Priority: " + row.priority + "<br/>" +
          "Biodiversity: " + row.biodiversity.toFixed(3) + "<br/>" +
          "Forest: " + row.forest_cover.toFixed(3) + "<br/>" +
          "Wetland: " + row.wetland_density.toFixed(3) + "<br/>" +
          "Low disturbance: " + row.low_disturbance.toFixed(3)
        );
      });

      const topBody = document.getElementById("top-body");
      topBody.innerHTML = "";
      scored.slice(0, 20).forEach((r) => {
        const tr = document.createElement("tr");
        tr.innerHTML = "<td>" + r.grid_id + "</td><td>" + r.habitat_score.toFixed(3) + "</td><td>" + r.priority + "</td>";
        topBody.appendChild(tr);
      });

      window.__latestScored = scored;
      renderScenarioComparison();
    }

    function exportCsv() {
      const scored = window.__latestScored || scoreData();
      const header = [
        "grid_id","habitat_score","priority","biodiversity","forest_cover",
        "wetland_density","low_disturbance","disturbance_index",
        "centroid_lon","centroid_lat"
      ];
      const lines = [header.join(",")];
      scored.forEach((r) => {
        lines.push([
          r.grid_id, r.habitat_score.toFixed(6), r.priority, r.biodiversity.toFixed(6),
          r.forest_cover.toFixed(6), r.wetland_density.toFixed(6), r.low_disturbance.toFixed(6),
          r.disturbance_index.toFixed(6), r.centroid_lon.toFixed(6), r.centroid_lat.toFixed(6)
        ].join(","));
      });
      const blob = new Blob([lines.join("\\n")], { type: "text/csv;charset=utf-8;" });
      const link = document.createElement("a");
      link.href = URL.createObjectURL(blob);
      link.download = "dashboard_current_ranking.csv";
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }

    Object.values(weightInputs).forEach((input) => input.addEventListener("input", render));
    document.getElementById("normalize-btn").addEventListener("click", () => {
      applyWeightsToSliders(normalizeWeights(getRawWeights()));
      render();
    });
    document.getElementById("reset-btn").addEventListener("click", () => {
      initializeWeights();
      render();
    });
    document.getElementById("export-btn").addEventListener("click", exportCsv);
    document.getElementById("preset-baseline-btn").addEventListener("click", () => {
      applyWeightsToSliders(normalizeWeights(presetScenarios.baseline));
      render();
    });
    document.getElementById("preset-bio-btn").addEventListener("click", () => {
      applyWeightsToSliders(normalizeWeights(presetScenarios.biodiversityFirst));
      render();
    });
    document.getElementById("preset-lowdist-btn").addEventListener("click", () => {
      applyWeightsToSliders(normalizeWeights(presetScenarios.lowDisturbance));
      render();
    });
    document.getElementById("compare-btn").addEventListener("click", renderScenarioComparison);

    initializeWeights();
    render();
  </script>
</body>
</html>
"""

    payload = json.dumps(records)
    config_payload = json.dumps(
        {
            "weights": w,
            "highQuantile": high_q,
            "lowQuantile": low_q,
        }
    )
    html = (
        template.replace("__DATA__", payload)
        .replace("__CONFIG__", config_payload)
        .replace("__FEATURE_FILE__", feature_file.as_posix())
    )
    return html


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    cfg = load_config(root / "configs" / "project_config.yaml")
    feature_file = choose_feature_file(root, cfg)
    records = load_records(feature_file)
    html = build_html(records, cfg, feature_file)

    out_path = root / "outputs" / "decision_dashboard.html"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
    print(f"Dashboard generated: {out_path}")
    print(f"Records embedded: {len(records)}")


if __name__ == "__main__":
    main()
