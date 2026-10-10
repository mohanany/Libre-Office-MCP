#!/usr/bin/env bash
# Build libreoffice-mcp-bridge.oxt (a zip) from extension/
set -euo pipefail
cd "$(dirname "$0")/../extension"
out="../dist/libreoffice-mcp-bridge.oxt"
mkdir -p ../dist
rm -f "$out"
zip -r "$out" . -x '*.pyc' -x '__pycache__/*'
echo "built $out"
