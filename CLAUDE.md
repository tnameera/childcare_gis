# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Small GIS project that downloads and visualizes childcare center locations in the Seattle area using geospatial Python libraries.

## Running the scripts

```bash
# Basic plot (no basemap, fixes CRS from Web Mercator → WGS84)
python download_childcare.py

# Enhanced plot with CartoDB basemap via contextily
python plot_childcare.py
```

## Dependencies

- `geopandas` — reading/reprojecting GeoJSON data
- `matplotlib` — rendering plots
- `contextily` — fetching tile-based basemaps
- `pyogrio` — fast GeoJSON engine used via `engine="pyogrio"` in `gpd.read_file`

## Data

`childcare_seattle.geojson` — source data from ArcGIS. Despite the GeoJSON CRS header claiming `CRS84` (WGS84), the actual coordinates are stored in **EPSG:3857 (Web Mercator)** and must be overridden with `set_crs(epsg=3857, allow_override=True)` before reprojecting.

## Known issue

`plot_childcare.py` is missing `import geopandas as gpd` at the top of the file.
