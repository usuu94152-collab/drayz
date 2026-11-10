#!/usr/bin/env python3
"""DRAYZ 카드뉴스 만들기: 틀(index.html) + 내용(data.json) + 사진 폴더 → 카드뉴스 HTML 한 파일.

사용법
  python3 -I tools/fill.py --master index.html --data data.json --photos 사진폴더 --out 결과.html

data.json 은 틀 맨 위 <script id="cardnews-data"> 와 같은 구조입니다.
사진 자리(photo, map, items[].photo)에는
  - 사진 폴더 안의 파일 이름(예: "IMG_0412.jpg") 또는
  - 틀에 이미 들어 있는 보관함 이름(예: "logo-drayz")
을 적으면 됩니다. 파일은 긴 변 1600px 이하 JPEG(품질 86)로 줄여서 담습니다.
"""
import argparse, base64, io, json, re, sys
from pathlib import Path

try:
    from PIL import Image, ImageOps
except ImportError:
    sys.exit('Pillow 가 필요합니다: pip install --break-system-packages pillow')

FONT_LINK_RE = re.compile(r'<link[^>]*pretendard[^>]*>', re.I)
FONT_FILE = Path(__file__).resolve().parent / 'vendor/pretendard/dist/web/variable/woff2/PretendardVariable.woff2'
SCRIPT_RE = re.compile(r'<script[^>]*html-to-image[^>]*></script>', re.I)
SCRIPT_FILE = Path(__file__).resolve().parent / 'vendor/html-to-image/dist/html-to-image.js'
DATA_RE = re.compile(r'(<script type="application/json" id="cardnews-data">)(.*?)(</script>)', re.S)
ASSETS_RE = re.compile(r'(<script type="application/json" id="cardnews-assets">)(.*?)(</script>)', re.S)


def to_json(value, indent=None):
    # </script> 가 끼어들지 않도록 < 를 이스케이프
    return json.dumps(value, ensure_ascii=False, indent=indent).replace('<', '\\u003c')


def encode_photo(path: Path, max_side=1600, quality=86) -> str:
    im = ImageOps.exif_transpose(Image.open(path)).convert('RGB')
    scale = min(1, max_side / max(im.size))
    if scale < 1:
        im = im.resize((round(im.width * scale), round(im.height * scale)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, 'JPEG', quality=quality, optimize=True, progressive=True)
    return 'data:image/jpeg;base64,' + base64.b64encode(buf.getvalue()).decode()


def embed_font(html: str) -> str:
    """jsdelivr 글꼴 링크를 Pretendard 원본(woff2)을 담은 @font-face 로 바꾼다.
    어디서 열어도(오프라인·앱 안 브라우저) 편집 화면과 브라우저 JPG 저장이 같은 글꼴로 나오게 하기 위함."""
    if not FONT_FILE.is_file():
        print('⚠ Pretendard 파일이 없어 글꼴을 넣지 못했어요 (bash tools/setup.sh 먼저 실행). 온라인 링크로 둡니다.')
        return html
    b64 = base64.b64encode(FONT_FILE.read_bytes()).decode()
    style = ('<style id="cardnews-font">/* Pretendard Variable v1.3.9 · SIL OFL 1.1 · github.com/orioncactus/pretendard */\n'
             "@font-face{font-family:'Pretendard Variable';font-weight:45 920;font-style:normal;font-display:block;"
             f"src:url(data:font/woff2;base64,{b64}) format('woff2');}}</style>")
    if FONT_LINK_RE.search(html):
        return FONT_LINK_RE.sub(lambda _: style, html, count=1)
    return html.replace('</head>', style + '\n</head>', 1)


def embed_script(html: str) -> str:
    """jsdelivr 의 html-to-image 링크를 파일 안에 직접 넣는다.
    링크로 두면 인터넷이 막힌 곳(앱 안 미리보기 등)에서 'JPG 저장'이 '이미지 저장 도구를 불러오지 못했어요'로 실패한다."""
    if not SCRIPT_FILE.is_file():
        print('⚠ html-to-image 파일이 없어 저장 도구를 넣지 못했어요 (bash tools/setup.sh 먼저 실행). 온라인 링크로 둡니다.')
        return html
    code = SCRIPT_FILE.read_text(encoding='utf-8')
    code = re.sub(r'//# sourceMappingURL=.*', '', code).replace('</script', '<\\/script')
    tag = '<script id="cardnews-html-to-image">/* html-to-image 1.11.11 · MIT */\n' + code + '\n</script>'
    return SCRIPT_RE.sub(lambda _: tag, html, count=1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--master', required=True)
    ap.add_argument('--data', required=True)
    ap.add_argument('--photos', default='.')
    ap.add_argument('--out', required=True)
    args = ap.parse_args()

    html = Path(args.master).read_text(encoding='utf-8')
    data = json.loads(Path(args.data).read_text(encoding='utf-8'))
    m = ASSETS_RE.search(html)
    if not m or not DATA_RE.search(html):
        sys.exit('틀에서 cardnews-data / cardnews-assets 블록을 찾지 못했어요.')
    old_assets = json.loads(m.group(2) or '{}')
    photos = Path(args.photos)

    assets, encoded = {}, {}
    def take(name):
        if not name:
            return name
        if name in old_assets:                      # 로고 등 틀에 있던 것
            assets[name] = old_assets[name]
            return name
        f = photos / name
        if not f.is_file():
            sys.exit(f'사진을 찾을 수 없어요: {f}')
        if name not in encoded:
            key = 'photo-' + re.sub(r'[^0-9A-Za-z가-힣_-]+', '-', f.stem)
            while key in assets and key not in encoded.values():
                key += '-1'
            assets[key] = encode_photo(f)
            encoded[name] = key
        return encoded[name]

    take(data.get('brand', {}).get('logo'))
    for slide in data['slides']:
        if 'photo' in slide:
            slide['photo'] = take(slide['photo'])
        if 'map' in slide and slide['map'] and not str(slide['map']).startswith('<'):
            slide['map'] = take(slide['map'])
        for item in slide.get('items', []):
            item['photo'] = take(item.get('photo'))

    html = DATA_RE.sub(lambda mm: mm.group(1) + '\n' + to_json(data, 2) + '\n' + mm.group(3), html, count=1)
    html = ASSETS_RE.sub(lambda mm: mm.group(1) + to_json(assets) + mm.group(3), html, count=1)
    html = embed_script(embed_font(html))
    Path(args.out).write_text(html, encoding='utf-8')
    print(f'만듦: {args.out} ({len(html)//1024} KB, 카드 {len(data["slides"])}장, 사진 {len(encoded)}장)')


if __name__ == '__main__':
    main()
