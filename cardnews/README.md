# DRAYZ 카드뉴스 틀

인스타그램용 카드뉴스(1080×1350)를 만드는 단일 HTML 틀입니다.
디자인은 고정하고, **내용(글·사진)만 바꿔서** 매번 같은 톤의 카드뉴스를 만듭니다.

## 파일

| 파일 | 역할 |
|---|---|
| `index.html` | 마스터 틀. 브라우저로 열면 편집기(편집·사진 교체·JPG 저장)로 동작 |
| `tools/fill.py` | 틀 + `data.json` + 사진 폴더 → 카드뉴스 HTML 한 파일 |
| `tools/render.mjs` | 넘침 검사 + 미리보기 + JPG 저장 (Playwright) |
| `tools/setup.sh` | 검사용 글꼴·이미지 저장 도구 받기 |
| `examples/*.data.json` | 실제로 만든 카드뉴스의 데이터 예시 |

## 만드는 순서

```bash
cd cardnews
bash tools/setup.sh                                   # 처음 한 번
python3 -I tools/fill.py --master index.html --data data.json --photos 사진폴더 --out 결과.html
node tools/render.mjs 결과.html out --jpg             # 넘침 보고 + out/preview.png + JPG
```

> `fill.py`는 결과 HTML에 Pretendard 글꼴(woff2)을 직접 넣습니다(약 +2.7MB).
> 인터넷이 막히거나 앱 안 브라우저에서 열어도 편집 화면과 "JPG 저장"이 같은 글꼴로 나옵니다.
> 글꼴 파일은 `tools/setup.sh`가 `tools/vendor/`에 받아 둡니다.

## 카드 종류 (`type`)

| type | 모양 | 사진 |
|---|---|---|
| `cover` | 표지 · 전면 사진 | 세로 사진이 좋음 (가로는 좌우가 잘림) |
| `photo` | 전면 사진 + 아래 어두운 설명 상자 | 아래 35%는 상자에 가려짐 |
| `split` | 위쪽 사진(62%) + 아래 설명 + 태그 | 가로 사진에 적합, 아래로 갈수록 흐려짐 |
| `feature` | 위쪽 사진(58%) + 설명 + 특징 2칸 | 가로 사진 |
| `options` | 옵션 4칸 + 아래 띠 사진 | 아주 넓게 잘림 |
| `gallery` | 사진 4장 모음 (`items`) | 해상도 낮은 사진도 OK |
| `location` | 약도 + 정보 박스 2개 | `map`: 이미지 또는 SVG |
| `closing` | 마무리 · 연락처 | 전면 사진 |

데이터 구조는 `index.html` 맨 위 주석과 `examples/` 를 참고하세요.
