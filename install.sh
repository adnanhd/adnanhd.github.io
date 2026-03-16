#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

DEST="${1:?Usage: $0 user@host:/path/to/webroot}"

echo "Deploying to $DEST..."
scp -r index.html style.css data.js sitemap.xml robots.txt 404.html \
    resume.pdf cv.pdf profile.jpeg profile-sm.jpeg \
    images/ blogs/ "$DEST"

echo "Done."
