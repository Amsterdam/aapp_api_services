from pyproj import Transformer

# Initialize transformer: from WGS84 (EPSG:4326) to WGS84 (EPSG:4326) Rijksdriehoek (EPSG:28992),
# always_xy=True: the transform method will accept as input and return as output
# coordinates using the traditional GIS order, that is long, lat for geographic CRS and easting, northing for most projected CRS.
transformer = Transformer.from_crs(
    crs_from="EPSG:4326", crs_to="EPSG:28992", always_xy=True
)


def wgs_to_rd(lon: float, lat: float):
    """
    lon: longitude in decimal degrees
    lat: latitude in decimal degrees
    returns: (x, y): Rijksdriehoek X (Easting), Rijksdriehoek Y (Northing)
    """
    x, y = transformer.transform(lon, lat)
    return x, y
