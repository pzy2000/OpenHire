#!/bin/sh
dir="$HOME/.openhire"
if [ -d "$dir" ] && [ ! -w "$dir" ]; then
    owner_uid=$(stat -c %u "$dir" 2>/dev/null || stat -f %u "$dir" 2>/dev/null)
    cat >&2 <<EOF
Error: $dir is not writable (owned by UID $owner_uid, running as UID $(id -u)).

Fix (pick one):
  Host:   sudo chown -R 1000:1000 ~/.openhire
  Docker: docker run --user \$(id -u):\$(id -g) ...
  Podman: podman run --userns=keep-id ...
EOF
    exit 1
fi

if [ "$1" = "gateway" ] && [ ! -f "$dir/config.json" ]; then
    mkdir -p "$dir"
    cat > "$dir/config.json" <<EOF
{
  "agents": {
    "defaults": {
      "workspace": "$dir/workspace",
      "model": "ollama/llama3.2"
    }
  },
  "gateway": {
    "host": "0.0.0.0",
    "port": 7860
  }
}
EOF
fi

exec openhire "$@"
