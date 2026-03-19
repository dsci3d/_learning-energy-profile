#!/bin/bash
set -o pipefail
cd "$CLAUDE_PROJECT_DIR"
BRIEFER="$HOME/.briefer"
OUTPUT=$($BRIEFER/.venv/bin/python3 $BRIEFER/indexer.py . 2>&1 | tail -1)
BRIEFER_RULES=rules.yaml $BRIEFER/.venv/bin/python3 $BRIEFER/resolver.py --load-rules > /dev/null 2>&1
echo "$OUTPUT"
