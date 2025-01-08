# Generating the OSM Network for BeAM

1.  Download the larger "super-region" from here (~2GB): https://download.geofabrik.de/north-america/us-west.html
2.  Download the shapefile for Humboldt county: https://humboldtgov.org/276/GIS-Data-Download
    1. Alternatively, for a smaller analysis zone, download just the major city boundaries (including Rio Dell, Fortuna, Ferndale, Arcata, Eureka )
3.  Install GDAL and run this script: https://github.com/smellman/ogr2poly/ (e.g. `python ogr2poly.py humboldt.shp > humboldt.poly` where `humboldt.shp` is the path to the shapefile from step 2)
    - `python ogr2poly.py humboldt.shp > humboldt.poly`
    - `python ogr2poly.py cities.shp > humboldt-cities.poly`
4.  Install osmosis: `sudo apt install osmosis`
5.  Use `osmosis` to "clip" the super region from step 1 to the analysis region of interest: 
    1. For all of humboldt county: `osmosis --read-pbf file=us-west-latest.osm.pbf --bounding-polygon file=humboldt.poly completeWays=yes completeRelations=yes clipIncompleteEntities=true --write-pbf humboldt.osm.pbf`
    1. setting `completeWays=yes` could result in some funkiness with the actual included boundary for multi-polygons. So for just the cities, this might require a 2-step process:
        - `osmosis --read-pbf file=us-west-latest.osm.pbf --bounding-polygon file=humboldt-cities.poly completeWays=yes completeRelations=yes clipIncompleteEntities=true --write-pbf humboldt-cities.osm.pbf`
        - `osmosis --read-pbf file=humboldt-cities.osm.pbf --bounding-polygon file=humboldt.poly completeWays=yes completeRelations=yes clipIncompleteEntities=true --write-pbf humboldt-cities-clipped.osm.pbf`
