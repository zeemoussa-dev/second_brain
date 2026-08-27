class HermesUnavailableError(Exception):
    """Hermes did not respond, or responded with an error -- never raised
    for "the feature doesn't exist yet"; only for a real, attempted call
    that failed."""
