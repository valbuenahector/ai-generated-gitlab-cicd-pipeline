# scripts/validate_security_controls.sh
#
# Validates security-controls.yaml against lab policy and exports features.env
# Policy:
# 1) security-controls.yaml MUST exist
# 2) WAF MUST be enabled (minimum security)
# 3) API discovery optional; if enabled require openapi/openapi.json
# 4) Advanced BOT optional; if enabled require:
#    - app/templates/login.html
#    - app/templates/contact.html
# 5) Rate limiting optional
#
# Output: features.env (dotenv)
#   ENABLE_WAF=true/false
#   ENABLE_API_DISCOVERY=true/false
#   ENABLE_BOT_ADVANCED=true/false
#   ENABLE_RATE_LIMITING=true/false

set -euo pipefail

CONTROLS_FILE="security-controls.yaml"
FEATURES_ENV="features.env"

fail() {
  echo "POLICY GATE FAILED: $1" >&2
  exit 1
}

# 1) Enforce controls file existence
if [ ! -f "$CONTROLS_FILE" ]; then
  fail "A security-controls file MUST exist in the repository for the application to be published. Expected: ${CONTROLS_FILE}"
fi

# Prefer yq if present, otherwise fall back to python YAML parser (recommended).
# For a SHELL runner, you can preinstall python3 + pyyaml, OR install yq.
have_cmd() { command -v "$1" >/dev/null 2>&1; }

read_bool_yq() {
  local query="$1"
  # yq returns "true/false/null"
  yq -r "$query // \"false\"" "$CONTROLS_FILE" 2>/dev/null || echo "false"
}

read_bool_py() {
  local keypath="$1"  # e.g. controls.waf.enabled
  python3 - <<PY
import sys, yaml
p="$keypath".split(".")
with open("$CONTROLS_FILE","r") as f:
    data=yaml.safe_load(f) or {}
cur=data
for k in p:
    cur = cur.get(k, {}) if isinstance(cur, dict) else {}
val = cur if isinstance(cur, bool) else False
print("true" if val else "false")
PY
}

read_bool() {
  local keypath="$1"
  if have_cmd yq; then
    # Convert keypath to yq query: .controls.waf.enabled
    local q=".$(echo "$keypath" | sed 's/\./\./g')"
    read_bool_yq "$q"
  else
    # Requires python3 + PyYAML available on the runner
    have_cmd python3 || fail "python3 is required on the shell runner (or install yq) to parse ${CONTROLS_FILE}"
    python3 -c "import yaml" >/dev/null 2>&1 || fail "PyYAML is required on the shell runner (pip install pyyaml) or install yq"
    read_bool_py "$keypath"
  fi
}

ENABLE_WAF="$(read_bool controls.waf.enabled)"
ENABLE_API_DISCOVERY="$(read_bool controls.api_discovery.enabled)"
ENABLE_BOT_ADVANCED="$(read_bool controls.bot_advanced.enabled)"
ENABLE_RATE_LIMITING="$(read_bool controls.rate_limiting.enabled)"

# 3) Enforce WAF must be enabled
if [ "$ENABLE_WAF" != "true" ]; then
  fail "WAF must be enabled as the minimum application security baseline. Set controls.waf.enabled: true in ${CONTROLS_FILE}"
fi

# 5) If API discovery enabled, enforce openapi exists
if [ "$ENABLE_API_DISCOVERY" = "true" ]; then
  if [ ! -f "openapi/openapi.json" ]; then
    fail "API discovery is enabled, but openapi/openapi.json is missing. Provide the OpenAPI spec at openapi/openapi.json"
  fi
fi

# 6) If advanced BOT enabled, enforce templates exist
if [ "$ENABLE_BOT_ADVANCED" = "true" ]; then
  [ -f "app/templates/login.html" ]   || fail "Advanced BOT protection is enabled, but app/templates/login.html is missing."
  [ -f "app/templates/contact.html" ] || fail "Advanced BOT protection is enabled, but app/templates/contact.html is missing."
fi

# Export dotenv for downstream stages
cat > "$FEATURES_ENV" <<EOF
ENABLE_WAF=${ENABLE_WAF}
ENABLE_API_DISCOVERY=${ENABLE_API_DISCOVERY}
ENABLE_BOT_ADVANCED=${ENABLE_BOT_ADVANCED}
ENABLE_RATE_LIMITING=${ENABLE_RATE_LIMITING}
EOF
