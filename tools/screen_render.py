"""Offline SNES screen composer from Mesen dumps (vram.bin, cgram.bin, oam.bin) for mode-1 screens.

Tiles whose VRAM content matches a blob tile of the *reference* ROM can be replaced by the same
blob tile decompressed from a *new* ROM, so image-text edits can be previewed on a real screen.

  python tools/screen_render.py dumpdir ref_rom new_rom out.png
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from PIL import Image
from sf2_lzpy import decompress

BLOBS = [(0x18, 0xDF19), (0x17, 0xAA48), (0x17, 0x9B74), (0x19, 0x8A80), (0x16, 0xE5F8), (0x18, 0xA6FF), (0x18, 0xEAE9)]


def load(d, n):
    return open(os.path.join(d, n), 'rb').read()


def tile_pixels(buf, off):
    tb = buf[off:off + 32]
    return [[((tb[y * 2] >> (7 - x)) & 1) | ((tb[y * 2 + 1] >> (7 - x)) & 1) << 1 |
             ((tb[16 + y * 2] >> (7 - x)) & 1) << 2 | ((tb[16 + y * 2 + 1] >> (7 - x)) & 1) << 3
             for x in range(8)] for y in range(8)]


def build_replacements(ref, new):
    """map vram-tile-bytes(ref) -> replacement 32 bytes from new rom"""
    rep = {}
    for bank, end in BLOBS:
        base = bank * 0x8000 - 0x8000
        try:
            a, _ = decompress(ref, base + end)
            b, _ = decompress(new, base + end)
        except Exception:
            continue
        for t in range(min(len(a), len(b)) // 32):
            ta, tbb = a[t * 32:t * 32 + 32], b[t * 32:t * 32 + 32]
            if any(ta) and ta not in rep:
                rep[ta] = tbb
    return rep


def render(d, ref_rom=None, new_rom=None, bg1_width=64, bg1=True):
    v = bytearray(load(d, 'vram.bin')); cg = load(d, 'cgram.bin'); oam = load(d, 'oam.bin')
    if ref_rom and new_rom:
        rep = build_replacements(open(ref_rom, 'rb').read(), open(new_rom, 'rb').read())
        for t in range(0x10000 // 32):
            r = rep.get(bytes(v[t * 32:t * 32 + 32]))
            if r is not None:
                v[t * 32:t * 32 + 32] = r

    def color(i):
        w = cg[i * 2] | cg[i * 2 + 1] << 8
        return ((w & 31) * 255 // 31, (w >> 5 & 31) * 255 // 31, (w >> 10 & 31) * 255 // 31)

    img = Image.new('RGB', (256, 224), color(0))
    layers = ((0x9000, 32), (0x8000, bg1_width)) if bg1 else ((0x9000, 32),)
    for base, width in layers:          # BG2 then BG1
        for row in range(28):
            for col in range(32):
                o = base + (row * width + col) * 2
                e = v[o] | v[o + 1] << 8
                t = e & 0x3FF; pal = (e >> 10) & 7
                px = tile_pixels(v, t * 32)
                for y in range(8):
                    for x in range(8):
                        sx = 7 - x if e & 0x4000 else x; sy = 7 - y if e & 0x8000 else y
                        ci = px[sy][sx]
                        if ci:
                            img.putpixel((col * 8 + x, row * 8 + y), color(pal * 16 + ci))
    for i in range(127, -1, -1):
        x, y, t, a = oam[i * 4:i * 4 + 4]
        hi = (oam[512 + i // 4] >> ((i % 4) * 2)) & 3
        if y >= 224:
            continue
        x |= (hi & 1) << 8
        if x >= 256:
            x -= 512
        size = 16 if hi & 2 else 8
        base = 0xC000 + (0x2000 if a & 1 else 0)
        pal = (a >> 1) & 7
        for yy in range(size):
            for xx in range(size):
                sx = size - 1 - xx if a & 0x40 else xx; sy = size - 1 - yy if a & 0x80 else yy
                tt = t + (sy // 8) * 16 + sx // 8
                ci = tile_pixels(v, base + tt * 32)[sy % 8][sx % 8]
                X, Y = x + xx, y + yy
                if ci and 0 <= X < 256 and 0 <= Y < 224:
                    img.putpixel((X, Y), color(128 + pal * 16 + ci))
    return img


if __name__ == '__main__':
    d, ref, new, out = sys.argv[1:5]
    render(d, ref if ref != '-' else None, new if new != '-' else None).resize((512, 448), Image.NEAREST).save(out)
