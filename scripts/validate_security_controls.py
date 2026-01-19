import yaml
import sys
import os

# Configuration
CONTROLS_FILE = "security-controls.yaml"
FEATURES_ENV = "features.env"

def fail(message):
    """Prints error to stderr and exits with failure code."""
    print(f"POLICY GATE FAILED: {message}", file=sys.stderr)
    sys.exit(1)

# Helper to safely navigate the nested dict and return a boolean
def get_control_bool(data, path):
    keys = path.split('.')
    val = data
    for key in keys:
        if isinstance(val, dict):
            val = val.get(key, False)
        else:
            return False
    return bool(val)

def main():
    # 1) Enforce controls file existence
    if not os.path.isfile(CONTROLS_FILE):
        fail(f"A security-controls file MUST exist in the repository. Expected: {CONTROLS_FILE}")

    # Load YAML data
    try:
        with open(CONTROLS_FILE, "r") as f:
            data = yaml.safe_load(f) or {}
    except yaml.YAMLError as exc:
        fail(f"Error parsing {CONTROLS_FILE}: {exc}")

    # Extract configuration values
    enable_waf = get_control_bool(data, "controls.waf.enabled")
    enable_api_discovery = get_control_bool(data, "controls.api_discovery.enabled")
    enable_bot_advanced = get_control_bool(data, "controls.bot_advanced.enabled")
    enable_rate_limiting = get_control_bool(data, "controls.rate_limiting.enabled")

    # 2) Enforce WAF must be enabled (Minimum security)
    if not enable_waf:
        fail(f"WAF must be enabled as the minimum application security baseline. Set controls.waf.enabled: true in {CONTROLS_FILE}")

    # 3) If API discovery enabled, enforce openapi exists
    if enable_api_discovery:
        if not os.path.isfile("openapi/openapi.json"):
            fail("API discovery is enabled, but openapi/openapi.json is missing.")

    # 4) If advanced BOT enabled, enforce templates exist
    if enable_bot_advanced:
        required_templates = ["app/templates/login.html", "app/templates/contact.html"]
        missing_templates = []
        for template in required_templates:
            if not os.path.isfile(template):
                missing_templates.append(template)
        if len(missing_templates) > 0:
            fail(f"Advanced BOT protection is enabled, but {', '.join(missing_templates)} {"are" if len(missing_templates) > 1 else 'is'} missing.")

    # Export dotenv for downstream stages
    try:
        with open(FEATURES_ENV, "w") as f:
            f.write(f"ENABLE_WAF={str(enable_waf).lower()}\n")
            f.write(f"ENABLE_API_DISCOVERY={str(enable_api_discovery).lower()}\n")
            f.write(f"ENABLE_BOT_ADVANCED={str(enable_bot_advanced).lower()}\n")
            f.write(f"ENABLE_RATE_LIMITING={str(enable_rate_limiting).lower()}\n")
        print(f"Success: {FEATURES_ENV} generated.")
    except IOError as e:
        fail(f"Could not write to {FEATURES_ENV}: {e}")

if __name__ == "__main__":
    main()
 