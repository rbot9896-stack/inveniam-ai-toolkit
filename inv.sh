#!/usr/bin/env bash
# Thin wrapper: the helper is inv.py (cross-platform). Same usage:
#   ./inv.sh GET /v2/path [-H "k: v"] [-d DATA] [-o FILE]
#   INV_ENV=sales ./inv.sh GET /v2/path
D="$(cd "$(dirname "$0")" && pwd)"
exec python3 "$D/inv.py" "$@"
