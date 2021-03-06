#!/usr/bin/python3

from struct import unpack, pack
from json import loads, dumps
from sys import argv
from os import path
from functools import reduce
from imp import load_source
absolute_path = path.split(path.abspath(__file__))[0] + "/"
svgtopng = load_source('svgtopng', absolute_path + 'svgtopng.py')


def getFromDict(dataDict, mapList):
    try:
        return reduce(lambda d, k: d[k], mapList, dataDict)
    except KeyError:
        exit()

def setInDict(dataDict, mapList, value):
    getFromDict(dataDict, mapList[:-1])[mapList[-1]] = value

# iterative funtion to account for the new size of the png bytearray
def change_dict_vals(d, sizediff, offset):
    if isinstance(d, dict):
        d2 = {k: change_dict_vals(v, sizediff, offset) for k, v in d.items()}
        if d2.get('offset') and int(d2.get('offset')) > offset:
            d2['offset'] = str(int(d2['offset']) + sizediff)
        return d2
    return d


filename = argv[3] + argv[4]
icon_to_repl = argv[2]
icon_for_repl = argv[1]

# uses google's pickle format, which prefixes each field
# with its total length, the first field is a 32-bit unsigned
# integer, thus 4 bytes, we know that, so we skip it
try:
    asarfile = open(filename, 'rb')
except FileNotFoundError:
    exit()
asarfile.seek(4)

# header size is stored in byte 12:16
len1 = unpack('I', asarfile.read(4))[0]
len2 = unpack('I', asarfile.read(4))[0]
len3 = unpack('I', asarfile.read(4))[0]
header_size = len3
zeros_padding = (len2 - 4 - len3)

header = asarfile.read(header_size).decode('utf-8')

files = loads(header)
originaloffset = asarfile.tell() + zeros_padding
asarfile.close()

keys = icon_to_repl.split('/')

try:
    fileinfo = getFromDict(files, keys)
except KeyError:
    exit()
try:
    offset0 = int(fileinfo['offset'])
except KeyError:
    exit()
offset = offset0 + originaloffset
size = int(fileinfo['size'])

with open(filename, 'rb') as asarfile:
    bytearr = asarfile.read()

filename_svg, file_extension = path.splitext(icon_for_repl)
if file_extension == '.svg':
    if svgtopng.is_svg_enabled():
        pngbytes = svgtopng.convert_svg2bin(icon_for_repl)
    else:
        pngbytes = None
else:
    with open(icon_for_repl, 'rb') as pngfile:
        pngbytes = pngfile.read()

if pngbytes:
    setInDict(files, keys + ['size'], len(pngbytes))

    newbytearr = pngbytes.join([bytearr[:offset], bytearr[offset + size:]])

    sizediff = len(pngbytes) - size

    newfiles = change_dict_vals(files, sizediff, offset0)
    newheader = dumps(newfiles).encode('utf-8')
    newheaderlen = len(newheader)

    bytearr2 = b''.join([bytearr[:4], pack('I', newheaderlen + (len1 - len3)),
                         pack('I', newheaderlen + (len2 - len3)),
                         pack('I', newheaderlen), newheader,
                         b'\x00' * zeros_padding,
                         newbytearr[originaloffset:]])

    asarfile = open(filename, 'wb')
    asarfile.write(bytearr2)
    asarfile.close()
