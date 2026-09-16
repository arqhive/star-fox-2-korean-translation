import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from sf2_lz import decompress
def walk(rom, bank):
    base = (bank & 0x3F) * 0x8000
    end = 0x10000
    while end > 0x8000 and rom[base + end - 0x8000 - 1] == 0xFF: end -= 1
    blobs = []
    e = end
    while e > 0x8000:
        try:
            d, s, st = decompress(rom, bank, e)
            if not (0x8000 <= s < e) or len(d) == 0 or len(d) > 0x10000: raise ValueError('bad')
        except Exception as ex:
            blobs.append({'bank': bank, 'end': e, 'error': str(ex)}); break
        blobs.append({'bank': bank, 'start': s, 'end': e, 'size': len(d)})
        e = s
    return end, blobs[::-1]
if __name__ == '__main__':
    rom = open(sys.argv[1], 'rb').read()
    out = []
    for bank in [int(x, 16) for x in sys.argv[3].split(',')]:
        end, bl = walk(rom, bank)
        print('bank %02X data end %04X blobs %d%s' % (bank, end, len(bl), ' ERROR at %04X' % bl[0]['end'] if bl and 'error' in bl[0] else ''))
        out += bl
    json.dump(out, open(sys.argv[2], 'w'), indent=0)
