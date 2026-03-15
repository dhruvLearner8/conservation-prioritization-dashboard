from __future__ import annotations

import io
import zipfile
from pathlib import Path
from typing import Dict, Tuple

import geopandas as gpd
import numpy as np
import pandas as pd
import requests
import yaml
from shapely.geometry import Polygon


REAL_SOURCES = {
    "lakes": "https://naturalearth.s3.amazonaws.com/10m_physical/ne_10m_lakes.zip",
    "roads": "https://naturalearth.s3.amazonaws.com/10m_cultural/ne_10m_roads.zip",
    "populated_places": "https://naturalearth.s3.amazonaws.com/10m_cultural/ne_10m_populated_places.zip",
    "urban_areas": "https://naturalearth.s3.amazonaws.com/10m_cultural/ne_10m_urban_areas.zip",
    "protected_lands": "https://naturalearth.s3.amazonaws.com/10m_cultural/ne_10m_parks_and_protected_lands.zip",
}


def load_config(config_path: Path) -> Dict:
    with config_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def ensure_dirs(*dirs: Path) -> None:
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)


def bbox_polygon(cfg: Dict) -> Polygon:
    b = cfg["spatial"]["bbox_wgs84"]
    return Polygon(
        [
            (b["min_lon"], b["min_lat"]),
            (b["max_lon"], b["min_lat"]),
            (b["max_lon"], b["max_lat"]),
            (b["min_lon"], b["max_lat"]),
            (b["min_lon"], b["min_lat"]),
        ]
    )


def make_grid(cfg: Dict) -> gpd.GeoDataFrame:
    b = cfg["spatial"]["bbox_wgs84"]
    cell_km = float(cfg["spatial"]["grid_cell_km"])
    deg_step = cell_km / 111.0

    lon_values = np.arange(b["min_lon"], b["max_lon"], deg_step)
    lat_values = np.arange(b["min_lat"], b["max_lat"], deg_step)

    rows = []
    grid_id = 1
    for lon in lon_values:
        for lat in lat_values:
            lon2 = min(lon + deg_step, b["max_lon"])
            lat2 = min(lat + deg_step, b["max_lat"])
            poly = Polygon([(lon, lat), (lon2, lat), (lon2, lat2), (lon, lat2), (lon, lat)])
            rows.append(
                {
                    "grid_id": f"CELL_{grid_id:04d}",
                    "lon_min": lon,
                    "lat_min": lat,
                    "lon_max": lon2,
                    "lat_max": lat2,
                    "centroid_lon": (lon + lon2) / 2.0,
                    "centroid_lat": (lat + lat2) / 2.0,
                    "geometry": poly,
                }
            )
            grid_id += 1

    return gpd.GeoDataFrame(rows, crs="EPSG:4326")


def download_zip(url: str, dest_zip: Path) -> None:
    r = requests.get(url, timeout=120)
    r.raise_for_status()
    dest_zip.write_bytes(r.content)


def extract_zip(src_zip: Path, dest_dir: Path) -> None:
    with zipfile.ZipFile(src_zip, "r") as zf:
        zf.extractall(dest_dir)


def fetch_layer(name: str, url: str, raw_dir: Path) -> Path:
    layer_dir = raw_dir / "natural_earth" / name
    ensure_dirs(layer_dir)
    zip_path = layer_dir / f"{name}.zip"
    download_zip(url, zip_path)
    extract_zip(zip_path, layer_dir)
    shp_files = list(layer_dir.glob("*.shp"))
    if not shp_files:
        raise FileNotFoundError(f"No shapefile found after extracting {name}")
    return shp_files[0]


def clip_to_bbox(gdf: gpd.GeoDataFrame, bbox_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    if gdf.crs is None:
        gdf = gdf.set_crs("EPSG:4326")
    gdf = gdf.to_crs("EPSG:4326")
    clipped = gpd.clip(gdf, bbox_gdf)
    return clipped


def scale_series(s: pd.Series) -> pd.Series:
    min_v, max_v = float(s.min()), float(s.max())
    if max_v - min_v < 1e-9:
        return pd.Series(np.full(len(s), 0.5), index=s.index)
    return (s - min_v) / (max_v - min_v)


def compute_features(
    grid: gpd.GeoDataFrame,
    lakes: gpd.GeoDataFrame,
    roads: gpd.GeoDataFrame,
    places: gpd.GeoDataFrame,
    urban: gpd.GeoDataFrame,
    protected: gpd.GeoDataFrame,
    analysis_crs: str,
) -> pd.DataFrame:
    grid_m = grid.to_crs(analysis_crs).copy()
    grid_wgs84 = grid_m.to_crs("EPSG:4326")
    lakes_m = lakes.to_crs(analysis_crs)
    roads_m = roads.to_crs(analysis_crs)
    places_m = places.to_crs(analysis_crs)
    urban_m = urban.to_crs(analysis_crs)
    protected_m = protected.to_crs(analysis_crs)

    cell_area = grid_m.geometry.area
    centroids_m = grid_m.centroid

    lake_intersection = gpd.overlay(grid_m[["grid_id", "geometry"]], lakes_m[["geometry"]], how="intersection")
    if not lake_intersection.empty:
        lake_intersection["piece_area_m2"] = lake_intersection.geometry.area
        lake_area = lake_intersection.groupby("grid_id")["piece_area_m2"].sum()
    else:
        lake_area = pd.Series(dtype=float)

    urban_intersection = gpd.overlay(grid_m[["grid_id", "geometry"]], urban_m[["geometry"]], how="intersection")
    if not urban_intersection.empty:
        urban_intersection["piece_area_m2"] = urban_intersection.geometry.area
        urban_area = urban_intersection.groupby("grid_id")["piece_area_m2"].sum()
    else:
        urban_area = pd.Series(dtype=float)

    roads_join = gpd.sjoin(roads_m[["geometry"]], grid_m[["grid_id", "geometry"]], how="inner", predicate="intersects")
    if not roads_join.empty:
        roads_join["segment_length_m"] = roads_join.geometry.length
        road_lengths = roads_join.groupby("grid_id")["segment_length_m"].sum()
    else:
        road_lengths = pd.Series(dtype=float)

    place_join = gpd.sjoin(places_m[["geometry"]], grid_m[["grid_id", "geometry"]], how="inner", predicate="within")
    place_counts = place_join.groupby("grid_id").size() if not place_join.empty else pd.Series(dtype=float)

    prot_join = gpd.sjoin(protected_m[["geometry"]], grid_m[["grid_id", "geometry"]], how="inner", predicate="intersects")
    protected_presence = prot_join.groupby("grid_id").size() if not prot_join.empty else pd.Series(dtype=float)

    if roads_m.empty:
        dist_roads = pd.Series(np.full(len(grid_m), 1e6), index=grid_m["grid_id"])
    else:
        roads_union = roads_m.geometry.union_all()
        dist_roads = pd.Series(centroids_m.distance(roads_union).values, index=grid_m["grid_id"])

    if places_m.empty:
        dist_places = pd.Series(np.full(len(grid_m), 1e6), index=grid_m["grid_id"])
    else:
        places_union = places_m.geometry.union_all()
        dist_places = pd.Series(centroids_m.distance(places_union).values, index=grid_m["grid_id"])

    if lakes_m.empty:
        dist_lakes = pd.Series(np.full(len(grid_m), 1e6), index=grid_m["grid_id"])
    else:
        lakes_union = lakes_m.geometry.union_all()
        dist_lakes = pd.Series(centroids_m.distance(lakes_union).values, index=grid_m["grid_id"])

    if protected_m.empty:
        dist_protected = pd.Series(np.full(len(grid_m), 1e6), index=grid_m["grid_id"])
    else:
        protected_union = protected_m.geometry.union_all()
        dist_protected = pd.Series(centroids_m.distance(protected_union).values, index=grid_m["grid_id"])

    centroids_wgs84 = grid_m.centroid.to_crs("EPSG:4326")
    bounds_wgs84 = grid_wgs84.geometry.bounds
    out = pd.DataFrame(
        {
            "grid_id": grid_m["grid_id"],
            "lon_min": bounds_wgs84["minx"].values,
            "lat_min": bounds_wgs84["miny"].values,
            "lon_max": bounds_wgs84["maxx"].values,
            "lat_max": bounds_wgs84["maxy"].values,
            "centroid_lon": centroids_wgs84.x.values,
            "centroid_lat": centroids_wgs84.y.values,
            "cell_area_m2": cell_area.values,
        }
    ).set_index("grid_id")

    out["lake_area_m2"] = lake_area
    out["urban_area_m2"] = urban_area
    out["road_length_m"] = road_lengths
    out["place_count"] = place_counts
    out["protected_hits"] = protected_presence
    out["dist_to_road_m"] = dist_roads
    out["dist_to_place_m"] = dist_places
    out["dist_to_lake_m"] = dist_lakes
    out["dist_to_protected_m"] = dist_protected
    out = out.fillna(0.0)

    wetland_area_share = np.clip(out["lake_area_m2"] / out["cell_area_m2"], 0, 1)
    wetland_proximity = 1 - scale_series(out["dist_to_lake_m"])
    out["wetland_density"] = np.clip(wetland_area_share * 0.7 + wetland_proximity * 0.3, 0, 1)

    road_pressure = 1 - scale_series(out["dist_to_road_m"])
    place_pressure = 1 - scale_series(out["dist_to_place_m"])
    disturbance_raw = scale_series(out["road_length_m"]) * 0.35 + scale_series(out["place_count"]) * 0.25 + road_pressure * 0.25 + place_pressure * 0.15
    out["disturbance_index"] = np.clip(disturbance_raw, 0, 1)
    out["low_disturbance"] = 1 - out["disturbance_index"]

    naturalness = 1 - np.clip(out["urban_area_m2"] / out["cell_area_m2"], 0, 1)
    forest_proxy = naturalness * 0.5 + out["low_disturbance"] * 0.3 + out["wetland_density"] * 0.2
    out["forest_cover"] = np.clip(scale_series(forest_proxy), 0, 1)

    protected_proximity = 1 - scale_series(out["dist_to_protected_m"])
    biodiversity_raw = scale_series(out["wetland_density"]) * 0.4 + scale_series(out["protected_hits"]) * 0.3 + protected_proximity * 0.3
    out["biodiversity"] = np.clip(biodiversity_raw, 0, 1)

    # Use low disturbance and wetlands as a simple climate resilience proxy.
    out["climate_resilience"] = np.clip(scale_series(out["low_disturbance"] * 0.5 + out["wetland_density"] * 0.5), 0, 1)

    cols = [
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
        "climate_resilience",
        "biodiversity",
    ]
    return out[cols].reset_index()


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    cfg = load_config(root / "configs" / "project_config.yaml")
    raw_dir = root / cfg["paths"]["raw_data_dir"]
    proc_dir = root / cfg["paths"]["processed_data_dir"]
    ensure_dirs(raw_dir, proc_dir)

    bbox = gpd.GeoDataFrame({"id": [1]}, geometry=[bbox_polygon(cfg)], crs="EPSG:4326")
    grid = make_grid(cfg)

    paths: Dict[str, Path] = {}
    for name, url in REAL_SOURCES.items():
        print(f"Downloading {name}...")
        paths[name] = fetch_layer(name, url, raw_dir)

    print("Reading and clipping source layers...")
    lakes = clip_to_bbox(gpd.read_file(paths["lakes"]), bbox)
    roads = clip_to_bbox(gpd.read_file(paths["roads"]), bbox)
    places = clip_to_bbox(gpd.read_file(paths["populated_places"]), bbox)
    urban = clip_to_bbox(gpd.read_file(paths["urban_areas"]), bbox)
    protected = clip_to_bbox(gpd.read_file(paths["protected_lands"]), bbox)

    print("Computing cell-level real feature proxies...")
    features = compute_features(
        grid=grid,
        lakes=lakes,
        roads=roads,
        places=places,
        urban=urban,
        protected=protected,
        analysis_crs=cfg["spatial"]["analysis_crs"],
    )

    out_file = proc_dir / "real_features.csv"
    features.to_csv(out_file, index=False)
    print(f"Saved: {out_file}")
    print(f"Rows: {len(features)}")


if __name__ == "__main__":
    main()
