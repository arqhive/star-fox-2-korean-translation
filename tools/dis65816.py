"""Minimal 65816 disassembler (tracks M/X via REP/SEP linearly).

  python tools/dis65816.py rom.sfc BANK ADDR COUNT [m:8|16] [x:8|16]
"""
import sys

M = 'imm_m'; X = 'imm_x'
T = {}
for i, n in enumerate("ORA AND EOR ADC STA LDA CMP SBC".split()):
    b = i * 0x20
    for off, mode in ((0x01, 'dpxi'), (0x03, 'sr'), (0x05, 'dp'), (0x07, 'dpil'), (0x09, M), (0x0D, 'abs'),
                      (0x0F, 'long'), (0x11, 'dpiy'), (0x12, 'dpi'), (0x13, 'sriy'), (0x15, 'dpx'),
                      (0x17, 'dpily'), (0x19, 'absy'), (0x1D, 'absx'), (0x1F, 'longx')):
        if n == 'STA' and off == 0x09:
            continue
        T[b + off] = (n, mode)
EXTRA = """00 BRK imm8|02 COP imm8|04 TSB dp|06 ASL dp|08 PHP -|0A ASL -|0B PHD -|0C TSB abs|0E ASL abs|
10 BPL rel|14 TRB dp|16 ASL dpx|18 CLC -|1A INC -|1B TCS -|1C TRB abs|1E ASL absx|
20 JSR abs|22 JSL long|24 BIT dp|26 ROL dp|28 PLP -|2A ROL -|2B PLD -|2C BIT abs|2E ROL abs|
30 BMI rel|34 BIT dpx|36 ROL dpx|38 SEC -|3A DEC -|3B TSC -|3C BIT absx|3E ROL absx|
40 RTI -|42 WDM imm8|44 MVP mv|46 LSR dp|48 PHA -|4A LSR -|4B PHK -|4C JMP abs|4E LSR abs|
50 BVC rel|54 MVN mv|56 LSR dpx|58 CLI -|5A PHY -|5B TCD -|5C JML long|5E LSR absx|
60 RTS -|62 PER rell|64 STZ dp|66 ROR dp|68 PLA -|6A ROR -|6B RTL -|6C JMP absi|6E ROR abs|
70 BVS rel|74 STZ dpx|76 ROR dpx|78 SEI -|7A PLY -|7B TDC -|7C JMP absxi|7E ROR absx|
80 BRA rel|82 BRL rell|84 STY dp|86 STX dp|88 DEY -|89 BIT imm_m|8A TXA -|8B PHB -|8C STY abs|8E STX abs|
90 BCC rel|94 STY dpx|96 STX dpy|98 TYA -|9A TXS -|9B TXY -|9C STZ abs|9E STZ absx|
A0 LDY imm_x|A2 LDX imm_x|A4 LDY dp|A6 LDX dp|A8 TAY -|AA TAX -|AB PLB -|AC LDY abs|AE LDX abs|
B0 BCS rel|B4 LDY dpx|B6 LDX dpy|B8 CLV -|BA TSX -|BB TYX -|BC LDY absx|BE LDX absy|
C0 CPY imm_x|C2 REP imm8|C4 CPY dp|C6 DEC dp|C8 INY -|CA DEX -|CB WAI -|CC CPY abs|CE DEC abs|
D0 BNE rel|D4 PEI dpi|D6 DEC dpx|D8 CLD -|DA PHX -|DB STP -|DC JML absil|DE DEC absx|
E0 CPX imm_x|E2 SEP imm8|E4 CPX dp|E6 INC dp|E8 INX -|EA NOP -|EB XBA -|EC CPX abs|EE INC abs|
F0 BEQ rel|F4 PEA abs|F6 INC dpx|F8 SED -|FA PLX -|FB XCE -|FC JSR absxi|FE INC absx"""
for item in EXTRA.replace('\n', '').split('|'):
    c, mn, mode = item.split()
    T[int(c, 16)] = (mn, '' if mode == '-' else mode)

FMT = {'imm8': '#$%02X', 'dp': '$%02X', 'dpx': '$%02X,x', 'dpy': '$%02X,y', 'dpi': '($%02X)', 'dpxi': '($%02X,x)',
       'dpiy': '($%02X),y', 'dpil': '[$%02X]', 'dpily': '[$%02X],y', 'sr': '$%02X,s', 'sriy': '($%02X,s),y',
       'abs': '$%04X', 'absx': '$%04X,x', 'absy': '$%04X,y', 'absi': '($%04X)', 'absxi': '($%04X,x)',
       'absil': '[$%04X]', 'long': '$%06X', 'longx': '$%06X,x'}
SZ = {'': 0, 'imm8': 1, 'dp': 1, 'dpx': 1, 'dpy': 1, 'dpi': 1, 'dpxi': 1, 'dpiy': 1, 'dpil': 1, 'dpily': 1, 'sr': 1,
      'sriy': 1, 'rel': 1, 'abs': 2, 'absx': 2, 'absy': 2, 'absi': 2, 'absxi': 2, 'absil': 2, 'rell': 2, 'mv': 2,
      'long': 3, 'longx': 3}


def dis(d, off, pc, n, m16=True, x16=True):
    out = []
    for _ in range(n):
        o = d[off]; mn, mode = T[o]
        sz = (2 if m16 else 1) if mode == M else (2 if x16 else 1) if mode == X else SZ[mode]
        arg = int.from_bytes(d[off + 1:off + 1 + sz], 'little')
        if mode in (M, X): s = ('#$%04X' if sz == 2 else '#$%02X') % arg
        elif mode == 'rel': s = '$%04X' % ((pc + 2 + (arg - 256 if arg > 127 else arg)) & 0xFFFF)
        elif mode == 'rell': s = '$%04X' % ((pc + 3 + (arg - 65536 if arg > 32767 else arg)) & 0xFFFF)
        elif mode == 'mv': s = '$%02X,$%02X' % (arg & 0xFF, arg >> 8)
        else: s = FMT[mode] % arg if mode else ''
        if mn == 'REP':
            if arg & 0x20: m16 = True
            if arg & 0x10: x16 = True
        if mn == 'SEP':
            if arg & 0x20: m16 = False
            if arg & 0x10: x16 = False
        out.append('%04X  %-12s %s %s' % (pc, d[off:off + 1 + sz].hex(' '), mn, s))
        off += 1 + sz; pc += 1 + sz
    return out


if __name__ == '__main__':
    d = open(sys.argv[1], 'rb').read()
    bank = int(sys.argv[2], 16); addr = int(sys.argv[3], 16); n = int(sys.argv[4])
    m = sys.argv[5] != '8' if len(sys.argv) > 5 else True
    x = sys.argv[6] != '8' if len(sys.argv) > 6 else True
    off = (bank & 0x3F) * 0x8000 + addr - 0x8000
    print('\n'.join(dis(d, off, addr, n, m, x)))
