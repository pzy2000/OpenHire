"""OpenHands adapter is intentionally disabled.

The previous OpenHands Docker adapter is no longer registered or callable. Keep
this module as a disabled marker so old references have a clear place to land,
without exposing an active OpenHandsAdapter implementation.
"""

# OpenHands is intentionally disabled across OpenHire.
#
# Previous active implementation, including:
# - class OpenHandsAdapter(DockerAgent)
# - OpenHands Docker image docker.openhands.dev/openhands/openhands:1.6
# - /app/.venv/bin/python -m openhands.core.main execution
# - /.openhands/sessions error monitoring
# - localhost LLM_BASE_URL rewriting
#
# is commented out by policy. Re-enable only by restoring the adapter and adding
# it back to build_default_registry().
