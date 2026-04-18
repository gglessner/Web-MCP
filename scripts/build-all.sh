#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
. .venv/bin/activate
pip install --upgrade pip -q
pip install -q -r requirements.txt
pip install -q -e ".[dev]"
pip install -q -e MCPs/browser-mcp
pip install -q -e MCPs/burp-mcp
pip install -q -r MCPs/parley-mcp/requirements.txt
[ -f MCPs/github-mcp/requirements.txt ] && pip install -q -r MCPs/github-mcp/requirements.txt
[ -f MCPs/github-mcp/MCPs/libs/mcp_armor/requirements.txt ] && \
  pip install -q -r MCPs/github-mcp/MCPs/libs/mcp_armor/requirements.txt

( cd MCPs/burp-mcp/burp-ext && ./gradlew shadowJar )

pytest -q
echo "build-all: OK"
