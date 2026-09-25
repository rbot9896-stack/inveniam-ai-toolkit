#!/usr/bin/env bash
# Thin wrapper: the puller is tools/fetch_deal.py (cross-platform). Same usage:
#   INV_ENV=sales bash tools/fetch_deal.sh "The Meridian"
D="$(cd "$(dirname "$0")" && pwd)"
exec python3 "$D/fetch_deal.py" "$@"
