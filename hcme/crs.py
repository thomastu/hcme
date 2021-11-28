from pyproj import Proj

UTM10 = Proj(proj="utm", zone=10, ellps="WGS84")
WGS84 = Proj(proj="latlong", ellps="WGS84")
