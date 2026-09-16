"""Small Super FX (GSU-2) interpreter, pipeline-accurate enough to run ROM subroutines
(decompressor etc.) offline. Plot/cache/colour ops are no-ops.

    cpu = GSU(rom_bytes)
    cpu.ram[...] = ...
    cpu.call(0x01, 0xD9FF)   # runs until STOP
"""


class GSU:
    def __init__(self, rom):
        self.rom = rom
        self.ram = bytearray(0x20000)       # $70:0000-$71:FFFF
        self.r = [0] * 16
        self.pbr = 0; self.romb = 0; self.ramb = 0
        self.z = self.cy = self.s = self.ov = False
        self.alt = 0; self.b = False
        self.sreg = self.dreg = 0
        self.pipeline = 0
        self.r15mod = False
        self.lastram = 0
        self.steps = 0

    # ---- memory ----
    def rd(self, bank, addr):
        bank &= 0x7F
        if bank < 0x40:
            if addr >= 0x8000:
                return self.rom[((bank & 0x3F) * 0x8000 + (addr & 0x7FFF)) % len(self.rom)]
            return self.rom[((bank & 0x3F) * 0x8000 + addr) % len(self.rom)]
        if bank < 0x60:
            return self.rom[((bank - 0x40) * 0x10000 + addr) % len(self.rom)]
        if bank in (0x70, 0x71):
            return self.ram[(bank - 0x70) * 0x10000 + addr]
        raise ValueError('read %02X:%04X' % (bank, addr))

    def ramrd(self, a):
        a &= 0xFFFF; self.lastram = a
        return self.ram[self.ramb * 0x10000 + a]

    def ramwr(self, a, v):
        a &= 0xFFFF; self.lastram = a
        self.ram[self.ramb * 0x10000 + a] = v & 0xFF

    def ramrdw(self, a): return self.ramrd(a) | (self.ramrd(a + 1) << 8)
    def ramwrw(self, a, v): self.ramwr(a, v); self.ramwr(a + 1, v >> 8); self.lastram = a & 0xFFFF

    def fetch(self):
        return self.rd(self.pbr, self.r[15])

    def pipe(self):
        res = self.pipeline
        self.r[15] = (self.r[15] + 1) & 0xFFFF
        self.pipeline = self.fetch()
        self.r15mod = False
        return res

    def setr(self, n, v):
        self.r[n] = v & 0xFFFF
        if n == 15: self.r15mod = True

    def flags_sz(self, v):
        self.s = bool(v & 0x8000); self.z = (v & 0xFFFF) == 0

    # ---- run ----
    def call(self, bank, addr, max_steps=5_000_000):
        self.pbr = bank
        self.r[15] = addr
        self.pipeline = self.fetch()
        self.r[15] = (addr + 1) & 0xFFFF
        self.running = True
        while self.running:
            op = self.pipeline
            self.pipeline = self.fetch()
            self.r15mod = False
            self.exec(op)
            if not self.r15mod:
                self.r[15] = (self.r[15] + 1) & 0xFFFF
            else:
                self.r15mod = False
            self.steps += 1
            if self.steps > max_steps:
                raise RuntimeError('step limit')

    def reset_prefix(self):
        self.alt = 0; self.b = False; self.sreg = self.dreg = 0

    def exec(self, op):
        hi, n = op >> 4, op & 15
        R = self.r
        alt = self.alt
        if op == 0x00:  # STOP
            self.running = False; self.reset_prefix(); return
        if op == 0x01 or op == 0x02:  # NOP / CACHE
            self.reset_prefix(); return
        if op == 0x03:  # LSR
            v = R[self.sreg]; self.cy = bool(v & 1); v >>= 1
            self.setr(self.dreg, v); self.flags_sz(v); self.reset_prefix(); return
        if op == 0x04:  # ROL
            v = R[self.sreg]; c = self.cy; self.cy = bool(v & 0x8000); v = ((v << 1) | int(c)) & 0xFFFF
            self.setr(self.dreg, v); self.flags_sz(v); self.reset_prefix(); return
        if 0x05 <= op <= 0x0F:
            e = self.pipe(); e = e - 256 if e > 127 else e
            cond = {5: True, 6: (self.s == self.ov), 7: (self.s != self.ov), 8: not self.z, 9: self.z,
                    10: not self.s, 11: self.s, 12: not self.cy, 13: self.cy, 14: not self.ov, 15: self.ov}[op]
            if cond:
                self.setr(15, R[15] + e)
            return  # prefixes untouched by branches
        if hi == 1:  # TO
            if self.b: v = R[self.sreg]; self.setr(n, v); self.reset_prefix()
            else: self.dreg = n
            return
        if hi == 2:  # WITH
            self.sreg = self.dreg = n; self.b = True; return
        if hi == 3:
            if n <= 11:
                if alt & 1: self.ramwr(R[n], R[self.sreg])
                else: self.ramwrw(R[n], R[self.sreg])
                self.reset_prefix(); return
            if n == 12:  # LOOP
                R[12] = (R[12] - 1) & 0xFFFF; self.flags_sz(R[12])
                if not self.z: self.setr(15, R[13])
                self.reset_prefix(); return
            self.alt = {13: 1, 14: 2, 15: 3}[n]; return
        if hi == 4:
            if n <= 11:
                v = self.ramrd(R[n]) if alt & 1 else self.ramrdw(R[n])
                self.setr(self.dreg, v); self.reset_prefix(); return
            if n == 12 or n == 14:  # PLOT/RPIX, COLOR/CMODE
                if n == 12 and alt & 1: self.flags_sz(0); self.setr(self.dreg, 0)
                self.reset_prefix(); return
            if n == 13:  # SWAP
                v = R[self.sreg]; v = ((v >> 8) | (v << 8)) & 0xFFFF; self.setr(self.dreg, v); self.flags_sz(v); self.reset_prefix(); return
            v = (~R[self.sreg]) & 0xFFFF; self.setr(self.dreg, v); self.flags_sz(v); self.reset_prefix(); return
        if hi == 5:
            a = R[self.sreg]; b = n if alt & 2 else R[n]; c = int(self.cy) if alt & 1 else 0
            res = a + b + c
            self.ov = bool(~(a ^ b) & (a ^ res) & 0x8000); self.cy = res > 0xFFFF
            res &= 0xFFFF; self.flags_sz(res); self.setr(self.dreg, res); self.reset_prefix(); return
        if hi == 6:
            a = R[self.sreg]; b = n if alt == 2 else R[n]
            c = 1 - int(self.cy) if alt == 1 else 0
            res = a - b - c
            self.ov = bool((a ^ b) & (a ^ res) & 0x8000); self.cy = res >= 0
            res &= 0xFFFF; self.flags_sz(res)
            if alt != 3: self.setr(self.dreg, res)
            self.reset_prefix(); return
        if hi == 7:
            if n == 0:  # MERGE
                v = (R[7] & 0xFF00) | (R[8] >> 8)
                self.setr(self.dreg, v); self.reset_prefix(); return
            b = n if alt & 2 else R[n]
            v = R[self.sreg] & (~b & 0xFFFF) if alt & 1 else R[self.sreg] & b
            self.setr(self.dreg, v); self.flags_sz(v); self.reset_prefix(); return
        if hi == 8:
            b = n if alt & 2 else R[n]
            if alt & 1: v = (R[self.sreg] & 0xFF) * (b & 0xFF)
            else:
                x = R[self.sreg] & 0xFF; x = x - 256 if x > 127 else x
                y = b & 0xFF; y = y - 256 if y > 127 else y
                v = (x * y) & 0xFFFF
            self.setr(self.dreg, v); self.flags_sz(v); self.reset_prefix(); return
        if hi == 9:
            if n == 0:  # SBK
                self.ramwrw(self.lastram, R[self.sreg]); self.reset_prefix(); return
            if 1 <= n <= 4:
                R[11] = (R[15] + n) & 0xFFFF; self.reset_prefix(); return
            if n == 5:
                v = R[self.sreg] & 0xFF; v = v | 0xFF00 if v & 0x80 else v
                self.setr(self.dreg, v); self.flags_sz(v); self.reset_prefix(); return
            if n == 6:  # ASR / DIV2
                v = R[self.sreg]; self.cy = bool(v & 1)
                v = ((v >> 1) | (v & 0x8000)) & 0xFFFF
                if alt & 1 and R[self.sreg] == 0xFFFF: v = 0
                self.setr(self.dreg, v); self.flags_sz(v); self.reset_prefix(); return
            if n == 7:  # ROR
                v = R[self.sreg]; c = self.cy; self.cy = bool(v & 1); v = (v >> 1) | (0x8000 if c else 0)
                self.setr(self.dreg, v); self.flags_sz(v); self.reset_prefix(); return
            if 8 <= n <= 13:
                if alt & 1:  # LJMP
                    self.pbr = R[n] & 0x7F; self.setr(15, R[self.sreg])
                else:
                    self.setr(15, R[n])
                self.reset_prefix(); return
            if n == 14:  # LOB
                v = R[self.sreg] & 0xFF; self.setr(self.dreg, v); self.s = bool(v & 0x80); self.z = v == 0
                self.reset_prefix(); return
            # FMULT / LMULT
            x = R[self.sreg]; x = x - 0x10000 if x & 0x8000 else x
            y = R[6]; y = y - 0x10000 if y & 0x8000 else y
            p = (x * y) & 0xFFFFFFFF
            if alt & 1: R[4] = p & 0xFFFF
            v = p >> 16
            self.setr(self.dreg, v); self.cy = bool(p & 0x8000); self.flags_sz(v); self.reset_prefix(); return
        if hi == 0xA:
            b = self.pipe()
            if alt == 0: self.setr(n, b | 0xFF00 if b & 0x80 else b)
            elif alt == 1: self.setr(n, self.ramrdw(b * 2))
            else: self.ramwrw(b * 2, R[n])
            self.reset_prefix(); return
        if hi == 0xB:  # FROM
            if self.b:
                v = R[n]; self.setr(self.dreg, v); self.ov = bool(v & 0x80); self.flags_sz(v); self.reset_prefix()
            else:
                self.sreg = n
            return
        if hi == 0xC:
            if n == 0:  # HIB
                v = R[self.sreg] >> 8; self.setr(self.dreg, v); self.s = bool(v & 0x80); self.z = v == 0
                self.reset_prefix(); return
            b = n if alt & 2 else R[n]
            v = R[self.sreg] ^ b if alt & 1 else R[self.sreg] | b
            self.setr(self.dreg, v); self.flags_sz(v); self.reset_prefix(); return
        if hi == 0xD:
            if n < 15:
                v = (R[n] + 1) & 0xFFFF; self.setr(n, v); self.flags_sz(v); self.reset_prefix(); return
            if alt == 2: self.ramb = R[self.sreg] & 1
            elif alt == 3: self.romb = R[self.sreg] & 0x7F
            self.reset_prefix(); return
        if hi == 0xE:
            if n < 15:
                v = (R[n] - 1) & 0xFFFF; self.setr(n, v); self.flags_sz(v); self.reset_prefix(); return
            buf = self.rd(self.romb, R[14])
            if alt == 0: v = buf
            elif alt == 1: v = (buf << 8) | (R[self.sreg] & 0xFF)
            elif alt == 2: v = (R[self.sreg] & 0xFF00) | buf
            else: v = buf | 0xFF00 if buf & 0x80 else buf
            self.setr(self.dreg, v); self.reset_prefix(); return
        # 0xF
        lo = self.pipe(); hi8 = self.pipe(); w = lo | (hi8 << 8)
        if alt == 0: self.setr(n, w)
        elif alt == 1: self.setr(n, self.ramrdw(w))
        else: self.ramwrw(w, R[n])
        self.reset_prefix()
