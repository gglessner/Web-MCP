#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

case "${1:-}" in
  parley) DIR="MCPs/parley-mcp"; URL="https://github.com/gglessner/Parley-MCP" ;;
  github) DIR="MCPs/github-mcp"; URL="https://github.com/gglessner/github-MCP" ;;
  *) echo "usage: $0 <parley|github>" >&2; exit 1 ;;
esac

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
git clone --depth 1 "$URL" "$TMP/upstream"
SHA=$(cd "$TMP/upstream" && git rev-parse HEAD)

find "$DIR" -mindepth 1 -maxdepth 1 ! -name 'UPSTREAM.txt' -exec rm -rf {} +
cp -r "$TMP/upstream/." "$DIR/"
rm -rf "$DIR/.git"

{
  echo "upstream: $URL"
  echo "pinned_commit: $SHA"
  date -u +"pinned_at: %Y-%m-%dT%H:%M:%SZ"
} > "$DIR/UPSTREAM.txt"

echo "Updated $DIR to $SHA. Reinstall deps and review the diff before committing."
