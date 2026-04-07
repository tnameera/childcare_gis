"""
Childcare GIS Analysis — Seattle Area
Three analyses:
  1. Childcare vs Schools overlay
  2. Childcare density heatmap
  3. Childcare gaps near job centers
Outputs: 3 PNGs + index.html report
"""

import geopandas as gpd
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import contextily as ctx
from scipy.stats import gaussian_kde
from shapely.geometry import Point
import requests
import base64
import os
from datetime import date

# ── helpers ─────────────────────────────────────────────────────────────────

def img_to_b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

# ── 1. Load childcare data ───────────────────────────────────────────────────

print("Loading childcare data…")
childcare = gpd.read_file("childcare_seattle.geojson", engine="pyogrio")
childcare = childcare.set_crs(epsg=3857, allow_override=True)
childcare_4326 = childcare.to_crs(epsg=4326)
print(f"  {len(childcare)} childcare centers loaded")

# ── 2. Fetch schools via Overpass API ────────────────────────────────────────

print("Fetching schools from OpenStreetMap…")
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
query = """
[out:json][timeout:30];
(
  node["amenity"="school"](47.48,-122.45,47.74,-122.22);
  way["amenity"="school"](47.48,-122.45,47.74,-122.22);
);
out center;
"""
try:
    resp = requests.post(OVERPASS_URL, data=query, timeout=45)
    elements = resp.json().get("elements", [])
    school_rows = []
    for el in elements:
        if el["type"] == "node":
            lat, lon = el["lat"], el["lon"]
        else:
            lat, lon = el["center"]["lat"], el["center"]["lon"]
        school_rows.append({"name": el.get("tags", {}).get("name", ""), "geometry": Point(lon, lat)})
    schools_4326 = gpd.GeoDataFrame(school_rows, crs="EPSG:4326")
    schools = schools_4326.to_crs(epsg=3857)
    print(f"  {len(schools)} schools loaded")
except Exception as e:
    print(f"  School fetch failed ({e}). Skipping overlay.")
    schools = None

# ════════════════════════════════════════════════════════════════════════════
# OPTION 1 — Childcare vs Schools
# ════════════════════════════════════════════════════════════════════════════

print("\n[1/3] Childcare vs Schools map…")
fig, ax = plt.subplots(figsize=(12, 10))

if schools is not None:
    schools.plot(ax=ax, color="#e74c3c", markersize=10, marker="^",
                 alpha=0.65, label=f"Schools ({len(schools)})", zorder=3)

childcare.plot(ax=ax, color="#2980b9", markersize=6, alpha=0.55,
               label=f"Childcare Centers ({len(childcare)})", zorder=4)

ctx.add_basemap(ax, source=ctx.providers.CartoDB.Positron, zoom=11)
ax.set_title("Childcare Centers vs Schools — Seattle Area",
             fontsize=15, fontweight="bold", pad=12)
ax.legend(loc="upper left", fontsize=11, framealpha=0.9)
ax.set_axis_off()
plt.tight_layout()
out1 = "map_schools_vs_childcare.png"
plt.savefig(out1, dpi=150, bbox_inches="tight")
plt.close()
print(f"  Saved {out1}")

# ════════════════════════════════════════════════════════════════════════════
# OPTION 2 — Density heatmap
# ════════════════════════════════════════════════════════════════════════════

print("\n[2/3] Childcare density heatmap…")
# Use Web Mercator (EPSG:3857) throughout — same CRS contextily uses natively
from pyproj import Transformer
_t = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)

xs = childcare.geometry.x.values
ys = childcare.geometry.y.values

# Normalise to avoid numerical issues in KDE
xs_n = (xs - xs.mean()) / xs.std()
ys_n = (ys - ys.mean()) / ys.std()
kde = gaussian_kde(np.vstack([xs_n, ys_n]), bw_method=0.15)

pad = 8000  # metres
x_min, x_max = xs.min() - pad, xs.max() + pad
y_min, y_max = ys.min() - pad, ys.max() + pad
xi_m, yi_m = np.mgrid[x_min:x_max:400j, y_min:y_max:400j]
xi_n = (xi_m - xs.mean()) / xs.std()
yi_n = (yi_m - ys.mean()) / ys.std()
zi = kde(np.vstack([xi_n.ravel(), yi_n.ravel()])).reshape(xi_m.shape)

threshold = zi.max() * 0.05
levels = np.linspace(threshold, zi.max(), 20)

fig, ax = plt.subplots(figsize=(13, 11))
# Set axis limits BEFORE adding basemap so contextily fetches the right tiles
ax.set_xlim(x_min, x_max)
ax.set_ylim(y_min, y_max)
ctx.add_basemap(ax, source=ctx.providers.CartoDB.Positron, zoom=11, zorder=1)

contour = ax.contourf(xi_m, yi_m, zi, levels=levels,
                      cmap="YlOrRd", alpha=0.72, zorder=2)

cbar = plt.colorbar(contour, ax=ax, shrink=0.55, pad=0.02)
cbar.set_ticks([levels[0], levels[-1]])
cbar.set_ticklabels(["Lower density", "Higher density"])
cbar.ax.tick_params(labelsize=10, length=0)

childcare.plot(ax=ax, color="black", markersize=3, alpha=0.35, zorder=3)

# Neighbourhood labels (convert from WGS84 → Web Mercator)
LABELS = [
    (-122.335, 47.610, "Downtown Seattle"),
    (-122.337, 47.627, "South Lake Union"),
    (-122.303, 47.655, "University District"),
    (-122.357, 47.668, "Ballard"),
    (-122.304, 47.734, "Shoreline / Kenmore"),
    (-122.201, 47.610, "Bellevue"),
    (-122.122, 47.674, "Redmond"),
    (-122.217, 47.480, "Renton"),
    (-122.346, 47.686, "Northgate"),
    (-122.330, 47.578, "SoDo / Georgetown"),
]
for lon, lat, name in LABELS:
    mx, my = _t.transform(lon, lat)
    if x_min < mx < x_max and y_min < my < y_max:
        ax.annotate(name, xy=(mx, my), fontsize=8, color="#1a1a2e",
                    fontweight="bold", ha="center", va="center", zorder=5,
                    bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.7, ec="none"))

ax.set_title("Childcare Center Density — Seattle Area",
             fontsize=15, fontweight="bold", pad=10)
ax.text(0.5, 0.98,
        "Dark orange = many centers nearby  ·  No color = few or none  ·  Dots = individual centers",
        transform=ax.transAxes, ha="center", va="top",
        fontsize=9, color="#555", style="italic")
ax.set_axis_off()
plt.tight_layout()
out2 = "map_heatmap.png"
plt.savefig(out2, dpi=150, bbox_inches="tight")
plt.close()
print(f"  Saved {out2}")

# ════════════════════════════════════════════════════════════════════════════
# OPTION 3 — Where childcare should go (gaps near job centers)
# ════════════════════════════════════════════════════════════════════════════

print("\n[3/3] Childcare gap analysis near job centers…")

EMPLOYMENT_CENTERS = [
    ("Downtown Seattle",     47.6062, -122.3321),
    ("South Lake Union",     47.6270, -122.3368),
    ("University District",  47.6553, -122.3035),
    ("Bellevue Downtown",    47.6101, -122.2015),
    ("Redmond / Microsoft",  47.6740, -122.1215),
    ("Renton",               47.4799, -122.2171),
    ("Kirkland",             47.6815, -122.2087),
    ("Burien",               47.4701, -122.3468),
    ("Northgate",            47.6855, -122.3257),
    ("SoDo / Industrial",    47.5771, -122.3296),
    ("Bellevue Tech Corr.",  47.5951, -122.1871),
    ("Lynnwood",             47.8209, -122.3151),
]

emp_gdf = gpd.GeoDataFrame(
    [{"name": n, "geometry": Point(lon, lat)} for n, lat, lon in EMPLOYMENT_CENTERS],
    crs="EPSG:4326"
).to_crs(epsg=3857)

BUFFER_M = 2500  # 2.5 km radius

def count_nearby(buf_geom):
    return int(childcare[childcare.geometry.within(buf_geom)].shape[0])

emp_gdf["buffer"] = emp_gdf.geometry.buffer(BUFFER_M)
emp_gdf["childcare_count"] = emp_gdf["buffer"].apply(count_nearby)

def coverage_label(n):
    if n >= 10:
        return "Good"
    if n >= 4:
        return "Moderate"
    return "Low — needs investment"

emp_gdf["coverage"] = emp_gdf["childcare_count"].apply(coverage_label)

buf_gdf = emp_gdf.set_geometry("buffer")

fig, ax = plt.subplots(figsize=(13, 11))

buf_gdf.plot(
    ax=ax,
    column="childcare_count",
    cmap="RdYlGn",
    alpha=0.45,
    legend=True,
    legend_kwds={"label": "Childcare centers within 2.5 km", "shrink": 0.65},
)

childcare.plot(ax=ax, color="#2980b9", markersize=5, alpha=0.45,
               label="Childcare Centers", zorder=4)

emp_gdf.set_geometry("geometry").plot(
    ax=ax, color="black", markersize=80, marker="*",
    zorder=6, label="Job Centers"
)

for _, row in emp_gdf.iterrows():
    ax.annotate(
        f"{row['name']}\n({row['childcare_count']})",
        xy=(row.geometry.x, row.geometry.y),
        xytext=(6, 6), textcoords="offset points",
        fontsize=7.5,
        color="darkred" if row["childcare_count"] < 4 else "black",
        fontweight="bold" if row["childcare_count"] < 4 else "normal",
    )

ctx.add_basemap(ax, source=ctx.providers.CartoDB.Positron, zoom=11)
ax.set_title("Where Childcare Is Needed — Gaps Near Job Centers",
             fontsize=15, fontweight="bold", pad=12)
ax.legend(loc="upper left", fontsize=10, framealpha=0.9)
ax.set_axis_off()
plt.tight_layout()
out3 = "map_childcare_gaps.png"
plt.savefig(out3, dpi=150, bbox_inches="tight")
plt.close()
print(f"  Saved {out3}")

# ── Summary table ────────────────────────────────────────────────────────────
summary = emp_gdf[["name", "childcare_count", "coverage"]].rename(columns={
    "name": "Job Center",
    "childcare_count": "Childcare Centers (2.5 km)",
    "coverage": "Coverage",
})
summary = summary.sort_values("Childcare Centers (2.5 km)")
summary.to_csv("childcare_coverage_summary.csv", index=False)
print("\nCoverage summary:")
print(summary.to_string(index=False))

# ════════════════════════════════════════════════════════════════════════════
# HTML REPORT
# ════════════════════════════════════════════════════════════════════════════

print("\nGenerating HTML report…")

def table_html(df):
    rows = ""
    for _, r in df.iterrows():
        color = ""
        if "Low" in str(r["Coverage"]):
            color = ' style="background:#fde8e8;"'
        elif "Moderate" in str(r["Coverage"]):
            color = ' style="background:#fef9e7;"'
        else:
            color = ' style="background:#eafaf1;"'
        rows += f"<tr{color}>" + "".join(f"<td>{v}</td>" for v in r) + "</tr>\n"
    headers = "".join(f"<th>{c}</th>" for c in df.columns)
    return f"<table><thead><tr>{headers}</tr></thead><tbody>{rows}</tbody></table>"

img1_b64 = img_to_b64(out1)
img2_b64 = img_to_b64(out2)
img3_b64 = img_to_b64(out3)

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Childcare GIS Analysis — Seattle</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: "Segoe UI", Arial, sans-serif; background: #f4f6f9; color: #222; }}
  header {{ background: #1a3a5c; color: #fff; padding: 2rem 2.5rem; }}
  header h1 {{ font-size: 1.9rem; }}
  header p  {{ margin-top: .4rem; opacity: .85; font-size: .95rem; }}
  main {{ max-width: 1100px; margin: 2rem auto; padding: 0 1.5rem; }}
  section {{ background: #fff; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,.08);
             padding: 2rem; margin-bottom: 2.5rem; }}
  h2 {{ font-size: 1.35rem; color: #1a3a5c; margin-bottom: .5rem; }}
  .badge {{ display:inline-block; background:#e8f0fe; color:#1a3a5c; border-radius:4px;
            padding:2px 8px; font-size:.8rem; font-weight:bold; margin-left:.5rem; }}
  p.desc {{ color: #555; line-height: 1.6; margin: .7rem 0 1.2rem; }}
  img {{ width: 100%; border-radius: 8px; border: 1px solid #dde; display:block; }}
  table {{ border-collapse: collapse; width: 100%; font-size: .9rem; margin-top: 1rem; }}
  th {{ background: #1a3a5c; color: #fff; padding: .55rem .8rem; text-align: left; }}
  td {{ padding: .5rem .8rem; border-bottom: 1px solid #eee; }}
  .key-stats {{ display: flex; gap: 1.5rem; flex-wrap: wrap; margin: 1rem 0; }}
  .stat-box {{ background: #e8f0fe; border-radius: 8px; padding: 1rem 1.5rem; flex: 1; min-width: 140px; }}
  .stat-box .num {{ font-size: 2rem; font-weight: bold; color: #1a3a5c; }}
  .stat-box .lbl {{ font-size: .85rem; color: #555; margin-top: .25rem; }}
  footer {{ text-align: center; padding: 1.5rem; color: #888; font-size: .85rem; }}
</style>
</head>
<body>

<header>
  <h1>Childcare GIS Analysis — Seattle Metro Area</h1>
  <p>Generated {date.today().strftime("%B %d, %Y")} &nbsp;·&nbsp; {len(childcare)} childcare centers &nbsp;·&nbsp; {len(schools) if schools is not None else "N/A"} schools</p>
</header>

<main>

  <!-- Key stats -->
  <section>
    <h2>At a Glance</h2>
    <div class="key-stats">
      <div class="stat-box"><div class="num">{len(childcare)}</div><div class="lbl">Childcare Centers</div></div>
      <div class="stat-box"><div class="num">{len(schools) if schools is not None else "—"}</div><div class="lbl">Schools (OSM)</div></div>
      <div class="stat-box"><div class="num">{sum(1 for c in emp_gdf["childcare_count"] if c < 4)}</div><div class="lbl">Job Centers with Low Coverage</div></div>
      <div class="stat-box"><div class="num">{len(EMPLOYMENT_CENTERS)}</div><div class="lbl">Employment Centers Analysed</div></div>
    </div>
  </section>

  <!-- Option 1 -->
  <section>
    <h2>Option 1 — Childcare Centers vs Schools <span class="badge">Overlay</span></h2>
    <p class="desc">
      Blue dots mark licensed childcare centers; red triangles show schools
      (sourced from OpenStreetMap via Overpass API). Together they reveal
      whether childcare supply clusters near schools, or if gaps exist in
      areas that serve working families.
    </p>
    <img src="data:image/png;base64,{img1_b64}" alt="Childcare vs Schools map">
  </section>

  <!-- Option 2 -->
  <section>
    <h2>Option 2 — Density Heatmap <span class="badge">Where It's Dense vs Lacking</span></h2>
    <p class="desc">
      Gaussian kernel density estimation reveals hotspots (deep red/orange)
      and underserved areas (pale yellow or white). High-density clusters
      appear in central Seattle and the Eastside corridor; large gaps are
      visible in south and east King County.
    </p>
    <img src="data:image/png;base64,{img2_b64}" alt="Heatmap">
  </section>

  <!-- Option 3 -->
  <section>
    <h2>Option 3 — Where Childcare Should Go <span class="badge">Gap Analysis</span></h2>
    <p class="desc">
      Each circle shows a 2.5 km buffer around a major employment center.
      Green = adequate supply; yellow = moderate; red = low coverage.
      Areas shaded red with few childcare centers despite high job density
      are the strongest candidates for new facility investment.
    </p>
    <img src="data:image/png;base64,{img3_b64}" alt="Gap analysis map">

    <h2 style="margin-top:1.5rem;">Coverage by Job Center</h2>
    {table_html(summary.reset_index(drop=True))}
  </section>

</main>

<footer>
  Data: King County / ArcGIS Open Data · OpenStreetMap contributors · Analysis by Claude Code
</footer>
</body>
</html>
"""

with open("index.html", "w") as f:
    f.write(html)

print("Saved index.html")
print("\nAll done!")
