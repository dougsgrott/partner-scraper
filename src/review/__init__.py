"""The review tool: a local UI for grading, labeling, and future human review.

See docs/review-tool-plan.md. Two design keys:

* **Everything is a review queue.** One abstraction — items, an evidence renderer, a
  verdict schema, a validated write path (`queues.py`). New human-review functionality
  is a new queue kind, not a new tool.
* **A thin skin over existing modules.** Rendering and writing go through `verdicts`,
  `audit`, `diff`, `blobs`, `classify`, `absence`; this package owns no grading or
  labeling semantics of its own, so it moves with the pipeline instead of forking it.

Only `app.py` imports FastAPI (the `review` extra); `store`, `queues` and `evidence`
are importable — and testable — without it, matching the `digest` package's split.
"""
