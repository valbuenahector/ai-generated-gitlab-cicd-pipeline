import os
import sys
import yaml

CONTROLS_FILE = "security-controls.yaml"
FEATURES_ENV = "features.env"

def fail(message):
    print(f"POLICY GATE FAILED: {message}", file=sys.stderr)
    sys.exit(1)

def validate_controls():
    # 1. Enforce existence of security-controls.yaml
    if not os.path.exists(CONTROLS_FILE):
        fail("A security-controls file MUST exist in the repository for the Application to be published.")

    try:
        with open(CONTROLS_FILE, 'r') as f:
            data = yaml.safe_load(f) or {}
    except Exception as e:
        fail(f"Failed to parse {CONTROLS_FILE}: {e}")

    # 2. Extract settings
    controls = data.get('controls', {})
    
    # 7. ANY other combination of setting on the security-controls.yaml is not supported.
    # We validate that only known keys exist in 'controls'
    supported_keys = {'waf', 'api_discovery', 'bot_advanced', 'rate_limiting'}
    actual_keys = set(controls.keys())
    if not actual_keys.issubset(supported_keys):
        unsupported = actual_keys - supported_keys
        fail(f"Unsupported security controls found: {unsupported}. Only WAF, API discovery, Advanced BOT protection, and Rate limiting are supported.")

    waf = controls.get('waf', {})
    api_discovery = controls.get('api_discovery', {})
    bot_advanced = controls.get('bot_advanced', {})
    rate_limiting = controls.get('rate_limiting', {})

    enable_waf = waf.get('enabled', False)
    enable_api_discovery = api_discovery.get('enabled', False)
    enable_bot_advanced = bot_advanced.get('enabled', False)
    enable_rate_limiting = rate_limiting.get('enabled', False)

    # 3. Enforce WAF setting MUST be enabled
    if not enable_waf:
        fail("WAF must be enabled as the minimum application security baseline. Set controls.waf.enabled: true in security-controls.yaml")

    # 5. If API discovery is enabled, enforce presence of openapi/openapi.json
    if enable_api_discovery:
        if not os.path.isfile("openapi/openapi.json"):
            fail("API discovery is enabled, but openapi/openapi.json is missing. Provide the OpenAPI spec at openapi/openapi.json")

    # 6. If advance BOT protection is enabled, enforce presence of templates
    if enable_bot_advanced:
        if not os.path.isfile("app/templates/login.html"):
            fail("Advanced BOT protection is enabled, but app/templates/login.html is missing.")
        if not os.path.isfile("app/templates/contact.html"):
            fail("Advanced BOT protection is enabled, but app/templates/contact.html is missing.")

    # Write features.env
    with open(FEATURES_ENV, 'w') as f:
        f.write(f"ENABLE_WAF={str(enable_waf).lower()}\n")
        f.write(f"ENABLE_API_DISCOVERY={str(enable_api_discovery).lower()}\n")
        f.write(f"ENABLE_BOT_ADVANCED={str(enable_bot_advanced).lower()}\n")
        f.write(f"ENABLE_RATE_LIMITING={str(enable_rate_limiting).lower()}\n")

    print("Security controls validated successfully.")

if __name__ == "__main__":
    validate_controls()
