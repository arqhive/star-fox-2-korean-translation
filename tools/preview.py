"""Render dialogue strings from a built ROM using the in-ROM font pages (offline check)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from PIL import Image
from sf2font import Font
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def render(rom, ids, out, table=0x2DA5, scale=2, maxw=300):
    from sf2font import font_pages
    fonts = font_pages(rom)
    rows = []
    for i in ids:
        p = int.from_bytes(rom[table+2*i:table+2*i+2], 'little') - 0x8000
        s = rom[p+2:rom.index(0, p+2)]
        img = Image.new('L', (maxw, 12 + 2), 30); x = 0; y = 1; lines = [img]
        k = 0
        while k < len(s):
            b = s[k]; k += 1; f = fonts[0]
            if b < 0x10:
                f = fonts[b]; b = s[k]; k += 1
            if b == 0x11: x -= 1; continue
            g = f.glyph_of(b) if b >= 0x21 else None
            if g is None: x += 6; continue
            gi = f.glyph_img(g)
            if x + gi.width > maxw:
                img = Image.new('L', (maxw, 14), 30); lines.append(img); x = 0
            img.paste(gi, (x, 1)); x += gi.width + 1
        rows += lines + [Image.new('L', (maxw, 3), 90)]
    H = sum(r.height for r in rows)
    canvas = Image.new('L', (maxw, H)); yy = 0
    for r in rows: canvas.paste(r, (0, yy)); yy += r.height
    canvas.resize((maxw*scale, H*scale), Image.NEAREST).save(out)

if __name__ == '__main__':
    rom = open(sys.argv[1], 'rb').read()
    ids = [int(x) for x in sys.argv[3].split(',')]
    render(rom, ids, sys.argv[2])
