# AI Generated GitLab CI/CD Pipeline for F5 AppWorld Lab

This repository contains a reference implementation of a GitLab CI/CD pipeline for the F5 AppWorld Lab "Code, Secure and Repeat".

## Requirements

The pipeline is designed to meet the following security and operational requirements:

- **Stages**: `policy_gate`, `test`, `build`, `deploy`.
- **Policy Gate**:
    - Enforces the existence of `security-controls.yaml`.
    - Validates that WAF is **enabled** (minimum security requirement).
    - Checks for mandatory files if optional controls are enabled:
        - If `api_discovery` is enabled, `openapi/openapi.json` must exist.
        - If `bot_advanced` is enabled, `app/templates/login.html` and `app/templates/contact.html` must exist.
- **Validation Script**: `scripts/validate_security_controls.sh` validates the configuration and exports `features.env` for downstream stages.

## File Structure

- `.gitlab-ci.yml`: Pipeline definition.
- `security-controls.yaml`: Security configuration for the application.
- `scripts/validate_security_controls.sh`: Security policy enforcement script.
- `app/templates/`: Application HTML templates.
- `openapi/`: API documentation.
- `terraform/`: Infrastructure as Code for deployment.

## Prompt Used

The initial prompt used to generate this pipeline was:
> "AI generated Gitlab CI/CD pipeline for F5 AppWorld lab Code, Secure and Repeat to meet the following requirements:
> - stages: policy_gate,test,build,deploy
> - Script to validate_security_controls.sh the security-controls.yaml with minimal schema and export to features.env
> - policy_gate stage should follow the criteria i have described:
>   1.- Enforce the existence of security-controls.txt (or JSON or YAML). If file does not exists CI/CD pipeline with error like but more formal \"A security-controls file MUST exists in the repo (or gitlab project) for the Application to be published\"
>   2.- security-controls file will contian setting for WAF, API discovery, Advance BOT protection and Rate limiting
>   3.- Enforce the WAF setting MUST be enabled (minumun app security)
>   4.- API discovery, advance BOT protection and Rate limiting are optional security controls
>   5.- If API discovery is enabled. Enforce the present of openapi/openapi.json
>   6.- If advance BOT protection is enabled Enforce the present of app/templates/login.html and app/templates/contact.html"

## Usage

1. Modify `security-controls.yaml` to toggle security features.
2. Ensure required files are present in the repository before pushing.
3. Observe the `policy_gate` stage in the GitLab CI/CD pipeline.
