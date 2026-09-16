"""Free-space pool for the 1MB layout (regions never read by the original game)."""
import re

LOROM_BANK = 0x8000


class Pool:
    def __init__(self):
        self.regions = []   # [file_offset, size]

    def add(self, off, size):
        if size > 0:
            self.regions.append([off, size])

    def total(self):
        return sum(s for _, s in self.regions)

    def largest(self):
        return max((s for _, s in self.regions), default=0)

    def alloc(self, size, rom=None):
        """best fit; returns file offset"""
        cands = [r for r in self.regions if r[1] >= size]
        if not cands:
            raise SystemExit('free space exhausted (need %d bytes, largest %d)' % (size, self.largest()))
        r = min(cands, key=lambda r: r[1])
        off = r[0]
        if rom is not None:
            assert all(b == 0xFF for b in rom[off:off + size]), 'region %X not free' % off
        r[0] += size; r[1] -= size
        if r[1] == 0:
            self.regions.remove(r)
        return off

    def take_largest(self):
        r = max(self.regions, key=lambda r: r[1])
        self.regions.remove(r)
        return r[0], r[1]


def bank_end_padding(rom, min_len=128, skip_banks=()):
    """0xFF runs that reach the end of a LoROM bank (or the internal header at 0x7FB0)."""
    pool = Pool()
    for m in re.finditer(rb'\xff{%d,}' % min_len, bytes(rom)):
        s = m.start()
        bank = s // LOROM_BANK
        e = min(m.end(), (bank + 1) * LOROM_BANK)
        if bank in skip_banks or e - s < min_len:
            continue
        if e % LOROM_BANK == 0 or e == 0x7FB0:
            pool.add(s, e - s)
    return pool


def cpu_addr(off):
    return off // LOROM_BANK, 0x8000 + off % LOROM_BANK
