# Star Fox 2 그림 글씨 한글화 정의 (tools/gfx_ko.py 가 읽음)
# 좌표는 블록 이미지(16타일 폭) 기준 픽셀. work/i_<blob>_N.png, tools/dumpidx.py 참고.
# 폰트: g7(Galmuri7, 한글 7px) g7s(g7을 6px로 자름, 받침 글자 주의) g9 g11 g11b g11c

BLOBS = [
    # ---- 맵 화면 HUD ----
    {'blob': '19_8000-8A80', 'bpp': 4, 'items': [
        {'rect': (2, 33, 36, 7), 'text': '파일럿', 'font': 'g7', 'fg': 0xE, 'bg': 6},
        {'rect': (43, 33, 37, 7), 'text': '실드', 'font': 'g7', 'fg': 0xE, 'bg': 6},
        {'rect': (86, 33, 24, 7), 'text': '아이템', 'font': 'g7', 'fg': 0xE, 'bg': 6},
        {'rect': (0, 41, 30, 7), 'text': '타임', 'font': 'g7', 'fg': 0xE, 'bg': 6},
        {'rect': (34, 41, 36, 7), 'text': '스코어', 'font': 'g7', 'fg': 0xE, 'bg': 6},
        {'rect': (79, 67, 40, 13), 'clear_rect': (79, 68, 40, 12), 'text': '코네리아\n대미지',
         'font': 'g7s', 'fg': 0xE, 'bg': 2, 'clear': [0xE, 1], 'line_gap': 1},
    ]},
    # ---- 파일럿 선택 화면 ----
    {'blob': '18_DF19-EAE9', 'bpp': 4, 'items': [
        {'rect': (77, 7, 46, 17), 'clear_rect': (77, 6, 46, 18), 'fill': True, 'text': '파일럿\n셀렉트',
         'font': 'g7', 'fg': 1, 'bg': 7, 'outline': 8, 'line_gap': 1},
        {'rect': (49, 89, 31, 7), 'clear_rect': (50, 89, 29, 7), 'fill': True, 'text': '충전', 'font': 'g7',
         'fg': 0xC, 'bg': 0xE},
        {'rect': (85, 89, 26, 7), 'clear_rect': (86, 89, 24, 7), 'fill': True, 'text': '실드', 'font': 'g7',
         'fg': 0xC, 'bg': 0xE},
        {'tiles': [190, 191, 208, 209], 'rect': (3, 1, 28, 7), 'clear_rect': (4, 1, 26, 7), 'fill': True,
         'text': '스피드', 'font': 'g7', 'fg': 0xC, 'bg': 0xE},
    ]},
    {'blob': '18_9697-A6FF', 'bpp': 4, 'items': [
        {'rect': (1, 56, 42, 7), 'vflip': True, 'text': '아이템', 'font': 'g7', 'fg': 9, 'bg': 0xB, 'clear': [9, 0xA]},
        {'rect': (64, 23, 31, 7), 'clear_rect': (64, 22, 31, 9), 'fill': True, 'text': '컨트롤', 'font': 'g7',
         'fg': 1, 'bg': 0, 'outline': 0xF},
        {'rect': (1, 17, 62, 7), 'clear_rect': (1, 16, 62, 8), 'text': '셀렉트', 'font': 'g7', 'bold': True, 'spacing': 2, 'fg': 1, 'bg': 0xD},
        {'rect': (1, 32, 62, 7), 'clear_rect': (1, 32, 62, 8), 'text': '컨트롤', 'font': 'g7', 'bold': True, 'spacing': 2, 'fg': 1, 'bg': 0xD},
        {'rect': (24, 147, 76, 11), 'fill': True, 'text': '파트너', 'font': 'g11', 'bold': True, 'spacing': 4,
         'fg': 9, 'bg': 0, 'outline': 0xF},
    ]},
    # ---- 조작 설정 (2bpp) ----
    {'blob': '19_8A80-8EE4', 'bpp': 2, 'items': [
        {'rect': (9, 6, 31, 8), 'text': '다운', 'font': 'g7', 'fg': 1, 'bg': 3},
        {'rect': (62, 6, 35, 8), 'text': '부스트', 'font': 'g7', 'fg': 1, 'bg': 3},
        {'rect': (62, 15, 35, 8), 'text': '스페셜', 'font': 'g7', 'fg': 1, 'bg': 3},
        {'rect': (62, 24, 35, 8), 'text': '브레이크', 'font': 'g7', 'fg': 1, 'bg': 3},
        {'rect': (9, 33, 31, 8), 'text': '업', 'font': 'g7', 'fg': 1, 'bg': 3},
        {'rect': (62, 33, 35, 8), 'text': '블래스터', 'font': 'g7', 'fg': 1, 'bg': 3},
        {'rect': (1, 54, 30, 8), 'text': '업', 'font': 'g7', 'fg': 1, 'bg': 3},
        {'rect': (37, 54, 35, 8), 'text': '블래스터', 'font': 'g7', 'fg': 1, 'bg': 3},
        {'rect': (76, 48, 36, 8), 'text': '스페셜', 'font': 'g7', 'fg': 1, 'bg': 3},
        {'rect': (76, 57, 36, 7), 'text': '브레이크', 'font': 'g7', 'fg': 1, 'bg': 3},
        {'rect': (1, 65, 30, 7), 'text': '다운', 'font': 'g7', 'fg': 1, 'bg': 3},
        {'rect': (37, 63, 35, 8), 'text': '부스트', 'font': 'g7', 'fg': 1, 'bg': 3},
    ]},
    # ---- 결과 화면 ----
    {'blob': '18_BF5D-DF19', 'bpp': 4, 'items': [
        {'rect': (84, 112, 44, 8), 'text': '사용 안 함', 'font': 'g7', 'fg': 0xE, 'bg': 1},
        {'rect': (84, 120, 44, 8), 'text': '사용함', 'font': 'g7', 'fg': 0xE, 'bg': 1},
        {'rect': (10, 129, 44, 13), 'fill': True, 'text': '기록삭제', 'font': 'g9', 'bold': True,
         'fg': 1, 'bg': 0xA, 'outline': 0xF},
        {'rect': (64, 128, 23, 8), 'text': '사인', 'font': 'g7', 'fg': 1, 'bg': 5},
        {'tiles': [268, 269, 270, 271, 279], 'rect': (4, 1, 35, 7), 'text': '파일럿', 'font': 'g7', 'fg': 1, 'bg': 5},
        {'rect': (80, 136, 48, 8), 'text': '토털 스코어', 'font': 'g7', 'fg': 1, 'bg': 5},
        # 스코어 화면 제목: 타일 131-140(y64) 위 + 464-473(y232) 아래가 한 줄로 합쳐짐
        {'tiles': [list(range(131, 141)), list(range(464, 474))], 'rect': (3, 1, 74, 12),
         'clear_rect': (0, 0, 80, 14), 'clear': [1, 0xC, 0xD, 0xE], 'text': '스코어 베스트5', 'font': 'g9',
         'fg': 0xD, 'bg': 0xB, 'outline': 0xC, 'fg_bottom': (0xE, 2)},
        {'rect': (24, 144, 64, 14), 'fill': True, 'text': '결과 보고', 'font': 'g11', 'spacing': 2,
         'fg': 4, 'bg': 5, 'outline': 0xF},
        {'rect': (96, 144, 24, 8), 'text': '타임', 'font': 'g7', 'fg': 1, 'bg': 5},
        {'rect': (96, 152, 24, 8), 'text': '랭크', 'font': 'g7', 'fg': 1, 'bg': 5},
        {'rect': (0, 184, 88, 7), 'fill': True, 'text': '기본 스코어', 'font': 'g7', 'align': 'left', 'fg': 0xE, 'bg': 1},
        {'rect': (0, 192, 88, 7), 'fill': True, 'text': '파괴한 배틀십', 'font': 'g7', 'align': 'left', 'fg': 0xE, 'bg': 1},
        {'rect': (0, 200, 88, 7), 'fill': True, 'text': '되찾은 행성', 'font': 'g7', 'align': 'left', 'fg': 0xE, 'bg': 1},
        {'rect': (0, 208, 80, 7), 'fill': True, 'text': '타임 (리미트)', 'font': 'g7', 'align': 'left', 'fg': 0xE, 'bg': 1},
        {'rect': (0, 216, 88, 7), 'fill': True, 'text': '코네리아 대미지', 'font': 'g7', 'align': 'left', 'fg': 0xE, 'bg': 1},
        {'rect': (0, 224, 88, 7), 'fill': True, 'text': '파트너 컨티뉴', 'font': 'g7', 'align': 'left', 'fg': 0xE, 'bg': 1},
        {'rect': (95, 193, 32, 13), 'fill': True, 'text': '토털', 'font': 'g9', 'bold': True, 'fg': 0xE, 'bg': 5, 'outline': 0xF},
        {'rect': (89, 209, 23, 13), 'fill': True, 'text': '점수', 'font': 'g9', 'bold': True, 'fg': 0xE, 'bg': 5, 'outline': 0xF},
        {'rect': (90, 223, 30, 8), 'fill': True, 'text': '랭크', 'font': 'g7', 'fg': 0xF, 'bg': 5},
        {'rect': (2, 241, 38, 13), 'clip': (2, 241, 38, 13), 'clear': [1, 0xF], 'text': '재도전', 'font': 'g9',
         'bold': True, 'fg': 1, 'bg': 8, 'outline': 0xF},
        # 버튼 오른쪽 끝 타일(x80-87)은 두 버튼이 공유하므로 건드리지 않음
        {'rect': (42, 241, 38, 13), 'clip': (42, 241, 38, 13), 'clear': [1, 0xF], 'text': '타이틀', 'font': 'g9',
         'bold': True, 'fg': 1, 'bg': 8, 'outline': 0xF},
        {'rect': (89, 241, 39, 13), 'fill': True, 'text': '기록보기', 'font': 'g9', 'spacing': -1,
         'fg': 1, 'bg': 0xD, 'outline': 0xF},
    ]},
    # ---- 기록 화면 ----
    {'blob': '17_9B74-AA48', 'bpp': 4, 'items': [
        {'rect': (0, 48, 128, 8), 'fill': True, 'text': '사인을 해 주게', 'font': 'g7', 'align': 'left', 'dx': 8, 'fg': 1, 'bg': 0},
        {'rect': (0, 56, 128, 8), 'fill': True, 'text': '어느 것을 자세히 보겠나?', 'font': 'g7', 'align': 'left', 'fg': 1, 'bg': 0},
        {'rect': (0, 64, 70, 8), 'fill': True, 'text': '삭제할까? (', 'font': 'g7', 'align': 'left', 'fg': 1, 'bg': 0},
        {'rect': (0, 72, 70, 8), 'fill': True, 'text': '정말인가? (', 'font': 'g7', 'align': 'left', 'fg': 1, 'bg': 0},
        {'rect': (0, 80, 128, 8), 'fill': True, 'text': '알았네! 지워 두지.', 'font': 'g7', 'align': 'left', 'fg': 1, 'bg': 0},
        {'rect': (0, 88, 128, 8), 'fill': True, 'text': '거기엔 데이터가 없네!', 'font': 'g7', 'align': 'left', 'fg': 1, 'bg': 0},
        {'rect': (0, 104, 24, 8), 'clear_rect': (0, 104, 24, 8), 'fill': True, 'clip': (0, 104, 24, 8),
         'text': '토털', 'font': 'g7', 'fg': 4, 'bg': 0, 'shadow': (9, 1, 1)},
    ]},
    # ---- EXPERT 안내 ----
    {'blob': '17_8000-9B74', 'bpp': 4, 'items': [
        {'rect': (54, 214, 34, 8), 'fill': True, 'text': '레벨에', 'font': 'g7', 'align': 'left', 'fg': 9, 'bg': 0xE},
        {'rect': (16, 225, 72, 8), 'fill': True, 'text': '도전해 보자!', 'font': 'g7', 'align': 'left', 'fg': 9, 'bg': 0xE},
    ]},
    # ---- 일시정지(맵) 메뉴: 스프라이트 타일 64-73 / 80-89 / 77-79 ----
    {'blob': '16_DDD4-E5F8', 'bpp': 4, 'items': [
        {'rect': (0, 32, 80, 7), 'clear_rect': (0, 32, 80, 8), 'fill': True, 'clip': (0, 32, 80, 8),
         'text': '배틀 계속', 'font': 'g7', 'align': 'left', 'dx': 1, 'fg': 1, 'bg': 0, 'outline': 0xF, 'fg_bottom': (2, 2)},
        {'rect': (0, 40, 80, 7), 'clear_rect': (0, 40, 80, 8), 'fill': True, 'clip': (0, 40, 80, 8),
         'text': '맵으로 복귀', 'font': 'g7', 'align': 'left', 'dx': 1, 'fg': 1, 'bg': 0, 'outline': 0xF, 'fg_bottom': (2, 2)},
        {'rect': (104, 32, 24, 7), 'clear_rect': (104, 32, 24, 8), 'fill': True, 'clip': (104, 32, 24, 8),
         'text': '카메라', 'font': 'g7', 'align': 'left', 'fg': 1, 'bg': 0, 'outline': 0xF, 'fg_bottom': (2, 2)},
    ]},
]
