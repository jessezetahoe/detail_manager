#!/bin/bash
# Copies the committed program files of the current commit into
# C:\sketchup_dev\detail_manager_release (outside the repo), so switching
# branches during development never changes the copy used for daily work.
set -e
cd "$(dirname "$0")/.."
[ -z "$(git status --porcelain src)" ] || { echo "src has uncommitted changes - commit first"; exit 1; }
OUT=../detail_manager_release
mkdir -p "$OUT"
VERSION=$(git show HEAD:src/detail_manager.py | sed -n 's/^APP_VERSION = "\(.*\)"/\1/p')
[ -n "$VERSION" ] || { echo "APP_VERSION not found in src/detail_manager.py"; exit 1; }
if [ -f "$OUT/VERSION.txt" ] && [ "${FORCE:-}" != "1" ]; then
  OLD_VERSION=$(sed -n 's/^Version: \([^\r]*\).*/\1/p' "$OUT/VERSION.txt")
  OLD_COMMIT=$(sed -n 's/^Built from: .*(\([0-9a-f]*\)).*/\1/p' "$OUT/VERSION.txt")
  if [ "$OLD_VERSION" = "$VERSION" ] && [ "$OLD_COMMIT" != "$(git rev-parse --short HEAD)" ]; then
    echo "Version $VERSION was already published from $OLD_COMMIT: bump APP_VERSION first (or FORCE=1)"; exit 1
  fi
fi
for f in detail_manager.py abbreviations.json categories.json chips.json thumbnail_worker.rb how_to.html; do git show "HEAD:src/$f" > "$OUT/$f"; done
cp tools/START_DETAIL_MANAGER.bat "$OUT/START_DETAIL_MANAGER.bat"
printf 'Detail Manager release copy\r\nVersion: %s\r\nBuilt from: %s (%s)\r\nCommit date: %s\r\nPublished: %s\r\n' \
  "$VERSION" "$(git rev-parse --abbrev-ref HEAD)" "$(git rev-parse --short HEAD)" "$(git log -1 --format=%ci)" "$(date '+%Y-%m-%d %H:%M')" > "$OUT/VERSION.txt"
echo "published $VERSION ($(git rev-parse --short HEAD)) to $OUT"
