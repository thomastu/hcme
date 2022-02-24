"""
"""
import sqlalchemy as sa
import geopandas as gpd
import plotly.express as px

from hcme.db import models, engine
from hcme.config import mapbox_token

px.set_mapbox_token(mapbox_token)


if __name__ == "__main__":
    gdf = gpd.read_postgis(
        sa.select(models.TAZ.id, models.TAZ.name, models.TAZ.geometry),
        geom_col="geometry",
    )

    # Set center of map
    c = gdf.dissolve().centroid
    center = {"lon": c.x, "lat": c.y}

    plt = px.choropleth_mapbox(
        gdf,
        geojson=gdf.geometry,
        center=center,
        labels="name",
        locations=df.index,
        color="id",
        zoom=7.5,
        width=600,
        height=800,
    )
    plt.update_coloraxes(showscale=False)
    plt.update_layout(showlegend=False)
    plt.write_image("tazs.png")
