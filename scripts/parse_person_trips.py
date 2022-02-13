"""
TODO:
- Figure out why BEAM agents keep choosing Walk as travel mode even when car is available and preferable
    - I think this is because people aren't starting at home, we should re-upload trips to enforce a home-start for everyone.

- Implement tool to track individual journeys from events.
"""
import click
import geopandas as gpd
import pandas as pd
import plotly.express as px
import sqlalchemy as sa

from hcme.config import mapbox_token
from hcme.db import engine, models

px.set_mapbox_access_token(mapbox_token)

pd.set_option("display.max_columns", None)


def parse_journey(agent_events_fp, person_id):
    agent_events = pd.read_csv(agent_events_fp)

    person_events = agent_events.query("person == @person_id").dropna(axis=1, how="all")
    links = person_events["link"].dropna().tolist()

    q = sa.select(
        models.Link.id,
        models.Link.geometry.label("geometry"),
        models.Link.from_node_id,
        models.Link.to_node_id,
    ).where(models.Link.id.in_(links))

    segments = gpd.read_postgis(q, con=engine, geom_col="geometry")

    # Separate out latitudes and longitudes
    coordinates = segments.geometry.apply(lambda x: x.coords.xy)
    # Concatenate all the latitudes and longitudes into one list

    longitudes = coordinates.str.get(0).sum().tolist()
    latitudes = coordinates.str.get(1).sum().tolist()

    # Create a new linestring
    fig = px.line_mapbox(lon=longitudes, lat=latitudes)
    fig.show()


@click.command()
@click.argument("agent_events_fp", type=click.Path(exists=True))
@click.argument("person_id", type=int)
def main(agent_events_fp, person_id):
    """Create a map of a single agent's daily travel journal based on BEAM events.

    Args:
        events_fp (str): Path to BEAM events file.
        person_id (int): Person ID to plot.

    Example:
        $ python scripts/plot_person_trips.py data/events.csv 1
    """
    parse_journey(agent_events_fp, person_id)


if __name__ == "__main__":

    main()
