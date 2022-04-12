from pyproj import Proj, Transformer

UTM10 = Proj(proj="utm", zone=10, ellps="WGS84")
WGS84 = Proj(proj="latlong", ellps="WGS84")

utm10_to_wgs84 = Transformer.from_crs(UTM10.crs, WGS84.crs)
wgs84_to_utm10 = Transformer.from_crs(WGS84.crs, UTM10.crs)
