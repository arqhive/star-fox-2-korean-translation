"""Blob <-> indexed pixel image (16 tiles per row). bpp 4 or 2."""
import sys
from PIL import Image, ImageDraw
FALSE = [(0,0,0),(255,255,255),(255,0,0),(0,200,0),(0,90,255),(255,255,0),(255,0,255),(0,255,255),
         (128,128,128),(128,0,0),(0,128,0),(0,0,128),(128,128,0),(128,0,128),(0,128,128),(200,160,110)]
def to_pixels(data, bpp=4, cols=16):
    ts = 32 if bpp == 4 else 16
    n = len(data) // ts
    rows = (n + cols - 1) // cols
    W, H = cols * 8, rows * 8
    px = [[0] * W for _ in range(H)]
    for t in range(n):
        tb = data[t*ts:t*ts+ts]; ox, oy = t % cols * 8, t // cols * 8
        for y in range(8):
            if bpp == 4: planes = (tb[y*2], tb[y*2+1], tb[16+y*2], tb[16+y*2+1])
            else: planes = (tb[y*2], tb[y*2+1])
            for x in range(8):
                v = 0
                for p, byte in enumerate(planes): v |= ((byte >> (7-x)) & 1) << p
                px[oy+y][ox+x] = v
    return px, n
def from_pixels(px, n, bpp=4, cols=16):
    ts = 32 if bpp == 4 else 16
    out = bytearray(n * ts)
    for t in range(n):
        ox, oy = t % cols * 8, t // cols * 8
        for y in range(8):
            for x in range(8):
                v = px[oy+y][ox+x]
                for p in range(bpp):
                    if v >> p & 1:
                        off = t*ts + y*2 + (p & 1) + (16 if p >= 2 else 0)
                        out[off] |= 0x80 >> x
    return bytes(out)
def show(px, pal=None, scale=3, region=None, grid=True):
    H, W = len(px), len(px[0])
    x0, y0, x1, y1 = region or (0, 0, W, H)
    img = Image.new('RGB', (x1-x0, y1-y0))
    for y in range(y0, y1):
        for x in range(x0, x1):
            img.putpixel((x-x0, y-y0), (pal or FALSE)[px[y][x]])
    img = img.resize(((x1-x0)*scale, (y1-y0)*scale), Image.NEAREST)
    if grid:
        d = ImageDraw.Draw(img)
        for gx in range((x0//8)*8, x1, 8):
            X = (gx-x0)*scale
            if X >= 0: d.line([(X,0),(X,img.height)], fill=(60,60,60))
        for gy in range((y0//8)*8, y1, 8):
            Y = (gy-y0)*scale
            if Y >= 0:
                d.line([(0,Y),(img.width,Y)], fill=(60,60,60))
                d.text((1, Y), str(gy), fill=(255,120,0))
        for gx in range((x0//16)*16, x1, 16):
            X = (gx-x0)*scale
            if X >= 0: d.text((X+1, 0), str(gx), fill=(0,255,120))
    return img
if __name__ == '__main__':
    d = open(sys.argv[1], 'rb').read(); bpp = int(sys.argv[3])
    px, n = to_pixels(d, bpp)
    region = tuple(int(v) for v in sys.argv[4].split(',')) if len(sys.argv) > 4 else None
    show(px, region=region, scale=int(sys.argv[5]) if len(sys.argv) > 5 else 3).save(sys.argv[2])
