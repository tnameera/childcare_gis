# childcare_gis

GIS analysis of childcare center locations in the Seattle metro area.

## Analyses

1. **Childcare vs Schools** — overlay of licensed childcare centers and schools (OpenStreetMap)
2. **Density Heatmap** — kernel density map showing where childcare is dense vs lacking
3. **Gap Analysis** — where childcare should go, scored against 12 major job centers

## Output

Open `index.html` for the full interactive HTML report with all three maps and a coverage table.

## Running

```bash
# Download data and generate all maps + HTML report
python analyze_and_report.py

# Quick basemap plot
python plot_childcare.py
```

## Dependencies

```
geopandas matplotlib contextily pyogrio scipy requests
```

## Data sources

- Childcare centers: King County / ArcGIS Open Data
- Schools: OpenStreetMap via Overpass API
- Employment centers: manually curated from publicly known Seattle-area job hubs
