import fiona
import geopandas as gpd

from geoalchemy2 import WKTElement

from hcme.config import input_data
from hcme.db import Session
from hcme.db.models.registry import TAZ


gpd.io.file.fiona.drvsupport.supported_drivers["KML"] = "rw"


def main():
    """Write the aggregated TAZs to the database."""
    tazs = gpd.read_file(str(input_data.aggregated_tazs), driver="KML")

    # Parse through descriptive attributes
    re_name = r"(?<=name\:\s)\w+$"
    re_id = r"(?<=^id\:\s)\d+(?=\W+br\W+)"

    tazs["name"] = tazs["Description"].str.findall(re_name).str.get(0)
    tazs["id"] = tazs["Description"].str.findall(re_id).str.get(0).astype(int)

    # Open session
    session = Session()

    # Write the geopandas dataframe to the taz table
    buffer = []
    for index, row in tazs.iterrows():
        row = dict(
            id=row["id"],
            name=row["name"],
            geometry=WKTElement(row.geometry.wkt, srid=4326),
        )
        buffer.append(row)

    session.bulk_insert_mappings(TAZ, buffer)
    session.commit()


if __name__ == "__main__":

    assert input_data.aggregated_tazs.exists(), "Missing input file for aggregated TAZs"

    main()
