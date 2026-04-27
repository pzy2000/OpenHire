#!/usr/bin/env python3
"""Minimal repro for POST /admin/api/companion/chat (no auth in default app).

Usage:
  OPENHIRE_URL=http://127.0.0.1:PORT python scripts/repro_companion_chat.py

Optional:
  COMPANION_MSG='your text' OPENHIRE_URL=... python scripts/repro_companion_chat.py

curl equivalent:
  curl -sS -X POST "$OPENHIRE_URL/admin/api/companion/chat" \\
    -H 'Content-Type: application/json' \\
    -d '{"messages":[{"role":"user","content":"..."}]}'
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

DEFAULT_URL = "http://127.0.0.1:8787"
URL = os.environ.get("OPENHIRE_URL", DEFAULT_URL).rstrip("/")
MSG = os.environ.get(
    "COMPANION_MSG",
    "请用 2 句话总结当前 OpenHire 管理后台运行态，并指出最重要的状态信号。",
)


def main() -> int:
    body = json.dumps(
        {"messages": [{"role": "user", "content": MSG}]},
        ensure_ascii=False,
    ).encode("utf-8")
    req = urllib.request.Request(
        f"{URL}/admin/api/companion/chat",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = resp.read().decode()
            print(f"HTTP {resp.status}")
            print(raw)
            try:
                data = json.loads(raw)
                content = data.get("content")
                print(f"\ncontent repr: {content!r}  len={len(content) if isinstance(content, str) else 'n/a'}")
            except json.JSONDecodeError:
                pass
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code}", file=sys.stderr)
        print(e.read().decode(errors="replace"), file=sys.stderr)
        return 1
    except OSError as e:
        print(f"Request failed: {e}", file=sys.stderr)
        print(f"Set OPENHIRE_URL to your gateway admin URL (default tried {DEFAULT_URL}).", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
