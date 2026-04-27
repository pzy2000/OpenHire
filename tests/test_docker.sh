#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.." || exit 1

IMAGE_NAME="openhire-test"
CONTAINER_NAME="openhire-test-run"
ONBOARDED_IMAGE="openhire-test-onboarded"

cleanup() {
    docker rm -f "$CONTAINER_NAME" 2>/dev/null || true
    docker rmi -f "$ONBOARDED_IMAGE" 2>/dev/null || true
    docker rmi -f "$IMAGE_NAME" 2>/dev/null || true
}

cleanup
trap cleanup EXIT

echo "=== Building Docker image ==="
docker build -t "$IMAGE_NAME" .

echo ""
echo "=== Running 'openhire onboard' ==="
docker run --name "$CONTAINER_NAME" "$IMAGE_NAME" onboard

echo ""
echo "=== Running 'openhire status' ==="
STATUS_OUTPUT=$(docker commit "$CONTAINER_NAME" "$ONBOARDED_IMAGE" > /dev/null && \
    docker run --rm "$ONBOARDED_IMAGE" status 2>&1) || true

echo "$STATUS_OUTPUT"

echo ""
echo "=== Validating output ==="
PASS=true

check() {
    if echo "$STATUS_OUTPUT" | grep -q "$1"; then
        echo "  PASS: found '$1'"
    else
        echo "  FAIL: missing '$1'"
        PASS=false
    fi
}

check "OpenHire Status"
check "Config:"
check "Workspace:"
check "Model:"
check "OpenRouter:"
check "Anthropic:"
check "OpenAI:"

echo ""
if $PASS; then
    echo "=== All checks passed ==="
else
    echo "=== Some checks FAILED ==="
    exit 1
fi

# Cleanup
echo ""
echo "=== Cleanup ==="
cleanup
trap - EXIT
echo "Done."
