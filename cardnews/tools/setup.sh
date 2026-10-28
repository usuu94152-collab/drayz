#!/usr/bin/env bash
# 미리보기·JPG 저장 검사용 글꼴(Pretendard)과 이미지 저장 도구(html-to-image)를 tools/vendor 에 받아 둡니다.
# (작업 환경에서 jsdelivr 가 막혀 있어도 npm 으로는 받을 수 있음)
set -e
cd "$(dirname "$0")"
mkdir -p vendor && cd vendor
[ -d pretendard ] || { npm pack pretendard@1.3.9 >/dev/null 2>&1; mkdir pretendard; tar xzf pretendard-1.3.9.tgz -C pretendard --strip-components=1; rm pretendard-1.3.9.tgz; }
[ -d html-to-image ] || { npm pack html-to-image@1.11.11 >/dev/null 2>&1; mkdir html-to-image; tar xzf html-to-image-1.11.11.tgz -C html-to-image --strip-components=1; rm html-to-image-1.11.11.tgz; }
echo "준비 완료: $(pwd)"
