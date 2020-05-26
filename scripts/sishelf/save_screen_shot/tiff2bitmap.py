# -*- coding: utf-8 -*-
'''
convert TIFF format file into Bitmap.

    usage:
        import tiff2bitmap
        tiff2bitmap.execute(input, output)
'''

import struct
import binascii


class BMPFileHeader(object):
    # http://www.umekkii.jp/data/computer/file_format/bitmap.cgi
    #
    # struct の fmt 引数の参考
    # https://docs.python.jp/3/library/struct.html
    # 7.1.2.2. 書式指定文字(原文)

    file_type = None      # unsigned int
    size = None           # unsigned long
    reserved1 = None      # unsigned int
    reserved2 = None      # unsigned int
    offset = None         # unsigned long

    def __init__(self, size):
        # type: (int) -> None

        self.file_type = binascii.unhexlify("424D")
        self.size = 54 + size + 6
        self.reserved1 = 0
        self.reserved2 = 0
        self.offset = binascii.unhexlify("36000000")

    def write(self, fp):
        # type:

        fp.write(self.file_type)
        fp.write(struct.pack("L", self.size))
        fp.write(struct.pack("h", self.reserved1))
        fp.write(struct.pack("h", self.reserved2))
        fp.write(self.offset)


class BMPInformationHeader(object):

    size = 40             # unsigned long
    width = None          # long
    height = None         # long
    planes = 1            # unsigned short
    bitsperpixel = 32     # unsigned short
    compression = 0       # unsigned long
    sizeofbitmap = None   # unsigned long
    horizontal_res = 3780 # unsigned long, 96dpi
    vertical_res = 3780   # unsigned long, 96dpi
    colors_used = 0       # unsigned long
    colors_imp = 0        # unsigned long

    def __init__(self, width, height):
        self.width = width
        self.height = height

        self.sizeofbitmap = width * height * 3

    def write(self, fp):

        fp.write(struct.pack("L", self.size))
        fp.write(struct.pack("l", self.width))
        fp.write(struct.pack("l", self.height))
        fp.write(struct.pack("h", self.planes))
        fp.write(struct.pack("h", self.bitsperpixel))
        fp.write(struct.pack("L", self.compression))
        fp.write(struct.pack("L", self.sizeofbitmap))
        fp.write(struct.pack("L", self.horizontal_res))
        fp.write(struct.pack("L", self.vertical_res))
        fp.write(struct.pack("L", self.colors_used))
        fp.write(struct.pack("L", self.colors_imp))


def execute(input_tif, output):

    with open(input_tif, 'rb') as f:
    
        size = struct.unpack_from("xxxxL", f.read(8), 0)[0] - 8
    
        rgb_tiff_body = f.read(size)
        skip = f.read(10)
        width = struct.unpack_from("L", f.read(4), 0)[0]
        skip = f.read(8)
        height = struct.unpack_from("L", f.read(4), 0)[0]

    bgr_bmp_body = ""
    rows = []

    b = "" 
    g = "" 
    r = "" 
    p = ""   # padding reserved
    row = ""

    for i, elem in enumerate(rgb_tiff_body):

        if 0 < i and (i % (width * 4) == 0):
            row = ""

            for j in range(width):
                row += b[j] + g[j] + r[j] + p[j]

            rows.append(row)
            b = ""
            g = ""
            r = ""
            p = ""
   
        if i % 4 == 0:
            # red
            r += elem
   
        if i % 4 == 1:
            # green
            g += elem
   
        if i % 4 == 2:
            # blue
            b += elem
   
        if i % 4 == 3:
            p += elem

    else:
        row = ""
        for j in range(len(b)):
            row += b[j] + g[j] + r[j] + p[j]

        rows.append(row)

    rows.reverse()
    bgr_bmp_body = "".join(rows)
    
    with open(output, 'wb') as f:
    
        file_header = BMPFileHeader(size)
        file_header.write(f)
    
        info_header = BMPInformationHeader(width, height)
        info_header.write(f)
    
        f.write(bgr_bmp_body)


if __name__ == '__main__':
    input = sys.argv[0]
    output = sys.argv[1]

    assert os.path.exists(input), "input file not found"

    execute(input, output)

