# Maika CLI package
__version__ = "3.0.0"

# Maika framework/protocol version stamped into resolved-config.yaml and the
# render context. Distinct from __version__ (the CLI package version).
FRAMEWORK_VERSION = "3.0"

# Canonical Maika framework root — the single default used wherever a
# framework_root cannot be derived from a loaded config. Equals the base/
# generic platform's framework_root (asserted by tests).
CANONICAL_FRAMEWORK_ROOT = ".maika"
