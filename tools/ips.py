"""Minimal IPS patch creator / applier (RLE-less; supports file growth up to 16MB).

Usage: python ips.py create source target patch.ips
       python ips.py apply  source patch.ips output
"""
import sys

def create(src, dst):
    out = bytearray(b'PATCH')
    n = len(dst); i = 0
    while i < n:
        if i < len(src) and src[i] == dst[i]:
            i += 1; continue
        j = i
        # extend run while differing (or beyond source); allow short equal gaps (<6) inside a run
        while j < n and j - i < 0xFFFF:
            if j < len(src) and src[j] == dst[j]:
                k = j
                while k < n and k < len(src) and src[k] == dst[k] and k - j < 6: k += 1
                if k - j >= 6 or k >= n: break
                j = k
            else:
                j += 1
        if i == 0x454F46:   # offset spelling "EOF" is reserved: start one byte earlier
            i -= 1
        k = i
        while k < j:     # emit, using RLE records for runs of >= 9 identical bytes
            r = k
            while r < j and dst[r] == dst[k] and r - k < 0xFFFF: r += 1
            if r - k >= 9:
                out += k.to_bytes(3, 'big') + bytes(2) + (r - k).to_bytes(2, 'big') + dst[k:k + 1]
                k = r
            else:
                e = k
                while e < j:
                    rr = e
                    while rr < j and dst[rr] == dst[e] and rr - e < 9: rr += 1
                    if rr - e >= 9: break
                    e = rr
                if e == k: e = min(j, k + 1)
                out += k.to_bytes(3, 'big') + (e - k).to_bytes(2, 'big') + dst[k:e]
                k = e
        i = j
    out += b'EOF'
    if n != len(src):
        out += n.to_bytes(3, 'big')     # truncation/size extension marker
    return bytes(out)

def apply(src, patch):
    assert patch[:5] == b'PATCH'
    buf = bytearray(src); p = 5
    while patch[p:p + 3] != b'EOF':
        off = int.from_bytes(patch[p:p + 3], 'big'); size = int.from_bytes(patch[p + 3:p + 5], 'big'); p += 5
        if size == 0:
            rl = int.from_bytes(patch[p:p + 2], 'big'); data = patch[p + 2:p + 3] * rl; p += 3
        else:
            data = patch[p:p + size]; p += size
        if len(buf) < off + len(data): buf += bytes(off + len(data) - len(buf))
        buf[off:off + len(data)] = data
    p += 3
    if len(patch) >= p + 3:
        size = int.from_bytes(patch[p:p + 3], 'big')
        if len(buf) < size: buf += bytes(size - len(buf))
        else: del buf[size:]
    return bytes(buf)

if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'create':
        s = open(sys.argv[2], 'rb').read(); t = open(sys.argv[3], 'rb').read()
        open(sys.argv[4], 'wb').write(create(s, t)); print('ips written')
    elif cmd == 'apply':
        s = open(sys.argv[2], 'rb').read(); pt = open(sys.argv[3], 'rb').read()
        open(sys.argv[4], 'wb').write(apply(s, pt)); print('applied')
