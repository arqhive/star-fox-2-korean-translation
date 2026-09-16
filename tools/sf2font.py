"""Star Fox 2 font reader (GSU proportional 1bpp strip font)."""
from PIL import Image

class Font:
    def __init__(self, rom, base):
        d = rom
        self.base = base
        self.hdr = d[base:base+7]
        self.height = d[base+1]
        self.first = d[base+2]
        self.last = d[base+3]
        n = self.last - self.first + 1
        self.map = list(d[base+7:base+7+n])
        self.nglyph = max(x for x in self.map if x != 0xFF) + 1
        tbl = base+7+n
        self.ents = [int.from_bytes(d[tbl+2*i:tbl+2*i+2], 'little') for i in range(self.nglyph)]
        self.data_start = base + int.from_bytes(d[base+5:base+7], 'little')
        # strip width -> stride
        self.W = max((e & 0x7FF) + (e >> 11) for e in self.ents)
        self.stride = (self.W + 7) // 8
        self.rom = d

    def set_stride(self, s):
        self.stride = s

    def glyph_of(self, code):
        if not (self.first <= code <= self.last): return None
        g = self.map[code - self.first]
        return None if g == 0xFF else g

    def glyph_img(self, g):
        e = self.ents[g]; x0 = e & 0x7FF; w = e >> 11
        img = Image.new('L', (max(w, 1), self.height))
        for y in range(self.height):
            row = self.rom[self.data_start + y*self.stride: self.data_start + (y+1)*self.stride]
            for x in range(w):
                bx = x0 + x
                if row[bx//8] >> (7 - bx % 8) & 1: img.putpixel((x, y), 255)
        return img


HOOK_ORG = 0xFEC0


def font_pages(rom):
    """Korean build: read the page table (bank, addr) written after the GSU hooks; returns Font list."""
    code = rom[HOOK_ORG:HOOK_ORG + 16]
    assert code[:2] == bytes([0x20, 0x1E]) and code[9] == 0xFE, 'not a Korean build (hook not found)'
    table = code[10] | code[11] << 8
    off = (table - 0x8000) + 0x8000           # bank 1: file offset == address
    fonts = []
    while True:
        lo, hi, bank = rom[off], rom[off + 1], rom[off + 2]
        addr = lo | hi << 8
        if addr < 0x8000 or bank > 0x3F or len(fonts) >= 16:
            break
        fo = bank * 0x8000 + addr - 0x8000
        if not (rom[fo + 1] == 12 and rom[fo + 2] == 0x21 and rom[fo + 3] == 0xFE):
            break
        fonts.append(Font(rom, fo))
        off += 3
    return fonts
