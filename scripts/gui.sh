#!/usr/bin/env bash
set -euo pipefail

# gui.sh: wrapper for the ICM GUI server
# Usage: gui.sh [--demo] [--as LOGIN] [--port N] [--check]

DEMO=false
LOGIN=""
PORT=8765
CHECK=false
DEMO_DIR=""
CLEANUP_DEMO=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --demo)
            DEMO=true
            shift
            ;;
        --as)
            LOGIN="$2"
            shift 2
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        --check)
            CHECK=true
            shift
            ;;
        *)
            echo "Unknown option: $1" >&2
            exit 1
            ;;
    esac
done

# Determine root and project directories
if [ "$DEMO" = true ]; then
    DEMO_DIR=$(mktemp -d)
    CLEANUP_DEMO=true
    cp -r gui/fixtures/demo/* "$DEMO_DIR/"
    ROOT="$DEMO_DIR"
    PROJECT="$DEMO_DIR/icm-project"
else
    ROOT=$(dirname "$(pwd)/scripts")
    PROJECT="$ROOT/../icm-project"
fi

# Clean up demo directory on exit
cleanup() {
    if [ "$CLEANUP_DEMO" = true ] && [ -n "$DEMO_DIR" ] && [ -d "$DEMO_DIR" ]; then
        rm -rf "$DEMO_DIR"
    fi
}
trap cleanup EXIT

# Determine login
if [ -z "$LOGIN" ]; then
    if command -v gh &> /dev/null; then
        LOGIN=$(gh api user --jq .login) || {
            echo "Error: --as required when gh cli is not available" >&2
            exit 1
        }
    else
        echo "Error: --as required when gh cli is not available" >&2
        exit 1
    fi
fi

# Look up role in people.md
if [ ! -f "$PROJECT/people.md" ]; then
    echo "Error: people.md not found at $PROJECT/people.md" >&2
    exit 1
fi

ROLE=$(grep "^| $LOGIN |" "$PROJECT/people.md" | awk -F'|' '{print $3}' | tr -d ' ' || true)
if [ -z "$ROLE" ]; then
    echo "Error: unknown login '$LOGIN'" >&2
    exit 1
fi

IDENTITY="$ROLE:$LOGIN"

if [ "$CHECK" = true ]; then
    # Start server in background
    python3 gui/server.py --root "$ROOT" --project "$PROJECT" --as "$IDENTITY" --port "$PORT" &
    SERVER_PID=$!

    # Wait for server to start and poll /pipeline
    MAX_ATTEMPTS=5
    ATTEMPT=0
    HTTP_STATUS=0

    while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
        sleep 1
        HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:$PORT/pipeline" 2>/dev/null || true)
        if [ "$HTTP_STATUS" = "200" ]; then
            break
        fi
        ATTEMPT=$((ATTEMPT + 1))
    done

    # Kill server
    if kill $SERVER_PID 2>/dev/null; then
        wait $SERVER_PID 2>/dev/null || true
    fi

    if [ "$HTTP_STATUS" = "200" ]; then
        exit 0
    else
        exit 1
    fi
else
    # Run server in foreground
    exec python3 gui/server.py --root "$ROOT" --project "$PROJECT" --as "$IDENTITY" --port "$PORT"
fi
