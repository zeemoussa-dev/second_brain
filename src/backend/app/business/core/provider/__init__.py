"""Provider entity -- a real LLM credential source (endpoint/model/
credential) Second Brain knows about, kept for a not-yet-built future
use (provisioning a brand-new Hermes install with known-good provider
credentials), not for live per-agent selection -- Hermes owns that
directly now. ProviderManager (2026-08-28) is the sole gateway onto
this data; see provider.py for the shape, provider_manager.py for
ProviderManager itself.
"""
