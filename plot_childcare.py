import matplotlib.pyplot as plt
import contextily as ctx

gdf = gpd.read_file("childcare_seattle.geojson", engine="pyogrio")

# Your data is in Web Mercator already
gdf = gdf.set_crs(epsg=3857, allow_override=True)

fig, ax = plt.subplots(figsize=(10, 10))

gdf.plot(
    ax=ax,
    markersize=8,
    alpha=0.6
)

# Add basemap
ctx.add_basemap(ax, source=ctx.providers.CartoDB.Positron)

ax.set_title("Childcare Centers in Seattle Area")
ax.set_axis_off()

plt.savefig("childcare_map_basemap.png", dpi=200, bbox_inches="tight")
print("Saved childcare_map_basemap.png")
