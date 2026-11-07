#!/usr/bin/env bash
# 개발 뉴스를 GitHub(공개 저장소 dev-news)에 올리고 GitHub Pages 를 켭니다.
set -e
GH="/c/Program Files/GitHub CLI/gh.exe"
cd /c/Users/kkhss/Documents/dev-news

[ -d .git ] || git init -q -b main
printf 'kakao.txt\n__pycache__/\n' > .gitignore
git add -A
git -c user.name="Kkhgold" -c user.email="kkhssam3@gmail.com" commit -q -m "Dev news $(date +%Y-%m-%d)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" || echo "(변경 없음)"

if ! git remote get-url origin >/dev/null 2>&1; then
  "$GH" repo create dev-news --public --source . --push --description "평일 개발·AI 뉴스"
  "$GH" api -X POST repos/Kkhgold/dev-news/pages -f "source[branch]=main" -f "source[path]=/" >/dev/null
else
  git push -q origin main
fi
echo "✅ https://kkhgold.github.io/dev-news/"
