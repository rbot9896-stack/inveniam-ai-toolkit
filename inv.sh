#!/usr/bin/env bash
# Inveniam API helper.
#   ./inv.sh GET /v2/path [curl args...]            -> uses .env          (prod)
#   INV_ENV=sales ./inv.sh GET /v2/path [curl args] -> uses .env.sales
# Each .env file holds INVENIAM_API_KEY, INVENIAM_API_TOKEN, INVENIAM_BASE_URL.
# The short-lived JWT is cached per environment for 50 minutes.
set -euo pipefail
D="$(cd "$(dirname "$0")" && pwd)"
ENVN="${INV_ENV:-prod}"
[ "$ENVN" = "prod" ] && F="$D/.env" || F="$D/.env.$ENVN"
[ -f "$F" ] || { echo "No credentials file: $F" >&2; exit 1; }
set -a; . "$F"; set +a
: "${INVENIAM_API_KEY:?missing in $F}"; : "${INVENIAM_API_TOKEN:?missing in $F}"; : "${INVENIAM_BASE_URL:?missing in $F}"
C="${TMPDIR:-/tmp}/.inveniam_jwt.$ENVN"
if [ ! -s "$C" ] || [ $(( $(date +%s) - $(stat -c %Y "$C" 2>/dev/null || stat -f %m "$C") )) -gt 3000 ]; then
  R=$(curl -sf "$INVENIAM_BASE_URL/v2/api-keys/auth/token" -H "x-api-key: $INVENIAM_API_KEY" -H "Authorization: $INVENIAM_API_TOKEN")
  echo "$R" | python3 -c 'import sys,json;d=json.load(sys.stdin);d=d.get("data",d);print(d.get("token") or d.get("accessToken") or d.get("access_token"))' > "$C"
  chmod 600 "$C"
fi
M="$1"; P="$2"; shift 2
curl -sS -X "$M" "$INVENIAM_BASE_URL$P" -H "x-api-key: $INVENIAM_API_KEY" -H "Authorization: Bearer $(cat "$C")" "$@"
