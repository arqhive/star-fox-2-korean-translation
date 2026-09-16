"""Minimal BDF reader -> 1-bit glyph images aligned on a common baseline."""
from PIL import Image
class BDF:
    def __init__(self, path):
        self.glyphs = {}
        lines = open(path, encoding='utf-8', errors='replace').read().splitlines()
        i = 0
        while i < len(lines):
            l = lines[i]
            if l.startswith('FONT_ASCENT'): self.ascent = int(l.split()[1])
            elif l.startswith('FONT_DESCENT'): self.descent = int(l.split()[1])
            elif l.startswith('STARTCHAR'):
                enc = None; bbx = None; dw = None; rows = []
                i += 1
                while not lines[i].startswith('ENDCHAR'):
                    t = lines[i].split()
                    if t[0] == 'ENCODING': enc = int(t[1])
                    elif t[0] == 'BBX': bbx = tuple(map(int, t[1:5]))
                    elif t[0] == 'DWIDTH': dw = int(t[1])
                    elif t[0] == 'BITMAP':
                        i += 1
                        while not lines[i].startswith('ENDCHAR'):
                            rows.append(int(lines[i], 16)); i += 1
                        break
                    i += 1
                if enc is not None and enc >= 0:
                    self.glyphs[enc] = (bbx, dw, rows)
            i += 1
        self.height = self.ascent + self.descent

    def glyph(self, ch):
        """returns (img 'L' of size (dwidth, height), dwidth); ink=255"""
        g = self.glyphs.get(ord(ch))
        if g is None: return None
        (w, h, xo, yo), dw, rows = g
        img = Image.new('L', (max(dw, xo + w, 1), self.height), 0)
        nbytes = (w + 7) // 8
        top = self.ascent - (yo + h)
        for r, v in enumerate(rows):
            for x in range(w):
                if v >> (nbytes * 8 - 1 - x) & 1:
                    X, Y = xo + x, top + r
                    if 0 <= X < img.width and 0 <= Y < img.height: img.putpixel((X, Y), 255)
        return img, dw

    def text(self, s, spacing=0):
        parts = [self.glyph(c) for c in s]
        W = sum(p[1] + spacing for p in parts if p) - spacing
        img = Image.new('L', (max(W, 1), self.height), 0); x = 0
        for p in parts:
            if not p: continue
            img.paste(p[0].crop((0, 0, p[1], self.height)), (x, 0)); x += p[1] + spacing
        return img
