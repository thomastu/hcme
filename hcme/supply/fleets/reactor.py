"""
Create a fleet scenario
"""
from dataclasses import dataclass, field
from typing import List, Tuple

import geoalchemy2 as ga
import geopandas as gpd
import pandas as pd
import plotly.express as px
import shapely
import sqlalchemy as sa
from geovoronoi import voronoi_regions_from_coords
from shapely.ops import transform

from hcme.config import artifacts, input_data, mapbox_token
from hcme.constants import METERS_TO_MILE
from hcme.crs import UTM10, WGS84, wgs84_to_utm10
from hcme.db import Session, engine, models

px.set_mapbox_access_token(mapbox_token)


output = artifacts.figures / ""


def create_travel_zones(
    boundary_region: "shapely.geometry.base.BaseGeometry",
    poi: gpd.GeoDataFrame,
    ridership_pool: gpd.GeoDataFrame,
):
    ridership_pool = ridership_pool.to_crs("EPSG:4326")
    regions, region_keys = voronoi_regions_from_coords(
        poi.geometry.to_crs("EPSG:4326"), boundary_region
    )
    locations = []
    session = Session()
    for region_id, region in regions.items():
        ridership = ridership_pool[ridership_pool.geometry.intersects(region)]
        n = ridership.shape[0]
        if n:
            area = transform(wgs84_to_utm10.transform, region).area
            riders_per_m2 = n / area
            nearest_poi = poi.iloc[region_keys[region_id][0]]
            centroid = ridership.dissolve().representative_point().iloc[0]

            # Get nearest node in physssim network
            q_nearest_node = (
                sa.select(models.Node.coordinates)
                .order_by(
                    ga.functions.ST_Distance(
                        models.Node.coordinates, ga.functions.ST_GeomFromWKB(centroid.wkb, 4326)
                    )
                )
                .limit(1)
            )
            nearest_node = transform(
                wgs84_to_utm10.transform,
                ga.shape.to_shape(session.execute(q_nearest_node).first()[0]),
            )

            # Determine minimum service radius
            minimum_service_radius = nearest_poi.geometry.distance(nearest_node)

            locations.append(
                {
                    "num_households": n,
                    "ridership_centroid": centroid,
                    "ridership_centroid_nearest_node": nearest_node,
                    "min_geofence_range": minimum_service_radius,
                    "area_m2": area,
                    "num_agents": n,
                    "agents_per_m2": riders_per_m2,
                    "region": region,
                    "poi_id": nearest_poi.name,
                    "poi_coords": nearest_poi.geometry,
                    "region_id": region_id,
                }
            )
    return locations


def generate_boundary_from_tazs(q=None) -> "shapely.geometry.base.BaseGeometry":
    """Generate a boundary from TAZs"""

    boundary = (
        gpd.read_postgis(
            sa.select(ga.functions.ST_Union(models.TAZ.geometry).label("geometry")),
            con=engine,
            geom_col="geometry",
        )
        .iloc[0]
        .geometry
    )
    return boundary


def ridership_from_last_mile_stops(
    pois: gpd.GeoDataFrame, distance_threshold_mi: float = 0.25, max_distance_mi: float = 2
):
    """Create a GeoDataFrame of households that are in 'last mile' range to the input Points-of-interest."""
    households = gpd.read_postgis(
        sa.select(models.Household, models.Location).join(
            models.Location, models.Household.location_id == models.Location.id
        ),
        con=engine,
        geom_col="coordinates",
    )
    ridership = (
        households.to_crs(UTM10.crs)
        .sjoin_nearest(
            pois.to_crs(UTM10.crs),
            how="left",
            distance_col="distance_m",
        )
        .to_crs(epsg=4326)
    )
    ridership["distance_miles"] = ridership["distance_m"] * METERS_TO_MILE
    ridership = ridership.query(
        "distance_miles >= @distance_threshold_mi and distance_miles <= @max_distance_mi"
    ).copy()
    return ridership


def ridership_from_last_mile_trip_origins(
    pois: gpd.GeoDataFrame, distance_threshold_mi: float = 0.25, max_distance_mi: float = 2
):
    """Create a GeoDataFrame of trips that are in 'last mile' range to the input points of interest"""
    trips = gpd.read_postgis(
        sa.select(models.Trip, models.Location).join(
            models.Location, models.Trip.origin_location_id == models.Location.id
        ),
        con=engine,
        geom_col="coordinates",
    )
    ridership = (
        trips.to_crs(UTM10.crs)
        .sjoin_nearest(
            pois.to_crs(UTM10.crs),
            how="left",
            distance_col="distance_m",
        )
        .to_crs(epsg=4326)
    )
    ridership["distance_miles"] = ridership["distance_m"] * METERS_TO_MILE
    ridership = ridership.query(
        "distance_miles >= @distance_threshold_mi and distance_miles <= @max_distance_mi"
    ).copy()
    return ridership


@dataclass
class FleetReactor:

    boundary: "shapely.geometry.base.BaseGeometry"
    service_range: int
    vehicle_type: str = "MT_SHUTTLE"
    shifts: List[Tuple] = field(
        default_factory=lambda: [
            (7 * 3600, 19 * 3600),
        ]
    )

    def run(self, pois: gpd.GeoDataFrame, ridership_pool: gpd.GeoDataFrame, fleet_size: int):
        """ """
        data = create_travel_zones(self.boundary, pois, ridership_pool)

        zones = gpd.GeoDataFrame(data, geometry="poi_coords").set_crs(WGS84.crs).to_crs(UTM10.crs)
        zones["shuttles"] = 1
        zones["agents_per_m2_per_shuttle"] = zones["agents_per_m2"] / zones["shuttles"]
        zones = zones.sort_values("agents_per_m2_per_shuttle", ascending=False)
        n = zones.shape[0]

        rh_fleet = []
        shifts = ";".join(
            "{{{}}}".format(":".join(map(str, s))) for s in sorted(self.shifts, key=lambda x: x[0])
        )
        # Set first shuttle as most agents per m^2
        datum = zones.iloc[0]

        service_range = self.service_range / METERS_TO_MILE

        # shuttles = []

        for i in range(fleet_size):
            coords_utm10 = datum["poi_coords"]
            vehicle = {
                "id": f"mt-{i}",
                "rideHailManagerId": "HAYL",
                "vehicleType": self.vehicle_type,
                "initialLocationX": coords_utm10.x,
                "initialLocationY": coords_utm10.y,
                "shifts": shifts,
                "geofenceX": coords_utm10.x,
                "geofenceY": coords_utm10.y,
                "geofenceRadius": service_range,
            }
            rh_fleet.append(vehicle)

            # Recalculate where there are the most shuttles within a service area.
            # shuttles.append(coords_utm10)
            # S = gpd.GeoSeries(shuttles).set_crs(UTM10.crs)
            # service_buffer = zones.geometry.buffer(service_range)
            zones.loc[datum.name, "shuttles"] += 1
            zones["agents_per_m2_per_shuttle"] = zones["agents_per_m2"] / zones["shuttles"]
            zones = zones.sort_values("agents_per_m2_per_shuttle", ascending=False)
            datum = zones.iloc[0]
        return rh_fleet


"""
id,rideHailManagerId,vehicleType,initialLocationX,initialLocationY,shifts,geofenceX,geofenceY,geofenceRadius
rideHailVehicle-49,HAYL,BEV,172151.0125,3081.44259,{10:22000};{30000:80000},172151.0125,3081.44259,500
"""


if __name__ == "__main__":
    boundary = generate_boundary_from_tazs()
    reactor = FleetReactor(boundary, 2)

    # Use existing stops as POIs
    stops = gpd.GeoDataFrame(pd.read_csv(input_data.gtfs_dir / "stops.txt"))
    stops = stops.set_geometry(gpd.points_from_xy(stops.stop_lon, stops.stop_lat)).set_crs(
        epsg=4326
    )

    # Consider both household and trip-origins for ridership
    ridership_scenarios = {
        "last_mile_trip_origin": ridership_from_last_mile_trip_origins,
        "last_mile_stops": ridership_from_last_mile_stops,
    }
    fleets = {}
    for scenario, func in ridership_scenarios.items():
        ridership = func(stops, 0.25, 2.5)
        rh_fleet_gdf = reactor.run(stops, ridership, fleet_size=100)
        rh_fleet_gdf.to_csv()
        fleets[scenario] = rh_fleet_gdf
