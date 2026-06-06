#!/usr/bin/env bash
# Example shell script run from a GitHub Actions workflow.
# Takes the Behave tag as the first argument and prints the commands
# a real pipeline would run. Uses strict mode for safe failures.
set -euo pipefail

TAG="${1:-smoke}"

echo "run-checks.sh starting"
echo "Behave tag: ${TAG}"

echo "Step 1: static analysis"
echo "  pylint your-solution-root-folder-name/ --exit-zero"

echo "Step 2: BDD suite"
echo "  behave --tags=${TAG} --no-capture"

echo "run-checks.sh completed successfully"
