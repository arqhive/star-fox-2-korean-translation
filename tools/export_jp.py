"""Read the Japanese dialogue table from the original ROM.

  python tools/export_jp.py --rom "Star Fox 2 (Japan).sfc" [--out work/jp.json]

The exported file contains original game text: keep it out of git (work/ is ignored).
"""
import sys, json, os, argparse
sys.path.insert(0, os.path.dirname(__file__))
from jp_table import decode
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TABLE = 0x2DA5; COUNT = 216
SPEAKER = {0:'폭스',1:'피피',2:'팔코',3:'슬리피',4:'페퍼 장군',5:'안돌프',7:'미유',8:'페이',0xA:'울프',0xB:'피그마',0xC:'알지',0xD:'레온'}


def read_script(d, with_text=True):
    out = []
    for i in range(COUNT):
        p = int.from_bytes(d[TABLE+2*i:TABLE+2*i+2], 'little') - 0x8000
        e = d.index(0, p+2)
        body = d[p+2:e]
        item = {'id': i, 'speaker': d[p], 'face': d[p+1], 'who': SPEAKER.get(d[p], '?'), 'raw': body.hex()}
        if with_text:
            item['jp'] = decode(body).replace('[ST]{11}[AR]{11}[BOX_L]', '{START}').replace('[SE]{11}[LE]{11}[BOX_R]', '{SELECT}')
        out.append(item)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--rom', required=True)
    ap.add_argument('--out', default=os.path.join(ROOT, 'work', 'jp.json'))
    a = ap.parse_args()
    out = read_script(open(a.rom, 'rb').read())
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump(out, open(a.out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('exported', len(out), '->', a.out)


if __name__ == '__main__':
    main()
