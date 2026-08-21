#!/usr/bin/env bash
# Sprakkontroll for ai-skiftet.se. Fallerar (exit 1) vid spraklackage.
# Kors som BLOCKERANDE steg fore publicering.
#
#   bash tools/sprakkontroll/verifiera.sh            # arbetskopian
#   bash tools/sprakkontroll/verifiera.sh --live     # publicerade sidor
#   bash tools/sprakkontroll/verifiera.sh index.html no/index.html
set -euo pipefail
cd "$(dirname "$0")/../.."
exec python3 tools/sprakkontroll/check_language.py "$@"
