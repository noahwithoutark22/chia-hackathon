#!/usr/bin/env bash
# Add a new LLM API key to the fallback pool, end to end. Replaces the
# manual process of hand-editing opencode.jsonc in 3 places (host + 2
# containers) and llm_models.txt -- easy to get wrong (wrong provider slot,
# forgetting a container, adding an untested model to the live fallback
# list) when done by hand.
#
# Usage:
#   uvm_loop/scripts/add_llm_provider.sh <base_url> <api_key> <model_name> [slug]
#
# Example (an NVIDIA build.nvidia.com key):
#   uvm_loop/scripts/add_llm_provider.sh \
#     https://integrate.api.nvidia.com/v1 \
#     nvapi-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx \
#     openai/gpt-oss-20b
#
# What it does:
#   1. Picks the next free "nvidiaN" provider slot (or use `slug` to name it explicitly).
#   2. Registers it in ~/.config/opencode/opencode.jsonc.
#   3. Copies that config into every running opencode worker container (opencode.jsonc is
#      NOT bind-mounted from the host, unlike auth.json -- edits don't reach the container
#      any other way).
#   4. Smoke-tests it live with a trivial prompt (timeout 90s, one retry on timeout --
#      some models are just slow on a cold first call).
#   5. Only on success: appends `<slug>/<model_name>` to config/llm_models.txt so it's
#      actually used. On failure, the provider stays registered (for later re-testing)
#      but is NOT added to the live fallback list.
set -euo pipefail

if [[ $# -lt 3 || $# -gt 4 ]]; then
    echo "Usage: $0 <base_url> <api_key> <model_name> [slug]" >&2
    exit 2
fi

BASE_URL="$1"
API_KEY="$2"
MODEL_NAME="$3"
SLUG="${4:-}"
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
OC_CONFIG="$HOME/.config/opencode/opencode.jsonc"
LLM_MODELS_TXT="$REPO/uvm_loop/config/llm_models.txt"

[[ -f "$OC_CONFIG" ]] || { echo "ERROR: $OC_CONFIG not found. Set up opencode first." >&2; exit 1; }

if [[ -z "$SLUG" ]]; then
    SLUG=$(python3 - "$OC_CONFIG" <<'EOF'
import re, sys
text = open(sys.argv[1]).read()
existing = [int(m) for m in re.findall(r'"nvidia(\d+)"', text)]
print(f"nvidia{max(existing) + 1 if existing else 2}")
EOF
)
fi

echo "Registering provider '$SLUG' -> $MODEL_NAME @ $BASE_URL"

python3 - "$OC_CONFIG" "$SLUG" "$BASE_URL" "$API_KEY" "$MODEL_NAME" <<'EOF'
import sys, re
path, slug, base_url, api_key, model_name = sys.argv[1:6]
text = open(path).read()
if f'"{slug}"' in text:
    print(f"ERROR: provider '{slug}' already registered in {path}", file=sys.stderr)
    sys.exit(1)

entry = f'''    "{slug}": {{
      "npm": "@ai-sdk/openai-compatible",
      "options": {{
        "baseURL": "{base_url}",
        "apiKey": "{api_key}"
      }},
      "models": {{ "{model_name}": {{}} }}
    }},
'''
marker = '  "provider": {\n'
idx = text.index(marker) + len(marker)
text = text[:idx] + entry + text[idx:]
open(path, 'w').write(text)
print(f"added to {path}")
EOF

# Push into every running opencode worker container (path is not bind-mounted).
CONTAINERS=$(docker ps --format '{{.Names}}' | grep -i opencode || true)
if [[ -z "$CONTAINERS" ]]; then
    echo "WARNING: no running opencode containers found (docker ps | grep opencode) -- skipping container sync."
else
    for c in $CONTAINERS; do
        docker cp "$OC_CONFIG" "$c:/home/ray/.config/opencode/opencode.jsonc"
        echo "synced to container: $c"
    done
fi

# Smoke test.
TEST_CONTAINER=$(echo "$CONTAINERS" | head -1)
if [[ -z "$TEST_CONTAINER" ]]; then
    echo "No container to smoke-test against. Registered but NOT added to $LLM_MODELS_TXT -- test manually first."
    exit 1
fi

echo "Smoke-testing $SLUG/$MODEL_NAME (up to 2 attempts, 90s each)..."
OK=0
for attempt in 1 2; do
    if docker exec "$TEST_CONTAINER" timeout 90 opencode run -m "$SLUG/$MODEL_NAME" "reply with exactly: PONG" 2>&1 | grep -q PONG; then
        OK=1
        break
    fi
    echo "  attempt $attempt failed, retrying..."
done

if [[ "$OK" -eq 1 ]]; then
    LINE="$SLUG/$MODEL_NAME"
    if grep -qxF "$LINE" "$LLM_MODELS_TXT" 2>/dev/null; then
        echo "$LINE already present in $LLM_MODELS_TXT"
    else
        echo "$LINE" >> "$LLM_MODELS_TXT"
        echo "Added to fallback pool: $LINE"
    fi
    echo "SUCCESS: $SLUG is live and in the fallback list."
else
    echo "FAILED both smoke-test attempts. Provider '$SLUG' stays registered in opencode.jsonc"
    echo "for later re-testing, but was NOT added to $LLM_MODELS_TXT."
    exit 1
fi
