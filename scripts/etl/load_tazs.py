import fiona
import geopandas as gpd

from geoalchemy2 import WKTElement

from hcme.config import input_data
from hcme.db import Session
from hcme.db.models.registry import TAZ
from hcme.utils import assert_depends_on


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
    write_buffer = []
    update_buffer = []
    # Make idempotent
    # Query for existing TAZs with IDs in tazs

    existing_tazs = session.query(TAZ.id).filter(TAZ.id.in_(tazs["id"])).all()

    for _, row in tazs.iterrows():
        row = dict(
            id=row["id"],
            name=row["name"],
            geometry=WKTElement(row.geometry.wkt, srid=4326),
        )
        # Skip any rows that already exist
        if row["id"] in existing_tazs:
            update_buffer.append(row)
        else:
            write_buffer.append(row)

    session.bulk_insert_mappings(TAZ, write_buffer)
    session.bulk_update_mappings(TAZ, update_buffer)
    session.commit()


depends_on = (input_data.aggregated_tazs,)


if __name__ == "__main__":
    assert_depends_on(depends_on)
    main()
