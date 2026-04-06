import geopandas as gpd
import matplotlib.pyplot as plt

gdf = gpd.read_file("childcare_seattle.geojson", engine="pyogrio")

# Fix the coordinate system:
# the ArcGIS coordinates are actually Web Mercator
gdf = gdf.set_crs(epsg=3857, allow_override=True)

# Convert to normal lat/lon
gdf = gdf.to_crs(epsg=4326)

fig, ax = plt.subplots(figsize=(8, 8))

gdf.plot(
    ax=ax,
    markersize=5,
    alpha=0.6
)

ax.set_title("Childcare Centers in Seattle Area")
ax.set_xlabel("Longitude")
ax.set_ylabel("Latitude")

plt.savefig("childcare_map_fixed.png", dpi=200, bbox_inches="tight")
print("Saved childcare_map_fixed.png")