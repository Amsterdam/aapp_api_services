#!/usr/bin/env bash

set -euo pipefail

service_name="${SERVICE_NAME:-}"
all_services="${ALL_SERVICES:-}"

if [[ -z "$service_name" || "$service_name" == "core" ]]; then
    echo "ERROR: SERVICE_NAME is not set"
    exit 1
fi

if [[ " $all_services " != *" $service_name "* ]]; then
    echo "ERROR: SERVICE_NAME must be one of: $all_services"
    exit 1
fi

mkdir -p .vscode

test_env_file=".vscode/.env.test.${service_name}"
settings_template=".vscode/settings.template.json"
launch_template=".vscode/launch.template.json"

if [[ ! -f "$test_env_file" ]]; then
    echo "ERROR: $test_env_file does not exist"
    exit 1
fi

if [[ ! -f ".vscode/settings.json" ]]; then
    if [[ ! -f "$settings_template" ]]; then
        echo "ERROR: $settings_template does not exist"
        exit 1
    fi
    cp "$settings_template" .vscode/settings.json
fi

if [[ ! -f ".vscode/launch.json" ]]; then
    if [[ ! -f "$launch_template" ]]; then
        echo "ERROR: $launch_template does not exist"
        exit 1
    fi
    cp "$launch_template" .vscode/launch.json
fi

perl -0pi -e 's/"python\.testing\.pytestArgs": \[\s*"[^"]+"\s*\]/"python.testing.pytestArgs": [\n    "'"$service_name"'"\n  ]/s; s/\.env\.test\.[^"]+/.env.test.'"$service_name"'/' .vscode/settings.json
perl -0pi -e 's/"name": "Pytest: current file \([^"]+\)"/"name": "Pytest: current file ('"$service_name"')"/; s/\.env\.test\.[^"]+/.env.test.'"$service_name"'/' .vscode/launch.json

echo "VS Code test service switched to $service_name. Refresh tests in the Testing view."