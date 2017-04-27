"""
code taken from:
http://stackoverflow.com/questions/902761/saving-a-numpy-array-as-an-image/19174800#19174800
thanks to @ideasman42 and @Evgeni Sergeev
adapted by @kalwalt
"""
import numpy as np


color_type = {'BW': 0, 'RGB': 2, 'RGBA': 6}
color_depth = {'BW': 1, 'RGB': 3, 'RGBA': 4}


def interp(array):
    d = np.interp(array, [0, 1], [0, 255])
    data_uint = np.array(d, dtype=np.uint8)
    return data_uint.flatten().tolist()


def convert(buf):
    array = np.array(buf)
    d = interp(array)
    return d


def write_png(buf, width, height, type, compression=5):

    import zlib, struct

    # reverse the vertical line order and add null bytes at the start
    width_byte = width * color_depth[type]

    raw_data = b''.join(b'\x00' + buf[span:span + width_byte]
                        for span in range((height - 1) * width_byte, -1, - width_byte))

    def png_pack(png_tag, data):
        chunk_head = png_tag + data
        return (struct.pack("!I", len(data)) +
                chunk_head +
                struct.pack("!I", 0xFFFFFFFF & zlib.crc32(chunk_head)))

    t = color_type[type]

    return b''.join([
        b'\x89PNG\r\n\x1a\n',
        png_pack(b'IHDR', struct.pack("!2I5B", width, height, 8, t, 0, 0, 0)),
        png_pack(b'IDAT', zlib.compress(raw_data, compression)),
        png_pack(b'IEND', b'')])


def save_png(filename, buf, type, width, height, compression=5):

    if isinstance(buf, np.ndarray):
        data = interp(buf)
    elif buf:
        data = convert(buf)

    _type = color_type[type]

    if _type not in [0, 2, 6]:
        raise ValueError('Color type not allowed, permitted are: BW, RGB, RGBA')
    if width < 1:
        raise ValueError("Width must be greater than 0")
    if height < 1:
        raise ValueError("Heigt must be greater than 0")
    if not 0 <= compression < 9:
        raise ValueError('compression level not in the range 0...9')

    d = bytearray([int(p)for p in data])
    final_data = write_png(d, width, height, type, compression)
    filename = filename + '.png'
    with open(filename, 'wb') as fd:
        fd.write(final_data)
        print(filename + ' image saved by sv_export_png!')
