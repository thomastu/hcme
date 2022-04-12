"""
"""
import geopandas as gpd
import plotly.express as px
import plotly.graph_objects as go
import sqlalchemy as sa

from hcme.config import artifacts, mapbox_token
from hcme.db import engine, models

px.set_mapbox_access_token(mapbox_token)


if __name__ == "__main__":
    gdf = gpd.read_postgis(
        sa.select(models.TAZ.id, models.TAZ.name, models.TAZ.geometry),
        con=engine,
        geom_col="geometry",
    )

    # Set center of map
    c = gdf.dissolve().centroid
    center = {"lon": float(c.x), "lat": float(c.y)}

    plt = px.choropleth_mapbox(
        gdf,
        geojson=gdf.geometry,
        center=center,
        labels="name",
        locations=gdf.index,
        color="id",
        zoom=7.5,
        width=600,
        height=800,
    )
    text_trace = go.Scattermapbox(
        lat=gdf.centroid.y,
        lon=gdf.centroid.x,
        text=gdf["id"].astype(str),
        mode="text",
        name="TAZ id",
    )
    plt.add_trace(text_trace)
    plt.update_coloraxes(showscale=False)
    plt.update_layout(showlegend=False, margin={"t": 0, "r": 0, "b": 0, "l": 0})
    plt.update_geos(fitbounds="locations")

    plt.write_image(artifacts.figures / "tazs.png", scale=4.0)
    plt.write_html(artifacts.figures / "tazs.html")
