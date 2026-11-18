#!/bin/bash
# Copies the committed program files of the current commit into
# C:\sketchup_dev\detail_manager_release (outside the repo), so switching
# branches during development never changes the copy used for daily work.
set -e
cd "$(dirname "$0")/.."
[ -z "$(git status --porcelain src)" ] || { echo "src has uncommitted changes - commit first"; exit 1; }
OUT=../detail_manager_release
mkdir -p "$OUT"
for f in detail_manager.py abbreviations.json categories.json thumbnail_worker.rb; do git show "HEAD:src/$f" > "$OUT/$f"; done
cp tools/START_DETAIL_MANAGER.bat "$OUT/START_DETAIL_MANAGER.bat"
printf 'Detail Manager release copy\r\nBuilt from: %s (%s)\r\nCommit date: %s\r\nPublished: %s\r\n' \
  "$(git rev-parse --abbrev-ref HEAD)" "$(git rev-parse --short HEAD)" "$(git log -1 --format=%ci)" "$(date '+%Y-%m-%d %H:%M')" > "$OUT/VERSION.txt"
echo "published $(git rev-parse --short HEAD) to $OUT"
