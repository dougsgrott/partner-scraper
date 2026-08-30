"""Phase 2: turning a run of changes into a digest a person reads.

See `docs/changefeed-phase-2.md` for why this is shaped the way it is. The short version:
a whole run compresses to ~92k tokens, so it goes to **one** session rather than being
batched, pre-filtered, or clustered.

The split inside this package matters. `compress` is deterministic and imports nothing
beyond phase 1 — it can be built, tested, and run with no model and no API key, which is
most of the surface area. Only the session layer touches `claude-agent-sdk`, and it imports
it lazily, so `import changefeed` keeps working without the optional dependency installed.
"""

from .compress import CompressedChange, CompressedRun, compress, compress_run

__all__ = ["CompressedChange", "CompressedRun", "compress", "compress_run"]
