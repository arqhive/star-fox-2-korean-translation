"""Star Fox 2 GSU LZ codec (pure Python, reverse-engineered from GSU routine $01:D9FF).

Stream layout (a blob occupies [start, end) in one ROM bank, read backwards from end):
  end-1,end-2 : output size (lo, hi)      end-3,end-4 : 00 00
  end-5..end-8: first bit word  R3 = b[-5] | b[-6]<<8 ; R2 = b[-7] | b[-8]<<8 ; word = R2<<16|R3
                (contains its own sentinel bit above the data bits)
  then 32-bit words going backwards, same byte order, all 32 bits are data.
Bits are taken LSB-first from each word; multi-bit values are MSB-first.
Output is written backwards from dst+size down to dst.

Token loop:
  n = bits(3); 7 -> bit? (bits(10) or, if 0, bits(18)) : bits(4)+7
  n literals (8 bits each)
  if output full: stop
  match: c = bits(2)
    0: len 2, dist bits(8)
    1: len 3, dist = bit ? bits(8) : bits(14)
    2: len 4, dist = D
    3: c2 = bits(2); 0/1 -> len c2+5; 2 -> len bits(2)+7; 3 -> len bits(8); dist = D
    D = bit==0 ? bits(16) : (bit ? bits(8) : bits(12))
  copy: out[p] = out[p + dist] (p decreasing)
"""


class BitReader:
    def __init__(self, blk, pos, w):
        self.b = blk; self.pos = pos; self.w = w  # w: current shift register (32-bit)

    def bit(self):
        c = self.w & 1
        self.w >>= 1
        if self.w == 0:
            p = self.pos
            r3 = self.b[p - 1] | self.b[p - 2] << 8
            r2 = self.b[p - 3] | self.b[p - 4] << 8
            self.pos = p - 4
            word = r2 << 16 | r3
            c = word & 1
            self.w = (word >> 1) | 0x80000000
        return c

    def bits(self, n):
        v = 0
        for _ in range(n):
            v = (v << 1) | self.bit()
        return v


def decompress(buf, end):
    """buf: bytes addressable so that buf[end-1] is the last byte of the blob. returns (data, start)."""
    size = buf[end - 1] | buf[end - 2] << 8
    r3 = buf[end - 5] | buf[end - 6] << 8
    r2 = buf[end - 7] | buf[end - 8] << 8
    br = BitReader(buf, end - 8, r2 << 16 | r3)
    out = bytearray(size)
    p = size
    while True:
        n = br.bits(3)
        if n == 7:
            if br.bit():
                n = br.bits(10)
                if n == 0:
                    n = br.bits(18) & 0xFFFF
            else:
                n = br.bits(4) + 7
        for _ in range(n):
            p -= 1; out[p] = br.bits(8)
        if p == 0:
            break
        c = br.bits(2)
        if c == 0:
            ln = 2; dist = br.bits(8)
        elif c == 1:
            ln = 3; dist = br.bits(8) if br.bit() else br.bits(14)
        else:
            if c == 2:
                ln = 4
            else:
                c2 = br.bits(2)
                ln = c2 + 5 if c2 < 2 else (br.bits(2) + 7 if c2 == 2 else br.bits(8))
            if br.bit() == 0:
                dist = br.bits(16)
            else:
                dist = br.bits(8) if br.bit() else br.bits(12)
        for _ in range(ln):
            p -= 1; out[p] = out[p + dist]
    return bytes(out), br.pos


class BitWriter:
    def __init__(self):
        self.bits = []

    def put(self, v, n):
        for i in range(n - 1, -1, -1):
            self.bits.append((v >> i) & 1)


def _lit_count(bw, n):
    if n < 7:
        bw.put(n, 3)
    elif n <= 22:
        bw.put(7, 3); bw.put(0, 1); bw.put(n - 7, 4)
    elif n <= 1023:
        bw.put(7, 3); bw.put(1, 1); bw.put(n, 10)
    else:
        bw.put(7, 3); bw.put(1, 1); bw.put(0, 10); bw.put(n, 18)


def _dist_long(bw, d):
    if d < 256:
        bw.put(1, 1); bw.put(1, 1); bw.put(d, 8)
    elif d < 4096:
        bw.put(1, 1); bw.put(0, 1); bw.put(d, 12)
    else:
        bw.put(0, 1); bw.put(d, 16)


def _match_cost(ln, d):
    if ln == 2: return 2 + 8 if d < 256 else None
    if ln == 3:
        if d < 256: return 2 + 1 + 8
        if d < 16384: return 2 + 1 + 14
        return None
    dc = 2 + 8 if d < 256 else 2 + 12 if d < 4096 else 1 + 16
    if ln == 4: return 2 + dc
    if ln <= 6: return 4 + dc
    if ln <= 10: return 6 + dc
    if ln <= 255: return 12 + dc
    return None


def compress(data):
    """Returns the blob bytes (to be placed so that it ENDS at the chosen end address)."""
    size = len(data)
    assert 0 < size <= 0xFFFF
    # work on reversed stream: output is produced from the end towards the start.
    # position q counts produced bytes; produced byte k is data[size-1-k]; match copies from data[idx+dist].
    rev = data[::-1]
    N = size
    # hash chains over rev for candidates: match at q means rev[q:q+ln] == rev[q-dist:q-dist+ln]
    from collections import defaultdict
    heads = defaultdict(list)
    MAXD = 0xFFFF
    tokens = []  # ('L', start, count) / ('M', ln, dist)
    q = 0; lit_start = 0
    bw_tokens = []

    def best_match(q):
        if q + 2 > N: return 0, 0
        key = bytes(rev[q:q + 2])
        best = (0, 0)
        cands = heads.get(key, [])
        for j in reversed(cands[-512:]):
            d = q - j
            if d > MAXD: break
            ln = 2
            lim = min(255, N - q)
            while ln < lim and rev[j + ln] == rev[q + ln]:
                ln += 1
            if ln > best[0] and _match_cost(ln, d) is not None:
                best = (ln, d)
                if ln == lim: break
        return best

    def insert(i):
        if i + 2 <= N:
            heads[bytes(rev[i:i + 2])].append(i)

    while q < N:
        ln, d = best_match(q)
        use = False
        if ln >= 2:
            cost = _match_cost(ln, d)
            use = cost < ln * 9
            # lazy: prefer next position if much better
            if use and q + 1 < N:
                insert(q)
                ln2, d2 = best_match(q + 1)
                if ln2 > ln + 1:
                    use = False
                heads[bytes(rev[q:q + 2])].pop() if q + 2 <= N else None
        if use:
            tokens.append(('L', lit_start, q - lit_start))
            tokens.append(('M', ln, d))
            for i in range(q, q + ln): insert(i)
            q += ln; lit_start = q
        else:
            insert(q); q += 1
    tokens.append(('L', lit_start, q - lit_start))

    bw = BitWriter()
    for t in tokens:
        if t[0] == 'L':
            n = t[2]; s = t[1]
            # split long literal runs: run(1023) + zero-length match impossible, so use chunks joined by a len-2 match? avoid: cap
            _lit_count(bw, n)
            for k in range(n):
                bw.put(rev[s + k], 8)
        else:
            _, ln, d = t
            if ln == 2:
                bw.put(0, 2); bw.put(d, 8)
            elif ln == 3:
                bw.put(1, 2)
                if d < 256: bw.put(1, 1); bw.put(d, 8)
                else: bw.put(0, 1); bw.put(d, 14)
            else:
                if ln == 4:
                    bw.put(2, 2)
                elif ln <= 6:
                    bw.put(3, 2); bw.put(ln - 5, 2)
                elif ln <= 10:
                    bw.put(3, 2); bw.put(2, 2); bw.put(ln - 7, 2)
                else:
                    bw.put(3, 2); bw.put(3, 2); bw.put(ln, 8)
                _dist_long(bw, d)
    bits = bw.bits
    # first word: up to 31 bits + sentinel
    k = min(31, len(bits))
    first = 1 << k
    for i in range(k): first |= bits[i] << i
    words = []
    i = k
    while i < len(bits):
        w = 0
        for j in range(32):
            if i + j < len(bits): w |= bits[i + j] << j
        words.append(w); i += 32
    # layout backwards: end-1 size lo, end-2 size hi, end-3/4 = 0, then first word, then words
    out = bytearray()
    def word_bytes(w):
        r3 = w & 0xFFFF; r2 = w >> 16
        # positions (backwards) p-1: r3 lo, p-2: r3 hi, p-3: r2 lo, p-4: r2 hi  -> forward order: r2hi r2lo r3hi r3lo
        return bytes([r2 >> 8, r2 & 0xFF, r3 >> 8, r3 & 0xFF])
    for w in reversed(words):
        out += word_bytes(w)
    out += word_bytes(first)
    out += bytes([0, 0, size >> 8, size & 0xFF])
    return bytes(out)
