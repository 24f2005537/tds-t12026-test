#!/usr/bin/env bash
set -euo pipefail

rm -rf api
rm -f q-vercel-latency.json requirements.txt vercel.json

git add -A
if ! git diff --cached --quiet; then
  git commit -m "Remove Vercel API files"
fi

git push origin main
