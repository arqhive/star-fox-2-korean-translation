"""Simulate the GSU line-wrap (measure routine $01:ED91) on the built ROM."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from sf2font import Font
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load(rom):
    from sf2font import font_pages
    return font_pages(rom)

def chars(body):
    k = 0; out = []
    while k < len(body):
        b = body[k]
        if b < 0x10:
            out.append((body[k:k+2], b, body[k+1])); k += 2
        else:
            out.append((body[k:k+1], 0, b)); k += 1
    return out

def width(fonts, page, code):
    f = fonts[page]
    if code == 0x20 or code < f.first or code > f.last:
        return 6
    g = f.glyph_of(code)
    if g is None: return 6
    return (f.ents[g] >> 11) + 1

def wrap(fonts, body, W):
    cs = chars(body); lines = []; i = 0
    while i < len(cs):
        w = 0; last_space = None; j = i
        while j < len(cs):
            w += width(fonts, cs[j][1], cs[j][2])
            if w > W:
                break
            if cs[j][2] == 0x20 and cs[j][1] == 0: last_space = j
            j += 1
        if j >= len(cs):
            lines.append(cs[i:]); break
        if last_space is not None and last_space > i:
            lines.append(cs[i:last_space]); i = last_space + 1
        else:
            lines.append(cs[i:j] if j > i else cs[i:i+1]); i = max(j, i + 1)
    return lines

if __name__ == '__main__':
    rom = open(sys.argv[1], 'rb').read()
    W = int(sys.argv[2])
    fonts = load(rom)
    import json
    ko = {}
    for l in open(os.path.join(ROOT, 'translation', 'ko.txt'), encoding='utf-8'):
        if '|' in l and not l.startswith('#'):
            a, b = l.rstrip('\n').split('|', 1); ko[int(a)] = b
    table = 0x2DA5
    over = 0
    for i in range(216):
        p = int.from_bytes(rom[table+2*i:table+2*i+2], 'little') - 0x8000
        body = rom[p+2:rom.index(0, p+2)]
        ls = wrap(fonts, body, W)
        if len(ls) > 3 or '-v' in sys.argv:
            over += len(ls) > 3
            print('%03d lines=%d  %s' % (i, len(ls), ko.get(i, '')))
    print('over 3 lines:', over)
