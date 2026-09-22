"""Refine v1.0 graphics while preserving its dialogue, font locations and code.

python tools/build_graphics.py --rom original.sfc --baseline v1.0_ko.sfc --out v1.1.sfc
--baseline takes an existing v1.0 Korean ROM (build it from the v1.0 tag if needed).
Only verified graphics streams and the SNES checksum may change. No relocation.
"""
import argparse
import hashlib
from pathlib import Path

from build_ko import SOURCE_SHA1
from freespace import bank_end_padding
from gfx_ko import find_refs, load_spec, patch_rom
from sf2_lzpy import compress, decompress

BASELINE_SHA1 = '89f871e2e12d10a8460cc10996a4829296091dad'


def blob_end(source, rom, bank, end):
    refs = find_refs(source, bank, end)
    targets = {(rom[bo] - 1) * 0x8000 + int.from_bytes(rom[ao:ao + 2], 'little')
               for _, ao, bo in refs}
    if not targets:
        return (bank - 1) * 0x8000 + end
    if len(targets) != 1:
        raise ValueError('inconsistent graphics pointers')
    return targets.pop()


def build(source, baseline):
    if hashlib.sha1(source).hexdigest() != SOURCE_SHA1:
        raise ValueError('original Japanese ROM SHA1 mismatch')
    if hashlib.sha1(baseline).hexdigest() != BASELINE_SHA1:
        raise ValueError('baseline must be the unmodified Korean v1.0 ROM')
    scratch = bytearray(source)
    patch_rom(scratch, pool=bank_end_padding(scratch, skip_banks=(1,)))
    result = bytearray(baseline)
    allowed = bytearray(len(result))
    for spec in load_spec():
        name = spec['blob']
        bank, start, end = int(name[:2], 16), int(name[3:7], 16), int(name[8:12], 16)
        old_end = blob_end(source, baseline, bank, end)
        new_end = blob_end(source, scratch, bank, end)
        old_data, old_start = decompress(baseline, old_end)
        new_data, new_start = decompress(scratch, new_end)
        if old_data == new_data:
            continue
        if len(old_data) != len(new_data):
            raise ValueError('graphics tile count changed: ' + name)
        if old_end != (bank - 1) * 0x8000 + end:
            raise ValueError('changed block was relocated; needs explicit allocation: ' + name)
        blob = scratch[new_start:new_end]
        target_start = old_end - len(blob)
        # The old freed head may contain a dialogue font. Repack graphics more
        # tightly if necessary, rather than moving that font or changing code.
        if target_start < old_start and any(v != 0xFF for v in baseline[target_start:old_start]):
            candidate = compress(new_data, optimize=True)
            if len(candidate) < len(blob):
                blob = candidate
                target_start = old_end - len(blob)
        if target_start < (bank - 1) * 0x8000 + start:
            raise ValueError('graphics block exceeds original allocation: ' + name)
        if target_start < old_start and any(v != 0xFF for v in baseline[target_start:old_start]):
            raise ValueError('graphics growth would overwrite occupied data: ' + name)
        write_start = min(old_start, target_start)
        result[write_start:target_start] = b'\xff' * (target_start - write_start)
        result[target_start:old_end] = blob
        allowed[write_start:old_end] = b'\x01' * (old_end - write_start)
        if decompress(result, old_end)[0] != new_data:
            raise ValueError('graphics verification failed: ' + name)
        print('%s: %d -> %d compressed bytes' % (name, old_end - old_start, len(blob)))

    result[0x7FDC:0x7FE0] = b'\xff\xff\x00\x00'
    checksum = sum(result) & 0xFFFF
    result[0x7FDC:0x7FE0] = (checksum ^ 0xFFFF).to_bytes(2, 'little') + checksum.to_bytes(2, 'little')
    allowed[0x7FDC:0x7FE0] = b'\x01' * 4
    if len(result) != len(baseline) or any(a != b and not ok for a, b, ok in zip(baseline, result, allowed)):
        raise ValueError('unexpected change outside graphics and checksum')
    return bytes(result)


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--rom', required=True)
    ap.add_argument('--baseline', required=True, help='existing v1.0 Korean ROM')
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    source = Path(args.rom).read_bytes()
    baseline = Path(args.baseline).read_bytes()
    rom = build(source, baseline)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(rom)
    print('wrote', out, 'SHA1', hashlib.sha1(rom).hexdigest())
