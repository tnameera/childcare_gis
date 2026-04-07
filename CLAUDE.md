# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

GIS analysis of childcare center locations in the Seattle metro area using Python. Three analyses are produced and published as a self-contained HTML report on GitHub Pages.

**Live report:** https://tnameera.github.io/childcare_gis/
**GitHub repo:** https://github.com/tnameera/childcare_gis

## Main script

```bash
# Runs all three analyses, generates 3 PNGs + index.html, then copy to docs/
python analyze_and_report.py
cp index.html docs/index.html
```

After running, commit and push to update the live GitHub Pages site.

## The three analyses

| # | File | What it shows |
|---|------|---------------|
| 1 | `map_schools_vs_childcare.png` | Childcare centers (blue) vs schools (red triangles) from OpenStreetMap |
| 2 | `map_heatmap.png` | KDE density heatmap with neighbourhood labels; sparse areas transparent so basemap shows through |
| 3 | `map_childcare_gaps.png` | 2.5 km buffers around 12 job centers colored by childcare coverage (green = good, red = low) |

## Data sources

- `childcare_seattle.geojson` — from ArcGIS. CRS header claims WGS84 but coordinates are actually **EPSG:3857**. Must use `set_crs(epsg=3857, allow_override=True)` before any reprojection.
- Schools — fetched live from OpenStreetMap via Overpass API (265 schools in bounding box 47.48–47.74 lat, -122.45–-122.22 lon)
- Employment centers — 12 manually defined job hubs (Downtown Seattle, Bellevue, Redmond/Microsoft, Renton, etc.)

## Key findings (as of Apr 2026)

- 680 childcare centers in dataset
- **Renton and Burien have 0 childcare centers within 2.5 km of their job hubs** — highest need
- Kirkland has only 3; SoDo/Industrial and Bellevue Tech Corridor are moderate
- Downtown Seattle, South Lake Union, University District are well served (17–25 centers nearby)

## CRS / coordinate system rules

- All plotting is done in **EPSG:3857** (Web Mercator) — same CRS contextily uses natively
- Always set axis limits (`ax.set_xlim / ax.set_ylim`) **before** calling `ctx.add_basemap` so tiles are fetched for the right extent
- Neighbourhood label coordinates are stored as WGS84 and converted to 3857 via `pyproj.Transformer`

## Dependencies

- `geopandas` — reading/reprojecting GeoJSON
- `matplotlib` — rendering plots
- `contextily` — CartoDB Positron basemap tiles
- `pyogrio` — fast GeoJSON engine (`engine="pyogrio"`)
- `scipy` — `gaussian_kde` for density heatmap
- `pyproj` — coordinate transformation for neighbourhood labels
- `requests` — Overpass API calls for school data

## GitHub Pages

HTML report lives in `docs/index.html` (branch: `main`, folder: `/docs`).
All map images are embedded as base64 in the HTML so the report is fully self-contained.

## Legacy scripts

- `download_childcare.py` — basic plot, no basemap, WGS84 output
- `plot_childcare.py` — basemap plot; note: missing `import geopandas as gpd` at top
