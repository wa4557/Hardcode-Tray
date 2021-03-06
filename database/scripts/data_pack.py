#!/usr/bin/env python3

# Copyright (c) 2012 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE directory.

"""Support for formatting a data pack file used for platform agnostic resource
files.
"""

from collections import namedtuple
from os import path as os_path
from struct import unpack, pack
from sys import path as sys_path
if __name__ == '__main__':
    sys_path.append(os_path.join(os_path.dirname(__file__), '../..'))


PACK_FILE_VERSION = 4
# Two uint32s. (file version, number of entries) and
# one uint8 (encoding of text resources)
HEADER_LENGTH = 2 * 4 + 1
BINARY, UTF8, UTF16 = list(range(3))
RAW_TEXT = 1


data_pack_contents = namedtuple('DataPackContents',
                                'resources encoding')


def ReadFile(filename, encoding):
    '''Reads and returns the entire contents of the given file.
    Args:
       filename: The path to the file.
       encoding: A Python codec name or one of two special values:
            BINARY to read the file in binary mode,or
            RAW_TEXT to read it with newline conversion
            but without decoding to Unicode.
    '''
    mode = 'rb' if encoding == BINARY else 'rU'
    with open(filename, mode) as f:
        data = f.read()
    if encoding not in (BINARY, RAW_TEXT):
        data = data.decode(encoding)
    return data


def ReadDataPack(input_file):
    """Reads a data pack file and returns a dictionary."""
    data = ReadFile(input_file, BINARY)
    original_data = data

    # Read the header.
    version, num_entries, encoding = unpack('<IIB',
                                            data[:HEADER_LENGTH])
    if version != PACK_FILE_VERSION:
        print('Wrong file version in {0!s}'.format(input_file))
        raise Exception

    resources = {}
    if num_entries == 0:
        return data_pack_contents(resources, encoding)

    # Read the index and data.
    data = data[HEADER_LENGTH:]
    index_entry = 2 + 4  # Each entry is a uint16 and a uint32.
    for _ in range(num_entries):
        _id, offset = unpack('<HI', data[:index_entry])
        data = data[index_entry:]
        next_offset = unpack('<HI', data[:index_entry])[1]
        resources[_id] = original_data[offset:next_offset]

    return data_pack_contents(resources, encoding)


def WriteDataPackToString(resources, encoding):
    """Returns a string with a map of id=>data in the data pack format."""
    ids = sorted(resources.keys())
    ret = []

    # Write file header.
    ret.append(pack('<IIB', PACK_FILE_VERSION, len(ids), encoding))
    HEADER_LENGTH = 2 * 4 + 1            # Two uint32s and one uint8.

    # Each entry is a uint16 + a uint32s. We have one extra entry for the last
    # item.
    index_length = (len(ids) + 1) * (2 + 4)

    # Write index.
    data_offset = HEADER_LENGTH + index_length
    for _id in ids:
        ret.append(pack('<HI', _id, data_offset))
        data_offset += len(resources[_id])

    ret.append(pack('<HI', 0, data_offset))

    # Write data.
    for _id in ids:
        ret.append(resources[_id])
    return b''.join(ret)


def WriteDataPack(resources, output_file, encoding):
    """Writes a map of id=>data into output_file as a data pack."""
    content = WriteDataPackToString(resources, encoding)
    with open(output_file, 'wb') as file:
        file.write(content)
