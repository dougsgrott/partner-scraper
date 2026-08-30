"""Phase 2: turning a run of changes into a digest a person reads.

See `docs/changefeed-phase-2.md` for why this is shaped the way it is. The short version:
a whole run compresses to ~105k tokens, so it goes to **one** session rather than being
batched, pre-filtered, or clustered.

The split inside this package matters. `compress`, `findings` and the tool *handlers* are
deterministic and import nothing beyond phase 1 — they can be built, tested, and run with
no model and no API key, which is most of the surface area. Only `session` and the thin MCP
wrapper in `tools` touch `claude-agent-sdk`, and both import it lazily, so
`import changefeed` keeps working without the optional dependency installed.
"""

from .compress import CompressedChange, CompressedRun, compress, compress_run
from .findings import IMPACTS, Finding

__all__ = [
    "IMPACTS",
    "CompressedChange",
    "CompressedRun",
    "Finding",
    "compress",
    "compress_run",
]
