"""SNES tile rendering helpers."""
from PIL import Image
def tiles4(data, cols=16, pal=None, scale=2):
    n = len(data) // 32
    img = Image.new('L', (cols*8, ((n+cols-1)//cols)*8))
    for t in range(n):
        tb = data[t*32:t*32+32]
        for y in range(8):
            a, b, c, d = tb[y*2], tb[y*2+1], tb[16+y*2], tb[16+y*2+1]
            for x in range(8):
                s = 7-x
                v = (a>>s&1) | (b>>s&1)<<1 | (c>>s&1)<<2 | (d>>s&1)<<3
                img.putpixel((t%cols*8+x, t//cols*8+y), v*17)
    return img.resize((img.width*scale, img.height*scale), Image.NEAREST)
def tiles2(data, cols=16, scale=2):
    n = len(data) // 16
    img = Image.new('L', (cols*8, ((n+cols-1)//cols)*8))
    for t in range(n):
        tb = data[t*16:t*16+16]
        for y in range(8):
            a, b = tb[y*2], tb[y*2+1]
            for x in range(8):
                s = 7-x; v = (a>>s&1) | (b>>s&1)<<1
                img.putpixel((t%cols*8+x, t//cols*8+y), v*85)
    return img.resize((img.width*scale, img.height*scale), Image.NEAREST)
