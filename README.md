# 스타폭스 2 (SFC, SNES) 한글 패치

*Star Fox 2* (슈퍼 패미컴, 일본판 Classic Mini·Switch Online 덤프) 비공식 한국어 팬 패치입니다.
대사는 일본어판 원문을 기준으로 번역했습니다.

**제작: arqhive** · **최신 버전: [v1.1.1](https://github.com/arqhive/star-fox-2-korean-translation/releases/tag/v1.1.1)**

- 대사 216개 전체를 한글화했습니다(페퍼 장군 브리핑, 팀원·스타울프·안돌프 대사, 조작 안내).
- 슈퍼FX(GSU) 텍스트 렌더러를 확장해 한글 폰트 7페이지(약 460자)와 2바이트 문자를 지원합니다.
- 그림 글씨를 한글화했습니다(맵 HUD, 파일럿 선택, 조작 설정, 결과·기록 화면, 일시정지 메뉴, MISSION 설명 패널 등).
- **원본과 같은 1MB 롬 크기를 유지합니다.** 롬을 확장하지 않았습니다.

> 이 저장소에는 **게임 데이터(롬·디스크 이미지, 추출한 원문 대사, 그래픽, 스크린샷)가 들어 있지 않습니다.**
> 패치를 만들거나 적용하려면 본인이 소유한 게임에서 직접 덤프한 원본이 필요합니다.

## 사용자용: 패치 적용

### 준비물

- 일본판 롬(헤더 없음). 북미·유럽판에는 적용할 수 없습니다.
- BPS 패치 도구. [Rom Patcher JS](https://www.marcrobledo.com/RomPatcher.js/)나 Floating IPS를 쓰면 됩니다.

### 적용 방법

1. [배포 페이지](https://github.com/arqhive/star-fox-2-korean-translation/releases/tag/v1.1.1)에서 `StarFox2_JP_Korean_v1.1.1.zip`을 받습니다.
2. 가진 롬에 맞는 패치 하나를 적용합니다.

   | 가진 롬 | 적용할 패치 |
   |---|---|
   | 원본 일본판 | `StarFox2_JP_Korean_v1.1.1.bps` (권장) 또는 `.ips` |
   | 기존 v1.1 한글판 | `StarFox2_Korean_v1.1_to_v1.1.1.bps` |

3. 결과 롬의 확인값을 아래 표와 비교합니다. 어느 패치를 써도 결과는 같습니다.

자세한 방법은 [`README_한국어.txt`](release/README_한국어.txt)를 참고하세요.

### 파일 확인값

| 항목 | 원본 일본판 (헤더 없음) | 패치 적용 결과 (v1.1.1) |
|---|---|---|
| 크기 | 1,048,576 바이트 | 1,048,576 바이트 |
| CRC32 | `3753682F` | `CCF4A953` |
| MD5 | `e7de4068dd0577ec5567783739839a76` | `f94f97ea6ccb483ff62d1c4ca85b49e8` |
| SHA-1 | `578df9cc661548f278faa1fb4b9b2e9701bde92e` | `307dcb87a40d71ed34e4fa116a1f5b444fad74fb` |

원본 파일명 예: `Star Fox 2 (Japan) (Classic Mini, Switch Online).sfc`

### 실행 환경

- **확인함**: Mesen 2, Wii U용 RetroArch Snes9x 2010 코어.
- **미확인**: bsnes/higan, 최신 Snes9x(Snes9x 2010 코어 제외) 등 슈퍼FX를 지원하는 PC 에뮬레이터, SNES Classic Mini·Switch Online, FXPak Pro. 원본과 같은 1MB 구조라 동작할 것으로 예상합니다.

### 알려진 문제

- 맵 화면 대화창에서 줄이 꽉 차면 넘김 표시(▼)가 마지막 글자와 조금 겹칠 수 있습니다.
- 작은 라벨(7px)은 공간이 좁아 글자가 촘촘합니다.
- 스코어 화면의 "파일럿" 라벨은 결과 화면과 타일을 공유하는 제약 때문에 판 가운데보다 약간 왼쪽에 있습니다.
- EXPERT 레벨 안내 등 일부 그림 글씨는 게임 화면에서 확인하지 못했습니다. 이상한 부분은 이슈로 알려 주세요.
- 오프닝·엔딩 스태프 롤 등 원래 영문인 그래픽은 그대로입니다.

## 개발자용: 직접 빌드

### 요구 사항

- Python 3.10 이상, [Pillow](https://pypi.org/project/pillow/).
- 원본 롬(위 확인값과 일치하는 파일).
- 폰트는 저장소의 [`fonts/`](fonts/)(Galmuri BDF)를 쓰므로 OS 폰트와 관계없이 같은 결과가 나옵니다.

### 빌드

```bash
python tools/build_ko.py --rom "path/to/Star Fox 2 (Japan).sfc" --out work/sf2_ko.sfc
python tools/bps.py create "path/to/Star Fox 2 (Japan).sfc" work/sf2_ko.sfc work/patch.bps
python tools/ips.py create "path/to/Star Fox 2 (Japan).sfc" work/sf2_ko.sfc work/patch.ips
```

대사·폰트·그림 글씨를 모두 포함한 전체 빌드이며, 결과는 v1.1.1 배포본과 바이트 단위로 같습니다.

`build_ko.py`는 다음을 수행합니다.

1. `translation/gfx_ko.py` 정의에 따라 압축 그래픽을 풀어 한글을 그리고, 다시 압축해 제자리에 넣습니다. 커진 블록은 롬 안의 빈 공간으로 옮기고 포인터를 고칩니다.
2. MISSION 설명 패널(비압축 8bpp 이미지)을 수정합니다.
3. `translation/ko.txt`에 쓰인 글자로 한글 폰트 페이지(Galmuri9)를 만듭니다. 첫 페이지는 원래 일본어 대사 폰트 자리에, 나머지는 뱅크 끝 빈 공간에 둡니다.
4. 슈퍼FX 텍스트 루틴에 훅을 넣습니다. 접두 바이트 `0x01`에서 `0x0F`까지가 폰트 페이지 전환입니다.
5. 대사를 다시 인코딩해 원래 대사 영역에 기록하고 체크섬을 갱신합니다.

`tools/build_graphics.py`는 v1.1에서 쓴 그래픽 전용 경로입니다. v1.0 롬의 그래픽 스트림만 바꿔 v1.1 롬을 재현하며, 대사가 바뀐 v1.1.1부터는 위의 전체 빌드를 씁니다.

### 번역 수정

- 대사: [`translation/ko.txt`](translation/ko.txt). `번호|번역문` 형식이며 태그는 `{START}` `{SELECT}` `[Y]` `[X]` `[A]` `[B]` `[L]` `[R]` `[+]` `[▶]`입니다.
- 원문 확인: `python tools/export_jp.py --rom 원본.sfc`를 실행하면 `work/jp.json`이 만들어집니다. 원문이므로 커밋하지 않습니다.
- 줄 넘침 검사: 빌드 후 `python tools/wrapsim.py work/sf2_ko.sfc 127`(맵 대화창)과 `108`(전투·컷신 통신창)을 실행합니다. 한 대사는 3줄 이내여야 합니다.
- 그림 글씨: [`translation/gfx_ko.py`](translation/gfx_ko.py)에 블록별 좌표·색·문구를 정의합니다.

### 폴더 구조

```
release/       배포용 BPS/IPS 패치와 사용자 설명서
translation/   대사 번역(ko.txt), 그림 글씨 정의(gfx_ko.py)
fonts/         Galmuri 비트맵 폰트(BDF)와 라이선스(SIL OFL 1.1)
tools/         빌드 도구와 분석 도구
docs/          기술 문서, 릴리즈 노트 사본(docs/releases/)
```

### 기술 문서

텍스트·폰트 구조, 슈퍼FX 훅, 그래픽 압축 형식, 에뮬레이터 자동화 방법은 [`docs/TECHNICAL.md`](docs/TECHNICAL.md)에 정리했습니다.
v1.1 그래픽 개선 과정은 [`docs/GRAPHICS_REFINEMENT.md`](docs/GRAPHICS_REFINEMENT.md)에 있습니다.

## 변경 내역

전체 내역은 [`CHANGELOG.md`](CHANGELOG.md)에 있습니다.

## 크레딧·라이선스

- 이 저장소의 도구 코드, 한국어 번역문, 문서: [MIT License](LICENSE) (© 2026 arqhive).
- 폰트와 Galmuri 기반 HUD6 파생 픽셀: [Galmuri](https://github.com/quiple/galmuri) © quiple, [SIL Open Font License 1.1](fonts/OFL-Galmuri.txt).

## 면책

비공식 팬 번역이며 Nintendo와 관련이 없습니다. 「스타폭스」 관련 상표·저작권은 Nintendo에 있습니다.
패치를 적용한 게임 파일의 배포를 금지합니다.
