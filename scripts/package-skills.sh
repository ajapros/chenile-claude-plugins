#!/bin/sh
# Builds one zip per skill in dist/, for uploading to claude.ai (Settings > Capabilities > Skills) or for an
# organization owner to provision to everyone (Organization settings > Skills).
set -e
cd "$(dirname "$0")/.."
rm -rf dist && mkdir -p dist
for dir in plugins/*/skills/*/; do
  name=$(basename "$dir")
  (cd "$(dirname "$dir")" && zip -qr "../../../dist/$name.zip" "$name")
  echo "dist/$name.zip"
done
