# 스타폭스 2 한글 패치

*Star Fox 2* (슈퍼 패미컴, 일본판 / Classic Mini·Switch Online 덤프) 비공식 한국어 팬 패치입니다.
대사는 일본어판 원문을 기준으로 번역했습니다.

**제작: arqhive**

- 대사 216개 전체 한글화 (페퍼 장군 브리핑, 팀원·스타울프·안돌프 대사, 조작 안내)
- 슈퍼FX(GSU) 텍스트 렌더러 확장: 한글 폰트 7페이지(약 460자), 2바이트 문자 지원
- **원본과 같은 1MB 롬 크기 유지** (롬 확장 없음)
- 그림 글씨 한글화: 맵 HUD, 파일럿 선택, 조작 설정, 결과·기록 화면, 일시정지 메뉴, MISSION 설명 패널 등
- 확인 환경: Mesen 2 (첫 스테이지 진입까지 플레이 확인)

> 이 저장소에는 **게임 데이터(롬, 추출한 원문 대사, 그래픽, 스크린샷)가 들어 있지 않습니다.**
> 패치를 만들거나 적용하려면 본인이 소유한 게임에서 직접 덤프한 원본이 필요합니다.

## 사용자용: 패치 적용

[`release/`](release/) 폴더의 패치(`.bps` 권장, `.ips`도 제공)와 [`README_한국어.txt`](release/README_한국어.txt)를 참고하세요.

| 원본 (일본판, 헤더 없음) | 값 |
|---|---|
| 파일명 예 | `Star Fox 2 (Japan) (Classic Mini, Switch Online).sfc` |
| 크기 | 1,048,576 바이트 |
| CRC32 | `3753682F` |
| MD5 | `e7de4068dd0577ec5567783739839a76` |
| SHA1 | `578df9cc661548f278faa1fb4b9b2e9701bde92e` |

| 패치 적용 결과 | 값 |
|---|---|
| 크기 | 1,048,576 바이트 (원본과 같음) |
| CRC32 | `AFC844D5` |
| MD5 | `8eae26ddd7bc53b205adb2bb35e6a559` |
| SHA1 | `72ed558011fbd9f98ea6f491973042d6b017ad86` |

- 북미·유럽판 롬에는 적용할 수 없습니다.
- 확인: Mesen 2. 원본과 같은 1MB 구조라 슈퍼FX를 지원하는 PC 에뮬레이터(bsnes/higan, Snes9x 등),
  SNES Classic Mini·Switch Online, FXPak Pro에서도 동작할 것으로 예상하지만 **실기·공식 에뮬레이터는 확인하지 않았습니다.**
- SNES 에버드라이브는 슈퍼FX를 지원하지 않아 원본도 실행되지 않습니다.

## 개발자용: 직접 빌드

### 요구 사항
- Python 3.10 이상, [Pillow](https://pypi.org/project/pillow/)
- 원본 롬 (위 해시와 일치하는 파일)
- 폰트는 저장소의 [`fonts/`](fonts/)(Galmuri BDF)를 쓰므로 OS 폰트와 무관하게 같은 결과가 나옵니다.

### 빌드
```bash
python tools/build_ko.py --rom "path/to/Star Fox 2 (Japan).sfc" --out work/sf2_ko.sfc
python tools/bps.py create "path/to/Star Fox 2 (Japan).sfc" work/sf2_ko.sfc work/patch.bps
python tools/ips.py create "path/to/Star Fox 2 (Japan).sfc" work/sf2_ko.sfc work/patch.ips
```
빌드 결과는 위 "패치 적용 결과" 해시와 바이트 단위로 같습니다.

`build_ko.py`는 다음을 수행합니다.
1. `translation/gfx_ko.py` 정의에 따라 압축 그래픽을 풀어 한글을 그리고 재압축해 제자리에 삽입
   (커진 블록은 롬 안의 빈 공간으로 옮기고 포인터 수정)
2. MISSION 설명 패널(비압축 8bpp 이미지) 수정
3. `translation/ko.txt`에서 쓰인 글자로 한글 폰트 페이지(Galmuri9) 생성:
   첫 페이지는 원래 일본어 대사 폰트 자리, 나머지는 뱅크 끝 빈 공간에 배치
4. 슈퍼FX 텍스트 루틴에 훅 삽입 (`0x01`~`0x0F` 접두 바이트 = 폰트 페이지 전환)
5. 대사를 다시 인코딩해 원래 대사 영역에 기록, 체크섬 갱신

### 번역 작업
- 대사: [`translation/ko.txt`](translation/ko.txt) — `번호|번역문` 형식. 태그 `{START}` `{SELECT}` `[Y]` `[X]` `[A]` `[B]` `[L]` `[R]` `[+]` `[▶]`.
- 원문 확인: `python tools/export_jp.py --rom 원본.sfc` → `work/jp.json` (원문이므로 커밋 금지)
- 줄 넘침 검사: 빌드 후 `python tools/wrapsim.py work/sf2_ko.sfc 127` (맵 대화창) / `112` (전투 통신창). 한 대사는 3줄 이내여야 합니다.
- 그림 글씨: [`translation/gfx_ko.py`](translation/gfx_ko.py) — 블록별 좌표·색·문구 정의.

## 폴더 구조

```
release/       배포용 BPS/IPS 패치 + 사용자 설명서
translation/   대사 번역(ko.txt), 그림 글씨 정의(gfx_ko.py)
fonts/         Galmuri 비트맵 폰트(BDF) + 라이선스(SIL OFL 1.1)
tools/         빌드 도구와 분석 도구 (자세한 목록은 docs/TECHNICAL.md)
docs/          기술 문서
```

## 기술 문서

텍스트·폰트 구조, 슈퍼FX 훅, 그래픽 압축 형식, 에뮬레이터 자동화 방법은 [`docs/TECHNICAL.md`](docs/TECHNICAL.md)에 정리했습니다.

## 알려진 문제

- 대사 창에서 줄이 꽉 찬 경우 넘김 표시(▼)가 마지막 글자와 조금 겹칠 수 있습니다.
- 작은 라벨(7px)은 공간 제약으로 글자가 촘촘합니다.
- 결과·기록·조작 설정·EXPERT 안내 화면 등 일부 그림 글씨는 게임 화면에서 모두 확인하지 못했습니다. 이상한 부분은 이슈로 알려주세요.
- 오프닝·엔딩 스태프 롤 등 원래 영문인 그래픽은 그대로입니다.

## 크레딧·라이선스

- 이 저장소의 도구 코드, 한국어 번역문, 문서: [MIT License](LICENSE) (© 2026 arqhive)
- 폰트: [Galmuri](https://github.com/quiple/galmuri) © quiple, [SIL Open Font License 1.1](fonts/OFL-Galmuri.txt)

## 면책

비공식 팬 번역이며 Nintendo와 관련이 없습니다. 「스타폭스」 관련 상표·저작권은 Nintendo에 있습니다.
패치된 롬의 배포를 금지합니다.
