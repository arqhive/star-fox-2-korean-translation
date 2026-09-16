"""Korean graphics patcher for Star Fox 2 (JP).

Spec: translation/gfx_ko.py defines BLOBS = [ {blob, bpp, items:[...]}, ... ]
Item keys:
  rect   : (x, y, w, h) area in the blob image (16 tiles per row)
  tiles  : optional list of tile indices forming a virtual horizontal strip (8px tall rows);
           when given, rect is relative to that strip
  text   : Korean string ('\n' for multiple lines)
  font   : 'g7' | 'g9' | 'g11' | 'g11b' | 'g11c'
  fg, bg : colour indices; clear: indices replaced by bg inside rect (default [fg] + shadow)
  shadow : (index, dx, dy) optional ; outline: index optional (8-neighbour)
  align  : 'center' (default) | 'left' ; valign 'center' | 'top'
  spacing: extra px between glyphs (can be negative)
  fill   : True -> fill whole rect with bg first
"""
import os, sys, json, importlib.util
sys.path.insert(0, os.path.dirname(__file__))
from PIL import Image
from bdf import BDF
from blobimg import to_pixels, from_pixels, show
from sf2_lzpy import decompress, compress

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = {'g7': 'Galmuri7.bdf', 'g7s': 'Galmuri7.bdf', 'g9': 'Galmuri9.bdf', 'g11': 'Galmuri11.bdf', 'g11b': 'Galmuri11-Bold.bdf',
         'g11c': 'Galmuri11-Condensed.bdf'}
_cache = {}


def font(name):
    if name not in _cache:
        _cache[name] = BDF(os.path.join(ROOT, 'fonts', FONTS[name]))
    return _cache[name]


def squeeze_glyph(im):
    """im: 'L' glyph image; returns 6-row version of rows 2..8"""
    rows = [[1 if im.getpixel((x, y)) else 0 for x in range(im.width)] for y in range(2, 9)]
    def cost(r):
        cand = rows[:r] + rows[r + 1:]
        c = sum(rows[r])
        if r > 0 and rows[r] == rows[r - 1]: c -= 100      # duplicate of the row above
        if r < 6 and rows[r] == rows[r + 1]: c -= 100
        if r in (0, 6): c += 3                            # keep outer strokes when possible
        return c
    r = min(range(7), key=cost)
    rows = rows[:r] + rows[r + 1:]
    out = Image.new('L', (im.width, 6), 0)
    for y, row in enumerate(rows):
        for x, v in enumerate(row):
            if v: out.putpixel((x, y), 255)
    return out


def squeeze_line(f, text, spacing):
    parts = []
    for ch in text:
        g = f.glyph(ch)
        if g is None: continue
        parts.append((squeeze_glyph(g[0].crop((0, 0, g[1], g[0].height))), g[1]))
    W = max(1, sum(dw + spacing for _, dw in parts) - spacing)
    img = Image.new('L', (W, 6), 0); x = 0
    for im, dw in parts:
        img.paste(im, (x, 0)); x += dw + spacing
    return img


def text_mask(s, fname, spacing=0, line_gap=1):
    f = font(fname)
    lines = s.split('\n')
    if fname == 'g7s':  # Galmuri7 squeezed to 6 rows (per glyph: drop the least informative row)
        imgs = [squeeze_line(f, l, spacing) for l in lines]
    else:
        imgs = [f.text(l, spacing) for l in lines]
    # crop each line to ink rows (keep consistent top across lines: use font-wide hangul box)
    crops = []
    for im in imgs:
        bb = im.getbbox() or (0, 0, 1, 1)
        crops.append(im.crop((bb[0], 0, bb[2], im.height)))
    # vertical ink bounds across all lines
    top = min((im.getbbox() or (0, 0, 0, 0))[1] for im in imgs)
    bot = max((im.getbbox() or (0, 0, 0, 1))[3] for im in imgs)
    lh = bot - top
    W = max(c.width for c in crops)
    H = lh * len(lines) + line_gap * (len(lines) - 1)
    return [(c.crop((0, top, c.width, bot))) for c in crops], lh, W, H


def apply_item(px, it):
    if it.get('vflip') or it.get('hflip'):
        x, y, w, h = it.get('flip_rect', it['rect'])
        def flip():
            if it.get('vflip'):
                rows = [px[yy][x:x + w] for yy in range(y, y + h)]
                for i, yy in enumerate(range(y, y + h)):
                    px[yy][x:x + w] = rows[h - 1 - i]
            if it.get('hflip'):
                for yy in range(y, y + h):
                    px[yy][x:x + w] = px[yy][x:x + w][::-1]
        flip()
        it2 = dict(it); it2.pop('vflip', None); it2.pop('hflip', None)
        apply_item(px, it2)
        flip()
        return
    x, y, w, h = it['rect']
    fg = it['fg']; bg = it['bg']
    sh = it.get('shadow'); ol = it.get('outline')
    clear = set(it.get('clear', [fg] + ([sh[0]] if sh else []) + ([ol] if ol is not None else [])))
    cx, cy, cw, ch = it.get('clear_rect', it['rect'])
    for yy in range(cy, cy + ch):
        for xx in range(cx, cx + cw):
            if it.get('fill') or px[yy][xx] in clear:
                px[yy][xx] = bg
    if not it.get('text'):
        return
    lines, lh, W, H = text_mask(it['text'], it['font'], it.get('spacing', 0), it.get('line_gap', 1))
    oy = y + (h - H) // 2 if it.get('valign', 'center') == 'center' else y
    oy += it.get('dy', 0)
    ink = []
    for li, im in enumerate(lines):
        lw = im.width
        ox = x + (w - lw) // 2 if it.get('align', 'center') == 'center' else x
        ox += it.get('dx', 0)
        ly = oy + li * (lh + it.get('line_gap', 1))
        for yy in range(im.height):
            for xx in range(im.width):
                if im.getpixel((xx, yy)):
                    ink.append((ox + xx, ly + yy))
    if it.get('bold'):
        ink = ink + [(X + 1, Y) for X, Y in ink]
    inkset = set(ink)
    clip = it.get('clip')
    def put(X, Y, v):
        if clip and not (clip[0] <= X < clip[0] + clip[2] and clip[1] <= Y < clip[1] + clip[3]):
            return
        if 0 <= Y < len(px) and 0 <= X < len(px[0]):
            px[Y][X] = v
    shade = [(X + sh[1], Y + sh[2]) for X, Y in ink] if sh else []
    body = inkset | set(shade)
    if ol is not None:
        for X, Y in body:
            for ddx in (-1, 0, 1):
                for ddy in (-1, 0, 1):
                    if (X + ddx, Y + ddy) not in body:
                        put(X + ddx, Y + ddy, ol)
    if sh:
        for X, Y in ink:
            if (X + sh[1], Y + sh[2]) not in inkset:
                put(X + sh[1], Y + sh[2], sh[0])
    fb = it.get('fg_bottom')     # (colour, rows from bottom of each line)
    for X, Y in ink:
        col = fg
        if fb:
            li = (Y - oy) // (lh + it.get('line_gap', 1))
            ly0 = oy + li * (lh + it.get('line_gap', 1))
            if Y - ly0 >= lh - fb[1]: col = fb[0]
        put(X, Y, col)
    fitw = W <= w; fith = H <= h
    if not (fitw and fith):
        print('  WARNING: text "%s" (%dx%d) exceeds rect %dx%d' % (it['text'].replace('\n', '/'), W, H, w, h))


def strip_view(px, tiles):
    """build virtual strip rows from tile list (1 row of len(tiles)*8)"""
    S = [[0] * (8 * len(tiles)) for _ in range(8)]
    for i, t in enumerate(tiles):
        tx, ty = t % 16 * 8, t // 16 * 8
        for yy in range(8):
            for xx in range(8):
                S[yy][i * 8 + xx] = px[ty + yy][tx + xx]
    return S


def strip_back(px, S, tiles):
    for i, t in enumerate(tiles):
        tx, ty = t % 16 * 8, t // 16 * 8
        for yy in range(8):
            for xx in range(8):
                px[ty + yy][tx + xx] = S[yy][i * 8 + xx]


def load_spec():
    p = os.path.join(ROOT, 'translation', 'gfx_ko.py')
    spec = importlib.util.spec_from_file_location('gfx_spec', p)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m.BLOBS


def find_refs(rom, bank, end):
    """65816 references to a blob: returns list of (kind, offset_of_addr_word, offset_of_bank_byte)"""
    refs = []
    lo, hi = end & 0xFF, end >> 8
    pat1 = bytes([0xA9, bank, 0x00, 0x8F, 0x6A, 0x00, 0x70, 0xA9, lo, hi, 0x8F, 0x68, 0x00, 0x70])
    i = rom.find(pat1)
    while i >= 0:
        refs.append(('lda', i + 8, i + 1)); i = rom.find(pat1, i + 1)
    pat2 = bytes([lo, hi, bank, 0, 0, 0])
    i = rom.find(pat2)
    while i >= 0:
        if rom[i - 3] == 0x20 and rom[i - 1] == 0xD6:
            refs.append(('inline', i, i + 2))
        i = rom.find(pat2, i + 1)
    return refs


def patch_rom(rom, preview_dir=None, only=None, pool=None):
    """rom: bytearray (JP layout). modifies in place. returns report list.
    pool: freespace.Pool used for blobs that grew; freed blob heads are added to it."""
    report = []
    for b in load_spec():
        name = b['blob']
        if only and name not in only:
            continue
        bank = int(name[:2], 16); s = int(name[3:7], 16); e = int(name[8:12], 16)
        base = bank * 0x8000 - 0x8000
        data, start = decompress(rom, base + e)
        assert start == base + s, name
        bpp = b.get('bpp', 4); ts = 32 if bpp == 4 else 16
        px, n = to_pixels(data, bpp)
        orig = [row[:] for row in px]
        for it in b['items']:
            if 'tiles' in it:
                S = strip_view(px, it['tiles'])
                apply_item(S, it)
                strip_back(px, S, it['tiles'])
            else:
                apply_item(px, it)
        new = from_pixels(px, n, bpp) + data[n * ts:]
        blob = compress(new)
        chk, _ = decompress(blob, len(blob))
        assert chk == new
        room = e - s
        if len(blob) <= room:
            rom[base + e - len(blob):base + e] = blob
            for i in range(base + s, base + e - len(blob)):   # freed head, never read
                rom[i] = 0xFF
            if pool is not None:
                pool.add(base + s, room - len(blob))
            report.append((name, room, len(blob)))
        else:
            refs = find_refs(rom, bank, e)
            if not refs:
                raise SystemExit('blob %s grew (%d > %d) and no references found' % (name, len(blob), room))
            if pool is None:
                raise SystemExit('blob %s grew and no free-space pool given' % name)
            off = pool.alloc(len(blob), rom)
            rom[off:off + len(blob)] = blob
            nbank = off // 0x8000
            new_end = 0x8000 + off % 0x8000 + len(blob)
            assert new_end <= 0x10000
            for kind, ao, bo in refs:
                rom[ao] = new_end & 0xFF; rom[ao + 1] = new_end >> 8; rom[bo] = nbank
            print('  %s relocated to %02X:%04X (%d refs)' % (name, nbank, new_end, len(refs)))
            report.append((name, room, len(blob)))
        if preview_dir:
            os.makedirs(preview_dir, exist_ok=True)
            pal = b.get('preview_pal')
            H = len(px)
            a = show(orig, pal=pal, scale=3, grid=False); c = show(px, pal=pal, scale=3, grid=False)
            img = Image.new('RGB', (a.width * 2 + 6, a.height), (255, 0, 0))
            img.paste(a, (0, 0)); img.paste(c, (a.width + 6, 0))
            img.save(os.path.join(preview_dir, name + '.png'))
    return report


if __name__ == '__main__':
    # preview only: python tools/gfx_ko.py <jp_rom> [blob,blob]
    from freespace import bank_end_padding
    rom = bytearray(open(sys.argv[1], 'rb').read())
    only = sys.argv[2].split(',') if len(sys.argv) > 2 else None
    for r in patch_rom(rom, os.path.join(ROOT, 'work', 'gfx_preview'), only, bank_end_padding(rom, skip_banks=(1,))):
        print('%s  room %d  new %d' % r)
