"""The JSON API and the static shell. `scripts/review.py serve` runs this under uvicorn.

Localhost only, single user, no auth — recorded non-goals of v1 (docs/review-tool-plan.md).
Handlers open a `ChangeDB` per request (SQLite connections are thread-bound and FastAPI
runs sync handlers in a threadpool); the one expensive derived value, a snapshot pair's
`DiffResult`, is memoised per app instance because computing it walks every page version
and its blobs — seconds of work the evidence of every item in a queue shares.

Writes go through the queue kinds in `queues.py`, nowhere else: the API has no endpoint
that could store an unvalidated verdict or label.
"""

from __future__ import annotations

import threading
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles

from changefeed import diff as diff_mod
from changefeed.db import ChangeDB
from changefeed.digest import verdicts

from . import evidence, queues, store

STATIC_DIR = Path(__file__).parent / "static"


def create_app(changes_db: str | Path | None = None,
               blob_dir: str | Path | None = None) -> FastAPI:
    app = FastAPI(title="review", docs_url=None, redoc_url=None)
    blob_path = Path(blob_dir) if blob_dir else None
    diff_cache: dict[tuple[int, int], diff_mod.DiffResult] = {}
    diff_lock = threading.Lock()

    def open_db() -> ChangeDB:
        db = ChangeDB(changes_db) if changes_db else ChangeDB()
        store.ensure_schema(db)
        return db

    def make_ctx(db: ChangeDB) -> queues.Context:
        def diff_for(before: int, after: int) -> diff_mod.DiffResult:
            key = (before, after)
            with diff_lock:
                cached = diff_cache.get(key)
            if cached is not None:
                return cached
            b, a = db.snapshot(before), db.snapshot(after)
            if b is None or a is None:
                raise HTTPException(404, f"no such snapshot pair #{before} -> #{after}")
            result = diff_mod.compare(b, a, db=db, blob_dir=blob_path)
            with diff_lock:
                diff_cache[key] = result
            return result

        return queues.Context(db=db, blob_dir=blob_path, diff=diff_for)

    def load_queue(db: ChangeDB, queue_id: int):
        row = store.queue(db, queue_id)
        if row is None:
            raise HTTPException(404, f"no queue {queue_id}")
        return queues.load(row["kind"], row["id"], row["params"]), row

    # -- dashboard -----------------------------------------------------------

    @app.get("/api/snapshots")
    def api_snapshots() -> list[dict]:
        with open_db() as db:
            return [{"id": s.id, "taken_at": s.taken_at, "label": s.label,
                     "page_count": s.page_count} for s in db.snapshots()]

    @app.get("/api/accuracy")
    def api_accuracy() -> dict:
        with open_db() as db:
            return {"rows": verdicts.accuracy(db)}

    @app.get("/api/queues")
    def api_queues() -> list[dict]:
        with open_db() as db:
            ctx = make_ctx(db)
            out = []
            for row in store.queues(db):
                q = queues.load(row["kind"], row["id"], row["params"])
                try:
                    row["progress"] = q.progress(ctx)
                except (queues.ReviewError, ValueError) as err:
                    # A queue whose findings were re-run out from under it still lists,
                    # with the reason — hiding it would look like data loss.
                    row["progress"] = {"done": 0,
                                       "total": row["params"].get("item_count") or 0}
                    row["error"] = str(err)
                out.append(row)
            return out

    @app.post("/api/queues")
    def api_create_queue(payload: dict) -> dict:
        kind = payload.get("kind")
        title = (payload.get("title") or "").strip()
        params = payload.get("params") or {}
        if not title:
            raise HTTPException(400, "a queue needs a title")
        for field in ("before", "after"):
            if not str(params.get(field, "")).strip():
                raise HTTPException(400, f"params.{field} (a snapshot id) is required")
        with open_db() as db:
            ctx = make_ctx(db)
            try:
                q = queues.load(kind, 0, params)
                q.seal(ctx)  # validates and records selection/strata/item_count
            except (queues.ReviewError, ValueError) as err:
                raise HTTPException(400, str(err)) from err
            queue_id = store.create_queue(db, kind=kind, title=title, params=q.params,
                                          note=payload.get("note"))
            if kind == queues.LABELING:
                store.create_session(db, queue_id=queue_id,
                                     taxonomy_version=store.TAXONOMY_VERSION,
                                     pre_labeler=q.params["pre_labeler"])
            return store.queue(db, queue_id)

    # -- one queue -----------------------------------------------------------

    @app.get("/api/queues/{queue_id}")
    def api_queue(queue_id: int) -> dict:
        with open_db() as db:
            q, row = load_queue(db, queue_id)
            ctx = make_ctx(db)
            try:
                items = q.items(ctx)
            except (queues.ReviewError, ValueError) as err:
                raise HTTPException(409, f"queue {queue_id} cannot materialize: {err}"
                                    ) from err
            row["items"] = items
            row["progress"] = {"done": sum(1 for i in items if i["done"]),
                               "total": len(items)}
            if row["kind"] == queues.LABELING:
                session = store.session_for_queue(db, queue_id)
                if session:
                    row["flips"] = store.flip_summary(
                        store.labels_for_session(db, session["id"]))
            return row

    @app.get("/api/queues/{queue_id}/items/{item_id}")
    def api_evidence(queue_id: int, item_id: str) -> dict:
        with open_db() as db:
            q, _row = load_queue(db, queue_id)
            try:
                return q.evidence(make_ctx(db), item_id)
            except (queues.ReviewError, ValueError) as err:
                raise HTTPException(400, str(err)) from err

    @app.post("/api/queues/{queue_id}/items/{item_id}")
    def api_submit(queue_id: int, item_id: str, payload: dict) -> dict:
        with open_db() as db:
            q, _row = load_queue(db, queue_id)
            try:
                return q.submit(make_ctx(db), item_id, payload)
            except (queues.ReviewError, ValueError) as err:
                raise HTTPException(400, str(err)) from err

    @app.post("/api/queues/{queue_id}/export")
    def api_export(queue_id: int) -> dict:
        with open_db() as db:
            q, _row = load_queue(db, queue_id)
            try:
                path, count = q.export(make_ctx(db))
            except (queues.ReviewError, ValueError) as err:
                raise HTTPException(400, str(err)) from err
            return {"path": str(path), "count": count}

    @app.get("/api/queues/{queue_id}/page")
    def api_page(queue_id: int, url: str) -> dict:
        """Full before/after bodies, fetched lazily — the full-page method's `f` key."""
        with open_db() as db:
            q, _row = load_queue(db, queue_id)
            return evidence.page_bodies(db, q.pair, url, blob_dir=blob_path)

    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
    return app
