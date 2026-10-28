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
    Path(args.out).write_text(html, encoding='utf-8')
    print(f'만듦: {args.out} ({len(html)//1024} KB, 카드 {len(data["slides"])}장, 사진 {len(encoded)}장)')


if __name__ == '__main__':
    main()
