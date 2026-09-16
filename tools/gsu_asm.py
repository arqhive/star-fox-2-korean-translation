"""Tiny two-pass Super FX (GSU) assembler for hand-written patches.

Usage:
    a = Asm(org=0xFEC0)
    a.op('IBT', 0, 0x20); a.label('x'); a.br('BEQ', 'x') ...
    code = a.assemble()
"""

BR = {'BRA': 0x05, 'BGE': 0x06, 'BLT': 0x07, 'BNE': 0x08, 'BEQ': 0x09, 'BPL': 0x0A,
      'BMI': 0x0B, 'BCC': 0x0C, 'BCS': 0x0D, 'BVC': 0x0E, 'BVS': 0x0F}


class Asm:
    def __init__(self, org):
        self.org = org
        self.items = []  # (kind, data)
        self.labels = {}

    def label(self, name):
        self.items.append(('label', name))

    def raw(self, *bs):
        self.items.append(('bytes', bytes(bs)))

    # --- instructions ---
    def NOP(self): self.raw(0x01)
    def IBT(self, r, v): self.raw(0xA0 | r, v & 0xFF)
    def IWT(self, r, v):
        if isinstance(v, str): self.items.append(('iwt', (r, v)))
        else: self.raw(0xF0 | r, v & 0xFF, v >> 8)
    def LMS(self, r, a): assert a % 2 == 0 and a < 0x200; self.raw(0x3D, 0xA0 | r, a // 2)
    def SMS(self, r, a): assert a % 2 == 0 and a < 0x200; self.raw(0x3E, 0xA0 | r, a // 2)
    def LM(self, r, a): self.raw(0x3D, 0xF0 | r, a & 0xFF, a >> 8)
    def SM(self, r, a): self.raw(0x3E, 0xF0 | r, a & 0xFF, a >> 8)
    def ROMB(self): self.raw(0x3F, 0xDF)
    def GETB(self): self.raw(0xEF)
    def MOVE(self, d, s): self.raw(0x20 | s, 0x10 | d)      # Rd = Rs
    def MOVES(self, d, s): self.raw(0x20 | d, 0xB0 | s)     # Rd = Rs, set flags
    def FROM(self, r): self.raw(0xB0 | r)
    def TO(self, r): self.raw(0x10 | r)
    def WITH(self, r): self.raw(0x20 | r)
    def CMP(self, r): self.raw(0x3F, 0x60 | r)              # Sreg - Rr
    def ADDI(self, n): self.raw(0x3E, 0x50 | n)             # Dreg = Sreg + #n
    def INC(self, r): self.raw(0xD0 | r)
    def DEC(self, r): self.raw(0xE0 | r)
    def STW(self, r): self.raw(0x30 | r)
    def LDW(self, r): self.raw(0x40 | r)
    def LINK(self, n): self.raw(0x90 | n)
    def JMP(self, r): self.raw(0x90 | r)                    # r in 8..13
    def br(self, cond, target): self.items.append(('br', (BR[cond], target)))

    def assemble(self):
        for _ in range(2):
            pc = self.org
            out = bytearray()
            for kind, data in self.items:
                if kind == 'label':
                    self.labels[data] = pc
                elif kind == 'bytes':
                    out += data; pc += len(data)
                elif kind == 'br':
                    op, t = data
                    tgt = self.labels.get(t, pc + 2) if isinstance(t, str) else t
                    off = tgt - (pc + 2)
                    if not -128 <= off <= 127:
                        raise ValueError('branch out of range to %s' % t)
                    out += bytes((op, off & 0xFF)); pc += 2
                elif kind == 'iwt':
                    r, t = data
                    v = self.labels.get(t, 0)
                    out += bytes((0xF0 | r, v & 0xFF, v >> 8)); pc += 3
        return bytes(out)
