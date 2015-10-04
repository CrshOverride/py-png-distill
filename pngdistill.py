#!/usr/bin/env python

from cStringIO import StringIO
from shutil import copyfileobj
from zopfli.zlib import compress
from zlib import decompress
import png

CHUNKS_TO_DROP = ['tEXt', 'iTXt', 'zTXt', 'prVW', 'mkBF', 'mkTS', 'mkBS', 'mkBT']

def _reduce_chunks(acc, c):
    # Keep one, and only one, IDAT chunk as a placeholder for the re-compressed data
    if c[0] == 'IDAT':
        if not any(ec[0] == 'IDAT' for ec in acc):
            acc.append(c)
    elif c[0] not in CHUNKS_TO_DROP:
        acc.append(c)

    return acc

def distill(f=None, filename=None):
    if filename:
        f = open(filename)

    if not f:
        raise ValueError('No file was supplied to distill')

    reader = png.Reader(f)
    chunks = [(ct, c) for (ct, c) in reader.chunks()]
    rebuilt_idat_chunk = build_idat_chunk(chunks)
    distilled_chunks = reduce(_reduce_chunks, chunks, [])

    def _remap_chunks(acc, c):
        if c[0] == 'IDAT':
            acc.append(rebuilt_idat_chunk)
        else:
            acc.append(c)

        return acc

    result_chunks = reduce(_remap_chunks, distilled_chunks, [])
    result = StringIO()
    png.write_chunks(result, result_chunks)
    return result

def build_idat_chunk(chunks):
    deflated = ''.join([chunk for (chunk_type, chunk) in chunks if chunk_type == 'IDAT'])
    decompressed = decompress(deflated)
    return ('IDAT', compress(decompressed))

if __name__ == "__main__":
    import sys
    result = distill(filename=sys.argv[1])
    result.seek(0)
    with open(sys.argv[2], 'w+') as output_file:
        copyfileobj(result, output_file)

