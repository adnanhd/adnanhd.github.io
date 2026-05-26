#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

DEST="${1:?Usage: $0 user@host:/path/to/webroot}"

echo "Deploying to $DEST..."
scp -r index.html sitemap.xml robots.txt 404.html \
    resume.pdf \
    googlefdcfc688492f74e0.html \
    assets/ blogs/ "$DEST"

echo "Done."
