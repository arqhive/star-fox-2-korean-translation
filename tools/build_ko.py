"""Star Fox 2 (JP) Korean build script (1MB layout, same ROM size as the original).

  python tools/build_ko.py --rom "Star Fox 2 (Japan).sfc" [--out work/sf2_ko.sfc]

Pipeline
  1. Image text: decompress, draw Korean, recompress in place (blobs that grew go to free space).
  2. MISSION panel (raw 8bpp portrait sheet) patched.
  3. Korean font page 0 replaces the JP dialogue font at $0D:E1FB; pages 1..N are placed in
     bank-end padding. Text byte 0x01..0x0F = page prefix for the next byte.
  4. GSU hooks in $01:FEC0: width measure loop ($EDD8), draw loop ($EF80), 1-char draw ROMB ($EFAB),
     page lookup table (address + bank per page).
  5. Dialogue re-encoded into bank 0 (same area, same pointer table).
"""
import os, re, sys, json, argparse, collections
sys.path.insert(0, os.path.dirname(__file__))
from PIL import Image, ImageFont, ImageDraw
from sf2font import Font
from gsu_asm import Asm

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE_SHA1 = '578df9cc661548f278faa1fb4b9b2e9701bde92e'   # Star Fox 2 (Japan) (Classic Mini, Switch Online)

TEXT_TABLE = 0x2DA5; TEXT_COUNT = 216
TEXT_START = 0x1168; TEXT_END = 0x2DA5          # string area (bank 0), pointer table follows
PAGE0_OFF = 0x6E1FB                               # $0D:E1FB, original JP dialogue font
PAGE0_LIMIT = 0x6EE06 - 0x6E1FB                   # up to the next font header ($0D:EE06)
HOOK_ORG = 0xFEC0                                 # $01:FEC0 (file == address in bank 1)
HOOK_END = 0x10000
MAX_PAGES = 16                                    # prefixes 0x01..0x0F
MAGIC = 0xA55A                                    # R12 marker: hook-driven 1-char draw
GLYPH_H = 12
STRIDE_MAX = 255                                  # header byte0 is the row stride

# JP glyph codes kept as-is in page 0 (symbols, button icons, digits)
KEEP = {0x21: '!', 0x3F: '?', 0x30: '0', 0x31: '1', 0x32: '2', 0x39: '9', 0x7E: '~', 0xFE: '%',
        0x23: '[AR]', 0x24: '[BOX_L]', 0x26: '[BOX_R]', 0x28: '[B]', 0x29: '[X]', 0x2A: '[R]', 0x2B: '[L]',
        0x2C: '[▶]', 0x2E: '[!]', 0x33: '[+]', 0x38: '[A]', 0x3D: '[Y]', 0x40: '[ST]', 0x5D: '[SE]', 0x5E: '[LE]',
        0x5F: '-', 0xEB: '·'}
# new narrow glyphs rendered from the TTF, given fixed codes in page 0
NEW_FIXED = {0x34: '3', 0x35: '4', 0x36: '5', 0x37: '6', 0x3A: '7', 0x3B: '8', 0xE9: '.', 0xEA: ',',
             0x22: '\'', 0x25: '"', 0x27: '(', 0x2F: ')', 0x3C: ':'}
MACROS = {'{START}': '[ST]{11}[AR]{11}[BOX_L]', '{SELECT}': '[SE]{11}[LE]{11}[BOX_R]'}
SPACE = 0x20


def load_ko(path):
    ko = {}
    for line in open(path, encoding='utf-8'):
        line = line.rstrip('\n')
        if not line or line.startswith('#') or '|' not in line:
            continue
        i, t = line.split('|', 1)
        ko[int(i)] = t
    return ko


def tokenize(s):
    for k, v in MACROS.items():
        s = s.replace(k, v)
    toks = []
    i = 0
    while i < len(s):
        if s[i] == '[':
            j = s.index(']', i); toks.append(s[i:j+1]); i = j + 1
        elif s[i] == '{':
            j = s.index('}', i); toks.append(s[i:j+1]); i = j + 1
        else:
            toks.append(s[i]); i += 1
    return toks


DIALOG_FONT = os.environ.get('KO_DIALOG_FONT', 'Galmuri9')
FONT_CFG = {'Galmuri11': (2, 11), 'Galmuri9': (0, 9)}     # (top row cut, hangul width)


class GlyphSource:
    """Galmuri BDF cut to 12 rows."""
    def __init__(self):
        from bdf import BDF
        self.font = BDF(os.path.join(ROOT, 'fonts', DIALOG_FONT + '.bdf'))
        self.top, self.hw = FONT_CFG[DIALOG_FONT]

    def render(self, ch):
        g = self.font.glyph(ch)
        if g is None:
            raise SystemExit('glyph missing in %s: %r' % (DIALOG_FONT, ch))
        im, dw = g
        im = im.crop((0, self.top, im.width, self.top + GLYPH_H)).point(lambda v: 1 if v else 0, '1')
        if '가' <= ch <= '힣':
            return im.crop((0, 0, self.hw, GLYPH_H))
        bb = im.getbbox()
        if bb is None:
            return Image.new('1', (3, GLYPH_H), 0)
        return im.crop((bb[0], 0, bb[2], GLYPH_H))


def build_page(glyphs):
    """glyphs: dict code -> 1bit PIL image (height 12). returns bytes of font block."""
    codes = sorted(glyphs)
    order = list(codes)
    ents = []; x = 0
    for c in order:
        w = glyphs[c].width
        assert w < 32
        ents.append((x, w)); x += w
    W = x
    stride = (W + 7) // 8
    if stride > STRIDE_MAX or W > 0x7FF:
        raise ValueError('page too wide: %d px' % W)
    first, last = 0x21, 0xFE
    cmap = bytearray([0xFF] * (last - first + 1))
    for gi, c in enumerate(order):
        cmap[c - first] = gi
    table = b''.join(((w << 11) | xo).to_bytes(2, 'little') for xo, w in ents)
    data_off = 7 + len(cmap) + len(table)
    hdr = bytes([stride, GLYPH_H, first, last, 1]) + data_off.to_bytes(2, 'little')
    bmp = bytearray(stride * GLYPH_H)
    for (xo, w), c in zip(ents, order):
        img = glyphs[c]
        for yy in range(GLYPH_H):
            for xx in range(w):
                if img.getpixel((xx, yy)):
                    bx = xo + xx
                    bmp[yy * stride + bx // 8] |= 0x80 >> (bx % 8)
    return hdr + cmap + table + bmp, W


def jp_glyph(jpfont, code):
    g = jpfont.glyph_of(code)
    img = jpfont.glyph_img(g).point(lambda v: 1 if v else 0, '1')
    return img


def assemble_hooks(pages):
    """pages: list of (bank, addr) per page index (0 = JP dialogue font slot)."""
    a = Asm(HOOK_ORG)
    # ---------------- page lookup: in R0 = page; out R0 = header addr, R14 -> bank byte, ROMB = $01
    a.label('lookup')
    a.MOVE(14, 0)
    a.IBT(0, 0x01); a.ROMB()
    a.FROM(14); a.raw(0x5E)          # R0 = R14 + R14
    a.raw(0x5E)                      # R0 = R0 + R14  (3 * page)
    a.IWT(14, 'table')
    a.WITH(14); a.raw(0x50)          # R14 = table + 3 * page
    a.GETB()
    a.INC(14)
    a.raw(0x3D, 0xEF)                # GETBH: R0 = hi << 8 | lo
    a.INC(14)
    a.JMP(11); a.NOP()
    # ---------------- draw hook (from $EF80) ----------------
    # in: R0 = text byte (non-zero), R14 = ptr to next byte (saved in $B8), ROMB = text bank
    a.label('draw')
    a.IBT(12, MAX_PAGES)
    a.FROM(0); a.CMP(12)
    a.br('BCS', 'draw_plain'); a.NOP()
    a.MOVE(13, 0)                    # R13 = page
    a.GETB()                         # R0 = code
    a.INC(14)
    a.SM(14, 0x00B8)
    a.MOVE(12, 0)                    # R12 = code
    a.LMS(0, 0x02E)                  # 2-byte char: consume one extra count of the line byte counter
    a.DEC(0)
    a.raw(0x90)                      # SBK -> ($02E)
    a.LMS(0, 0x0BA)                  # push current font header
    a.STW(10); a.INC(10); a.INC(10)
    a.MOVE(0, 13)
    a.LINK(4); a.IWT(15, 'lookup'); a.NOP()
    a.SMS(0, 0x0BA)
    a.TO(13); a.GETB()               # R13 = bank of the page
    a.MOVE(0, 12)                    # R0 = code
    a.IWT(12, MAGIC)                 # tell the $EFAB stub to use R13 as font bank
    a.LINK(4); a.IWT(15, 0xEF91); a.NOP()
    a.DEC(10); a.DEC(10); a.LDW(10)  # pop header
    a.SMS(0, 0x0BA)
    a.IWT(15, 0xEF84); a.NOP()
    a.label('draw_plain')
    a.IWT(11, 0xEF84)
    a.IWT(15, 0xEF91); a.NOP()
    # ---------------- 1-char draw font bank (from $EFAB) ----------------
    a.label('efab')
    a.IWT(0, MAGIC)
    a.FROM(12); a.CMP(0)
    a.br('BNE', 'efab_def'); a.NOP()
    a.FROM(13); a.ROMB()
    a.IWT(15, 0xEFAF); a.NOP()
    a.label('efab_def')
    a.IBT(0, 0x0D); a.ROMB()
    a.IWT(15, 0xEFAF); a.NOP()
    # ---------------- measure hook (from $EDD8) ----------------
    # in: R5 = R0 = byte (non-zero), R12 = ptr to next byte, ROMB = text bank, R11 = caller return
    a.label('measure')
    a.LMS(9, 0x0BA); a.WITH(9); a.ADDI(7)      # R9 = header+7 (map of caller's font)
    a.IBT(1, MAX_PAGES)
    a.FROM(5); a.CMP(1)
    a.br('BCS', 'm_plain'); a.NOP()
    a.MOVE(14, 12); a.INC(12); a.GETB()        # R0 = code
    a.MOVE(1, 0)
    a.FROM(11); a.STW(10); a.INC(10); a.INC(10)
    a.MOVE(0, 5)
    a.LINK(4); a.IWT(15, 'lookup'); a.NOP()
    a.MOVE(9, 0); a.WITH(9); a.ADDI(7)
    a.TO(4); a.GETB()                          # R4 = bank
    a.DEC(10); a.DEC(10); a.TO(11); a.LDW(10)
    a.MOVES(5, 1)
    a.FROM(4); a.ROMB()
    a.IWT(15, 0xEDDC); a.NOP()
    a.label('m_plain')
    a.IBT(0, 0x0D); a.ROMB()
    a.IWT(15, 0xEDDC); a.NOP()
    # ---------------- page table ----------------
    a.label('table')
    for bank, addr in pages:
        a.raw(addr & 0xFF, addr >> 8, bank)
    code = a.assemble()
    return code, a.labels


def page_bytes(glyphs):
    W = sum(g.width for g in glyphs.values())
    return 7 + (0xFE - 0x21 + 1) + 2 * len(glyphs) + GLYPH_H * ((W + 7) // 8), W


def patch_portrait_text(rom, base, rect, text, fname, fg, bg, width=256, extra_clear=None):
    """8bpp sheet: replace fg pixels by bg in rect (only fg/bg pixels touched), draw text centered."""
    import gfx_ko
    x, y, w, h = rect
    if extra_clear:
        (ex, ey, ew, eh), vals = extra_clear
        for yy in range(ey, ey + eh):
            for xx in range(ex, ex + ew):
                if rom[base + yy * width + xx] in vals:
                    rom[base + yy * width + xx] = bg
    for yy in range(y, y + h):
        for xx in range(x, x + w):
            o = base + yy * width + xx
            if rom[o] == fg:
                rom[o] = bg
    lines, lh, W, H = gfx_ko.text_mask(text, fname)
    im = lines[0]
    ox = x + (w - im.width) // 2; oy = y + (h - im.height) // 2
    for yy in range(im.height):
        for xx in range(im.width):
            if im.getpixel((xx, yy)):
                o = base + (oy + yy) * width + ox + xx
                if rom[o] == bg:
                    rom[o] = fg


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--rom', required=True, help='original Japanese ROM (headerless, 1MB)')
    ap.add_argument('--out', default=os.path.join(ROOT, 'work', 'sf2_ko.sfc'))
    ap.add_argument('--ko', default=os.path.join(ROOT, 'translation', 'ko.txt'))
    args = ap.parse_args()

    rom = bytearray(open(args.rom, 'rb').read())
    if len(rom) == 0x100200:        # copier header
        rom = rom[0x200:]
    import hashlib
    if hashlib.sha1(rom).hexdigest() != SOURCE_SHA1:
        raise SystemExit('source ROM SHA1 mismatch (need Star Fox 2 (Japan) Classic Mini dump, headerless)')
    jpfont = Font(bytes(rom), 0x6E1FB)
    from export_jp import read_script
    jp = read_script(bytes(rom), with_text=False)
    ko = load_ko(args.ko)

    # ---- collect characters ----
    rev_keep = {v: k for k, v in KEEP.items()}
    rev_new = {v: k for k, v in NEW_FIXED.items()}
    freq = collections.Counter()
    ko_toks = {}
    for e in jp:
        t = ko.get(e['id'], '=')
        if t == '=':
            continue
        toks = tokenize(t)
        ko_toks[e['id']] = toks
        for tk in toks:
            if tk == ' ' or tk in rev_keep or tk in rev_new or tk.startswith('{'):
                continue
            freq[tk] += 1
    unknown = [c for c in freq if not ('가' <= c <= '힣') and len(c) == 1 and c not in '·']
    if unknown:
        print('WARNING: characters without fixed code (will be given hangul slots):', ''.join(unknown))
    ordered = [c for c, _ in freq.most_common()]

    # ---- image text first (freed blob heads join the free-space pool) ----
    import gfx_ko
    from freespace import bank_end_padding, cpu_addr
    pool = bank_end_padding(rom, skip_banks=(1,))
    for name, room, size in gfx_ko.patch_rom(rom, os.path.join(ROOT, 'work', 'gfx_preview'), pool=pool):
        print('gfx %s: %d / %d bytes' % (name, size, room))

    # ---- raw 8bpp portrait sheet (bank $14, 256 wide): MISSION panel ----
    patch_portrait_text(rom, 0xA0000, (226, 100, 28, 13), '\uC124\uBA85', 'g9', fg=0x9E, bg=0x96,
                        extra_clear=((232, 101, 20, 11), (0x56, 0x5E, 0x66)))

    # ---- font pages: page 0 in the JP font slot, others in free space ----
    src = GlyphSource()
    charcode = {}                     # char -> bytes
    page0 = {}
    for code, name in KEEP.items():
        page0[code] = jp_glyph(jpfont, code)
        charcode[name] = bytes([code])
    for code, ch in NEW_FIXED.items():
        page0[code] = src.render(ch)
        charcode[ch] = bytes([code])
    pages = [[0x0D, 0xE1FB, page0, PAGE0_OFF, PAGE0_LIMIT]]      # bank, addr, glyphs, file offset, room
    for ch in ordered:
        img = src.render(ch)
        while True:
            bank, addr, glyphs, off, room = pages[-1]
            codes = [c for c in range(0x21, 0xFF) if c not in glyphs]
            if codes:
                trial = dict(glyphs); trial[codes[0]] = img
                size, W = page_bytes(trial)
                if size <= room and W <= 255 * 8:
                    glyphs[codes[0]] = img
                    pi = len(pages) - 1
                    charcode[ch] = bytes([codes[0]]) if pi == 0 else bytes([pi, codes[0]])
                    break
            if len(pages) >= MAX_PAGES:
                raise SystemExit('too many font pages')
            off, room = pool.take_largest()
            bank, addr = cpu_addr(off)
            pages.append([bank, addr, {}, off, room])

    report = []
    for pi, (bank, addr, glyphs, off, room) in enumerate(pages):
        blk, W = build_page(glyphs)
        assert len(blk) <= room
        if pi:
            assert all(b == 0xFF for b in rom[off:off + len(blk)]), 'page %d area not free' % pi
        rom[off:off + len(blk)] = blk
        report.append('p%d %02X:%04X %dch %d/%dB' % (pi, bank, addr, len(glyphs), len(blk), room))
    print('font pages:', '; '.join(report))

    # ---- encode strings ----
    strings = []
    for e in jp:
        raw = bytes.fromhex(e['raw'])
        if e['id'] in ko_toks:
            body = bytearray()
            for tk in ko_toks[e['id']]:
                if tk == ' ':
                    body.append(SPACE)
                elif tk.startswith('{'):
                    body.append(int(tk[1:-1], 16))
                else:
                    body += charcode[tk]
            raw = bytes(body)
        strings.append(bytes([e['speaker'], e['face']]) + raw + b'\x00')
    pos = TEXT_START
    ptrs = []
    for s in strings:
        ptrs.append(pos)
        rom[pos:pos + len(s)] = s
        pos += len(s)
    if pos > TEXT_END:
        raise SystemExit('text overflow: %d bytes over' % (pos - TEXT_END))
    for i in range(pos, TEXT_END):
        rom[i] = 0xFF
    for i, p in enumerate(ptrs):
        rom[TEXT_TABLE + 2 * i:TEXT_TABLE + 2 * i + 2] = (p + 0x8000).to_bytes(2, 'little')
    print('text bytes %d / %d' % (pos - TEXT_START, TEXT_END - TEXT_START))

    # ---- GSU patches ----
    code, labels = assemble_hooks([(p[0], p[1]) for p in pages])
    assert all(b == 0xFF for b in rom[HOOK_ORG:HOOK_ORG + len(code)]), 'hook area not free'
    assert HOOK_ORG + len(code) <= HOOK_END, 'hook code too large (%d bytes)' % len(code)
    rom[HOOK_ORG:HOOK_ORG + len(code)] = code
    print('hook code %d bytes at $01:%04X (free %d)' % (len(code), HOOK_ORG, HOOK_END - HOOK_ORG - len(code)))

    def patch(off, old, new):
        assert rom[off:off + len(old)] == old, 'mismatch at %X: %s' % (off, rom[off:off+len(old)].hex())
        rom[off:off + len(new)] = new
    jmp = lambda lab: bytes([0xFF, labels[lab] & 0xFF, labels[lab] >> 8, 0x01])
    patch(0xEDD8, bytes.fromhex('a00d3fdf'), jmp('measure'))
    patch(0xEF80, bytes.fromhex('93050e01'), jmp('draw'))
    patch(0xEFAB, bytes.fromhex('a00d3fdf'), jmp('efab'))
    # comm / cut-scene text box line width 112 -> 108 px: hangul and '.' are inked to the glyph edge,
    # so full 112 px lines touched the box border
    patch(0x54FF4, bytes.fromhex('a970008fca0070'), bytes.fromhex('a96c008fca0070'))

    # ---- checksum ----
    rom[0x7FDC:0x7FE0] = b'\xFF\xFF\x00\x00'
    s = sum(rom) & 0xFFFF
    rom[0x7FDC:0x7FDE] = (s ^ 0xFFFF).to_bytes(2, 'little')
    rom[0x7FDE:0x7FE0] = s.to_bytes(2, 'little')

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    open(args.out, 'wb').write(rom)
    os.makedirs(os.path.join(ROOT, 'work'), exist_ok=True)
    json.dump({k: v.hex() for k, v in charcode.items()}, open(os.path.join(ROOT, 'work', 'ko_charmap.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    print('wrote', args.out)


if __name__ == '__main__':
    main()
