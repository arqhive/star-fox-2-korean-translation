import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from blobimg import to_pixels
name, bpp = sys.argv[1], int(sys.argv[2])
x0, y0, x1, y1 = map(int, sys.argv[3].split(','))
d = open('work/blobs_J/%s.bin' % name, 'rb').read()
px, n = to_pixels(d, bpp)
print('    ' + ''.join(str((x // 10) % 10) if x % 10 == 0 else ' ' for x in range(x0, x1)))
for y in range(y0, y1):
    print('%3d ' % y + ''.join('%X' % px[y][x] for x in range(x0, x1)))
