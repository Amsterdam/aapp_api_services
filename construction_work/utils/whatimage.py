"""
This code was copied from the "whatimage" project: https://github.com/david-poirier/whatimage
Since the project is no longer active, the source code is available here.
This logic might be better replaced by a better maintained library.
"""


def identify_tiff(data):
    if len(data) < 4:
        return
    if data[0:2] == b"MM":
        if int.from_bytes(data[2:4], byteorder="big") == 42:
            return "tiff"
    if data[0:2] == b"II":
        if int.from_bytes(data[2:4], byteorder="little") == 42:
            return "tiff"


def identify_bmp(data):
    if len(data) < 2:
        return
    if data[0:2] == b"BM":
        return "bmp"


def identify_pbm(data):
    if len(data) < 2:
        return
    if data[0:2] == b"P4":
        return "pbm"


def identify_pgm(data):
    if len(data) < 2:
        return
    if data[0:2] == b"P5":
        return "pgm"


def identify_ppm(data):
    if len(data) < 2:
        return
    if data[0:2] == b"P6":
        return "ppm"


def identify_gif(data):
    if len(data) < 6:
        return None
    if data[:6] in [b"GIF87a", b"GIF89a"]:
        return "gif"


def identify_png(data):
    if len(data) < 4:
        return None
    if data[0] == 0x89 and data[1:4] == b"PNG":
        return "png"


def identify_jpeg(data):
    if len(data) < 3:
        return None
    if data[0] == 0xFF and data[1] == 0xD8 and data[2] == 0xFF:
        return "jpeg"


def identify_webp(data):
    if len(data) < 12:
        return None
    if data[0:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"


def _identify_heic(major_brand, minor_version, compatible_brands):
    container_brands = [b"mif1", b"msf1"]
    coding_brands = [b"heic", b"heix", b"hevc", b"hevx"]
    if major_brand in coding_brands:
        return "heic"
    if major_brand in container_brands:
        for cb in compatible_brands:
            if cb in coding_brands:
                return "heic"


def _identify_avif(major_brand, minor_version, compatible_brands):
    container_brands = [b"mif1", b"msf1"]
    coding_brands = [b"avif", b"avis"]
    if major_brand in coding_brands:
        return "avif"
    if major_brand in container_brands:
        for cb in compatible_brands:
            if cb in coding_brands:
                return "avif"


def identify_isobmff(data):
    if len(data) < 8:
        return
    if data[4:8] != b"ftyp":
        return
    ftyp_len = int.from_bytes(data[0:4], "big")
    if len(data) < ftyp_len:
        return
    major_brand = data[8:12]
    minor_version = int.from_bytes(data[12:16], "big")
    compatible_brands = []
    for offset in range(16, ftyp_len, 4):
        compatible_brands.append(data[offset : offset + 4])

    for func in [_identify_heic, _identify_avif]:
        fmt = func(major_brand, minor_version, compatible_brands)
        if fmt:
            return fmt


identify_functions = [
    identify_jpeg,
    identify_png,
    identify_gif,
    identify_webp,
    identify_isobmff,
    identify_bmp,
    identify_tiff,
    identify_pbm,
    identify_pgm,
    identify_ppm,
]


def identify_image(data):
    for func in identify_functions:
        fmt = func(data)
        if fmt:
            return fmt
