"""Enumerate + decompress all GSU-LZ blobs (banks 15-19) of a ROM into work/blobs_<tag>/."""
import sys, os, json, hashlib
sys.path.insert(0, os.path.dirname(__file__))
from sf2_lz import decompress

def chain_back(rom, b, e, found):
    while e > 0x8000 and (b, e) not in found:
        try:
            d, s, st = decompress(rom, b, e)
            if not (0x8000 <= s < e) or not d or len(d) > 0x10000: return
        except Exception:
            return
        found[(b, e)] = (s, d); e = s

def enumerate_blobs(rom, seeds):
    found = {}
    for bank in (0x15, 0x16, 0x17, 0x18, 0x19):
        base = bank * 0x8000; end = 0x10000
        while end > 0x8000 and rom[base + end - 0x8000 - 1] == 0xFF: end -= 1
        chain_back(rom, bank, end, found)
    for b, e in seeds: chain_back(rom, b, e, found)
    # try to bridge gaps: any start that isn't some other blob's end
    return found

if __name__ == '__main__':
    rom = open(sys.argv[1], 'rb').read(); tag = sys.argv[2]
    seeds = [tuple(int(x, 16) for x in s.split(':')) for s in sys.argv[3].split(',')] if len(sys.argv) > 3 else []
    found = enumerate_blobs(rom, seeds)
    od = os.path.join('work', 'blobs_' + tag); os.makedirs(od, exist_ok=True)
    meta = []
    for (b, e), (s, d) in sorted(found.items()):
        name = '%02X_%04X-%04X' % (b, s, e)
        open(os.path.join(od, name + '.bin'), 'wb').write(d)
        meta.append({'name': name, 'bank': b, 'start': s, 'end': e, 'size': len(d), 'md5': hashlib.md5(d).hexdigest()})
    json.dump(meta, open(os.path.join(od, 'index.json'), 'w'), indent=0)
    print(tag, len(meta), 'blobs')
