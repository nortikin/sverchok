"""
code taken from:
http://stackoverflow.com/questions/902761/saving-a-numpy-array-as-an-image/19174800#19174800
thanks to @ideasman42 and @Evgeni Sergeev
"""
import numpy as np


color_size = {'BW': 1, 'RGB': 3, 'RGBA': 4}
color_type = {'BW': 0, 'RGB': 2, 'RGBA': 6}


def convert(buf, type, width, height):
    array = np.array(buf)
    print('array', array)
    d = np.interp(array, [0, 1], [0, 255])
    print('from converter', d)
    data_uint = np.array(d, dtype=np.uint8)
    res = np.reshape(data_uint, (width, height, color_size[type]))
    return res.flatten().tolist()


def write_png(buf, width, height, type):
    """ buf: must be bytes or a bytearray in Python3.x,
        a regular string in Python2.x.
    """

    import zlib, struct

    # reverse the vertical line order and add null bytes at the start
    width_byte_4 = width * 4
    raw_data = b''.join(b'\x00' + buf[span:span + width_byte_4]
                        for span in range((height - 1) * width_byte_4, -1, - width_byte_4))

    def png_pack(png_tag, data):
        chunk_head = png_tag + data
        return (struct.pack("!I", len(data)) +
                chunk_head +
                struct.pack("!I", 0xFFFFFFFF & zlib.crc32(chunk_head)))

    t = color_type[type]
    print('color type : ', t)

    return b''.join([
        b'\x89PNG\r\n\x1a\n',
        png_pack(b'IHDR', struct.pack("!2I5B", width, height, 8, t, 0, 0, 0)),
        png_pack(b'IDAT', zlib.compress(raw_data, 9)),
        png_pack(b'IEND', b'')])


def save_png(filename, buf, type, width, height):
    print(buf)
    if buf:
        print('inside save')
        data = convert(buf, type, width, height)
        # data = bytearray([int(p * 255) for p in buf[0]])
        print(data)
        d = bytearray([int(p)for p in data])
        print(d)
        final_data = write_png(d, width, height, type)
        filename = filename + '.png'
        with open(filename, 'wb') as fd:
            fd.write(final_data)
            print('png saved')
