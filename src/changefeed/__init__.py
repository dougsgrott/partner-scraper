"""Change intelligence over the corpus. See docs/changefeed-plan.md.

The scraper builds a corpus; this reads one. The dependency runs one way only —
`changefeed` imports `scraper`, never the reverse — so the corpus builder stays testable
offline and free of this package's concerns.

Phase 1 is deterministic end to end: no model, no tokens, no network beyond an opt-in
refresh. It exists to answer a question nothing else can, because nothing has ever
retained a before-state: **how much of this corpus actually changes between runs?**
"""
