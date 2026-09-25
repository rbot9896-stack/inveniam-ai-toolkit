#!/usr/bin/env python3
"""Inveniam API helper — cross-platform (Mac, Windows, Linux), standard library only.

    python3 inv.py GET "/v2/deals?page=1&limit=10"                 # production  (.env)
    INV_ENV=sales python3 inv.py GET "/v2/deals?limit=10"           # sales       (.env.sales)
    python3 inv.py --env sales GET "/v2/deals?limit=10"             # same, without an env var
    python3 inv.py POST /v2/dataroom/file-veracity/initiate -d '{"fileId":"..."}'
    python3 inv.py GET /v2/dataroom/download-file/<id> -o file.pdf

Options (curl-compatible where it matters):
    --env NAME      credentials set: prod (default) -> .env, anything else -> .env.NAME
    -H "k: v"       extra header (repeatable)
    -d DATA         request body (JSON string, or @file); sets content-type: application/json
    -o FILE         write the response body to FILE instead of stdout
    -X METHOD       alternative to giving the method positionally

Credentials come from a .env file beside this script (or in $INV_HOME if set):
    INVENIAM_API_KEY, INVENIAM_API_TOKEN, INVENIAM_BASE_URL
The short-lived JWT is cached in the system temp folder for 50 minutes per environment.
Exit status 0 on HTTP 2xx, 22 on other HTTP statuses (like curl -f), 1 on setup errors.
On Windows, use `python` (or `py`) in place of `python3`.
"""
import json, os, sys, time, tempfile, urllib.request, urllib.error

ROOT = os.environ.get("INV_HOME") or os.path.dirname(os.path.abspath(__file__))


def load_env(envname):
    f = os.path.join(ROOT, ".env" if envname == "prod" else f".env.{envname}")
    if not os.path.isfile(f):
        sys.exit(f"No credentials file: {f}")
    cfg = {}
    for line in open(f, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        cfg[k.strip()] = v.strip().strip('"').strip("'")
    for k in ("INVENIAM_API_KEY", "INVENIAM_API_TOKEN", "INVENIAM_BASE_URL"):
        if not cfg.get(k):
            sys.exit(f"{k} missing in {f}")
    cfg["INVENIAM_BASE_URL"] = cfg["INVENIAM_BASE_URL"].rstrip("/")
    return cfg


def jwt(cfg, envname):
    cache = os.path.join(tempfile.gettempdir(), f".inveniam_jwt.{envname}")
    try:
        if os.path.getsize(cache) > 0 and time.time() - os.path.getmtime(cache) < 3000:
            return open(cache, encoding="utf-8").read().strip()
    except OSError:
        pass
    req = urllib.request.Request(cfg["INVENIAM_BASE_URL"] + "/v2/api-keys/auth/token",
                                 headers={"x-api-key": cfg["INVENIAM_API_KEY"],
                                          "Authorization": cfg["INVENIAM_API_TOKEN"]})
    with urllib.request.urlopen(req, timeout=60) as r:
        d = json.load(r)
    d = d.get("data", d)
    tok = d.get("token") or d.get("accessToken") or d.get("access_token")
    if not tok:
        sys.exit("auth response had no token")
    fd = os.open(cache, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(tok)
    return tok


def call(method, path, envname="prod", headers=None, data=None, timeout=120):
    """Return (status, body_bytes). Importable: from inv import call."""
    cfg = load_env(envname)
    h = {"x-api-key": cfg["INVENIAM_API_KEY"], "Authorization": "Bearer " + jwt(cfg, envname)}
    if headers:
        h.update(headers)
    body = None
    if data is not None:
        body = data if isinstance(data, bytes) else data.encode("utf-8")
        h.setdefault("content-type", "application/json")
    req = urllib.request.Request(cfg["INVENIAM_BASE_URL"] + path, data=body, method=method.upper(), headers=h)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def get_json(path, envname="prod", **kw):
    status, body = call("GET", path, envname, **kw)
    if status // 100 != 2:
        raise RuntimeError(f"HTTP {status} for {path}: {body[:300]!r}")
    if not body.strip():
        raise RuntimeError(f"empty body for {path}")
    return json.loads(body)


def main(argv):
    envname = os.environ.get("INV_ENV", "prod")
    headers, data, out, method, path = {}, None, None, None, None
    a = list(argv)
    while a:
        x = a.pop(0)
        if x == "--env": envname = a.pop(0)
        elif x == "-H":
            k, v = a.pop(0).split(":", 1); headers[k.strip()] = v.strip()
        elif x == "-d":
            data = a.pop(0)
            if data.startswith("@"): data = open(data[1:], "rb").read()
        elif x == "-o": out = a.pop(0)
        elif x == "-X": method = a.pop(0)
        elif x in ("-s", "-S", "-f", "-sS", "-sf"): pass          # curl flags callers may still pass
        elif method is None and x.upper() in ("GET", "POST", "PUT", "PATCH", "DELETE"): method = x
        elif path is None: path = x
        else: sys.exit(f"unexpected argument: {x}")
    if not method or not path:
        sys.exit(__doc__)
    status, body = call(method, path, envname, headers, data)
    if out:
        open(out, "wb").write(body)
    else:
        sys.stdout.buffer.write(body)
        if body and not body.endswith(b"\n"): sys.stdout.buffer.write(b"\n")
    return 0 if status // 100 == 2 else 22


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
