"""Render a 4bpp tile blob with grid + tile numbers (index colours -> grey or given palette)."""
import sys
from PIL import Image, ImageDraw
def load_tiles(data):
    n = len(data)//32; out = []
    for t in range(n):
        tb = data[t*32:t*32+32]; px = []
        for y in range(8):
            a,b,c,d = tb[y*2],tb[y*2+1],tb[16+y*2],tb[16+y*2+1]
            px.append([((a>>(7-x))&1)|((b>>(7-x))&1)<<1|((c>>(7-x))&1)<<2|((d>>(7-x))&1)<<3 for x in range(8)])
        out.append(px)
    return out
def save_tiles(tiles):
    out = bytearray()
    for px in tiles:
        tb = bytearray(32)
        for y in range(8):
            for x in range(8):
                v = px[y][x]
                for p in range(4):
                    if v >> p & 1:
                        off = (y*2 + (p & 1)) + (16 if p >= 2 else 0)
                        tb[off] |= 0x80 >> x
        out += tb
    return bytes(out)
def render(tiles, cols=16, first=0, count=None, scale=4, grid=True, pal=None):
    count = count or len(tiles)-first
    rows = (count+cols-1)//cols
    img = Image.new('RGB', (cols*8, rows*8))
    for i in range(count):
        px = tiles[first+i]
        for y in range(8):
            for x in range(8):
                v = px[y][x]
                col = pal[v] if pal else (v*17, v*17, v*17)
                img.putpixel((i%cols*8+x, i//cols*8+y), col)
    img = img.resize((img.width*scale, img.height*scale), Image.NEAREST)
    if grid:
        d = ImageDraw.Draw(img)
        for i in range(count):
            x0 = i%cols*8*scale; y0 = i//cols*8*scale
            d.rectangle([x0, y0, x0+8*scale-1, y0+8*scale-1], outline=(90,0,0))
            d.text((x0+1, y0), '%X' % (first+i), fill=(255,60,60))
    return img
if __name__ == '__main__':
    data = open(sys.argv[1],'rb').read()
    first = int(sys.argv[3],16) if len(sys.argv)>3 else 0
    count = int(sys.argv[4],16) if len(sys.argv)>4 else None
    cols = int(sys.argv[5]) if len(sys.argv)>5 else 16
    render(load_tiles(data), cols, first, count).save(sys.argv[2])
