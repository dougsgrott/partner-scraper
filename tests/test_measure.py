"""Standing instruments and noise normalisations — issue/accuracy/10.

Fixture bytes are verbatim excerpts from the archived generations (the standing rule:
real text, because paraphrases change the measured property). Each noise pattern's
test uses the real churn that admitted it; the full-corpus validation — 0 / 5,255 /
1,084 on gen1->gen2, 188 / 4,966 / 680 on gen2->gen3 — is recorded in the issue file
and reruns via `scripts/measure.py raw-churn`.
"""

from __future__ import annotations

import json

from changefeed import measure
from changefeed.db import ChangeDB
from scraper.fetch import noise

# raw-archive/20260829T181157 vs 20260909T172623, admin/access-control/auth-external
H2_GEN1 = (b'<h2 class="anchor anchorTargetStickyNavbar_Dt63" id=requirements>Requirements'
           b'<a href=#requirements class=hash-link aria-label="Direct link to Requirements" '
           b'title="Direct link to Requirements" translate=no>\xe2\x80\x8b</a></h2>')
H2_GEN2 = H2_GEN1.replace(b"_Dt63", b"_e1Nq")

LINK_GEN2 = b"<link rel=stylesheet href=/aws/en/assets/css/styles.470f1909.css />"
LINK_GEN3 = b"<link rel=stylesheet href=/aws/en/assets/css/styles.e7867e07.css />"

# docs/raw-archive.md, the gen2->gen3 re-date event, verbatim
TIME_OLD = b"<time datetime=2026-06-23T00:00:00.000Z itemprop=dateModified>Jun 23, 2026"
TIME_NEW = b"<time datetime=2026-09-11T00:00:00.000Z itemprop=dateModified>Sep 11, 2026"

# foundation-model-apis/supported-models, gen1 vs gen2: the retention note with the
# appended cannot-use clause — the motivating real change of the whole issue set.
RETENTION_GEN1 = (b"<p>For Claude Fable 5, prompts and responses are retained for 30 days "
                  b"for trust and safety purposes. This data is processed by automated "
                  b"safety systems and may in certain instances be flagged")
RETENTION_GEN2 = (b"<p>For Claude Fable 5.1, prompts and responses are retained for 30 days "
                  b"for trust and safety purposes. Customers who opt out of data retention "
                  b"cannot use Claude Fable 5.1. This data is processed by automated "
                  b"safety systems and may in certain instances be flagged")


# -- noise patterns ---------------------------------------------------------

def test_css_module_suffix_collapses_the_rebuild():
    assert noise.collapse(H2_GEN1, H2_GEN2) == "css-module-suffix"


def test_lowercase_suffixes_normalise_too():
    """`navbarSearchContainer_xryr` — the suffix that broke the narrow first regex."""
    out = noise.normalise(b"<div class=navbarSearchContainer_xryr></div>")
    assert out == b"<div class=navbarSearchContainer_HASH></div>"


def test_asset_hash_collapses_a_bundle_rotation():
    assert noise.collapse(LINK_GEN2, LINK_GEN3) == "asset-hash"


def test_date_modified_collapses_the_redate():
    assert noise.collapse(TIME_OLD, TIME_NEW) == "date-modified"


def test_a_real_change_survives_every_pattern():
    """The Fable 5.1 retention clause must never be eaten as noise."""
    assert noise.collapse(RETENTION_GEN1, RETENTION_GEN2) is None


def test_noise_plus_real_change_still_survives():
    """A page with both a suffix rebuild and a prose edit is a survivor."""
    assert noise.collapse(H2_GEN1 + RETENTION_GEN1, H2_GEN2 + RETENTION_GEN2) is None


def test_attribution_is_the_first_sufficient_pattern():
    """Cumulative order: asset+css churn together is attributed to css-module-suffix,
    the pattern at which nothing remains — the recorded tables' convention."""
    assert noise.collapse(LINK_GEN2 + H2_GEN1, LINK_GEN3 + H2_GEN2) == "css-module-suffix"


def test_identical_bodies_are_not_a_collapse():
    assert noise.collapse(H2_GEN1, H2_GEN1) is None


# -- duplicate bodies -------------------------------------------------------

def _page(db, snap, url, body_hash):
    db.conn.execute(
        "INSERT INTO page_versions (snapshot_id, url, company, content_hash) "
        "VALUES (?, ?, ?, ?)", (snap, url, "anthropic", body_hash))


def test_duplicate_bodies_counts_groups_and_mirrors(tmp_path):
    with ChangeDB(tmp_path / "c.db") as db:
        _page(db, 1, "https://platform.claude.com/docs/en/api/admin/users", "aaa")
        _page(db, 1, "https://platform.claude.com/docs/en/api/beta/organization/users", "aaa")
        _page(db, 1, "https://docs.databricks.com/aws/en/mlflow3/genai/tracing/", "bbb")
        _page(db, 1, "https://docs.databricks.com/aws/en/mlflow3/genai/tracing/overview", "bbb")
        _page(db, 1, "https://platform.claude.com/docs/en/unique", "ccc")
        db.conn.commit()
        dup = measure.duplicate_bodies(db, 1)

    assert dup.groups == 2
    assert dup.mirror_groups == 1
    assert dup.pages_in_groups == 4
    assert dup.non_mirror_samples == [[
        "https://docs.databricks.com/aws/en/mlflow3/genai/tracing/",
        "https://docs.databricks.com/aws/en/mlflow3/genai/tracing/overview"]]


# -- ranking overlap --------------------------------------------------------

def _finding(db, urls, *, superseded=None, fid=None):
    cur = db.conn.execute(
        "INSERT INTO findings (before_snapshot, after_snapshot, recorded_at, impact, "
        "summary, urls, superseded_at) VALUES (1, 2, 't', 'additive', 's', ?, ?)",
        (json.dumps(urls), superseded))
    return cur.lastrowid


def test_ranking_overlap_uses_best_cited_rank(tmp_path):
    report = tmp_path / "r.json"
    report.write_text(json.dumps({"changes": [
        {"kind": "modified", "cause": "content", "url": "u1", "company": "a",
         "severity": 5.0},
        {"kind": "modified", "cause": "content", "url": "u2", "company": "a",
         "severity": 3.0},
        {"kind": "modified", "cause": "content", "url": "u3", "company": "a",
         "severity": 1.0},
        {"kind": "added", "cause": "content", "url": "u4", "company": "a",
         "severity": 9.0},
    ]}))
    with ChangeDB(tmp_path / "c.db") as db:
        _finding(db, ["u3", "u2"])          # best rank 2
        _finding(db, ["u4"])                # added page: no rank
        _finding(db, ["u1"], superseded="x")  # superseded: excluded
        db.conn.commit()
        overlap = measure.ranking_overlap(db, (1, 2), report)

    assert overlap.universe == 3
    assert overlap.findings == 2
    assert overlap.ranked == [2]
    assert overlap.unranked == 1


# -- reconciliation ---------------------------------------------------------

FEED = {"added": 69, "removed": 0, "modified": 991, "moved": 12, "metadata": 5}
CAUSES = {"content": 986}


def test_reconcile_agrees_within_residue():
    rec = measure.reconcile(FEED, CAUSES,
                            extract={"written": 6406, "unchanged_files": 5323})
    assert rec.ok
    assert rec.feed_changed == 986 + 69
    assert rec.extract_changed == 1083
    assert "residue: 28" in rec.render()
    assert "ok — feed changes within extract" in rec.render()


def test_reconcile_fails_loud_when_feed_exceeds_extract():
    """More changed pages in the feed than extract wrote: no healthy pipeline does this."""
    rec = measure.reconcile(FEED, CAUSES,
                            extract={"written": 6406, "unchanged_files": 6000})
    assert not rec.ok
    assert "!! MISMATCH" in rec.render()


def test_reconcile_fails_loud_when_noise_eats_a_real_change():
    churn = measure.RawChurn(gen1="g1", gen2="g2")
    churn.collapsed_paths = {
        ("databricks/docs.databricks.com/aws/en/machine-learning/"
         "foundation-model-apis/supported-models.html.gz")}
    rec = measure.reconcile(
        FEED, CAUSES, churn=churn,
        modified=[{"url": ("https://docs.databricks.com/aws/en/machine-learning/"
                           "foundation-model-apis/supported-models"),
                   "company": "databricks"}])
    assert not rec.ok
    assert rec.missed_real
    assert "must be 0" in rec.render()


def test_reconcile_with_no_legs_says_so():
    rec = measure.reconcile(FEED, CAUSES)
    assert rec.ok
    assert "nothing to check" in rec.render()
    assert "no summary for this window" in rec.render()


def test_reconcile_warns_on_pipeline_attribution():
    rec = measure.reconcile(FEED, {"content": 980, "pipeline": 6})
    assert rec.ok  # a warning, not a failure — extractor changes are legitimate
    assert "WARNING: 6 changes attributed `pipeline`" in rec.render()


# -- the noise canary (issue/accuracy/11) -----------------------------------

MODIFIED = [{"url": "https://docs.databricks.com/aws/en/machine-learning/"
                    "foundation-model-apis/supported-models",
             "company": "databricks"}]
SUPPORTED_MODELS_PATH = ("databricks/docs.databricks.com/aws/en/machine-learning/"
                         "foundation-model-apis/supported-models.html.gz")


def _churn_with(survivors):
    churn = measure.RawChurn(gen1="g1", gen2="g2")
    churn.survivors = list(survivors)
    return churn


def test_canary_stays_quiet_at_the_measured_base_rate():
    """~6-8% of survivors are residual noise in a quiet window; no alarm."""
    survivors = [SUPPORTED_MODELS_PATH] + [f"databricks/x/{i}.html.gz" for i in range(7)]
    canary = measure.unknown_noise(_churn_with(survivors), MODIFIED)
    assert len(canary.candidates) == 7
    assert not canary.tripped
    assert "quiet" in canary.render()


def test_canary_trips_on_event_scale_unknown_noise():
    survivors = [SUPPORTED_MODELS_PATH] + [f"databricks/x/{i}.html.gz" for i in range(99)]
    canary = measure.unknown_noise(_churn_with(survivors), MODIFIED)
    assert canary.tripped
    assert "!! CANARY" in canary.render("g1", "g2")
    assert "measure.py residue g1 g2" in canary.render("g1", "g2")


def test_canary_minimum_count_guards_tiny_survivor_sets():
    """100% of 10 survivors is residue arithmetic, not an event."""
    canary = measure.unknown_noise(
        _churn_with([f"databricks/x/{i}.html.gz" for i in range(10)]), MODIFIED)
    assert canary.rate == 1.0
    assert not canary.tripped


def test_a_mass_real_edit_does_not_trip_the_canary():
    """The false-alarm case, by construction: a site-wide *content* change puts its
    pages among the modifications, so they are subtracted before the rate is taken."""
    modified = [{"url": f"https://docs.databricks.com/aws/en/x/{i}",
                 "company": "databricks"} for i in range(200)]
    survivors = [f"databricks/docs.databricks.com/aws/en/x/{i}.html.gz"
                 for i in range(200)]
    canary = measure.unknown_noise(_churn_with(survivors), modified)
    assert canary.candidates == []
    assert not canary.tripped


def test_reconcile_carries_the_canary(tmp_path):
    churn = _churn_with([SUPPORTED_MODELS_PATH]
                        + [f"databricks/x/{i}.html.gz" for i in range(99)])
    rec = measure.reconcile(FEED, CAUSES, churn=churn, modified=MODIFIED)
    assert rec.canary is not None and rec.canary.tripped
    assert rec.ok  # a tripped canary is a warning to investigate, not a failure
    assert "!! CANARY" in rec.render()


def _write_gen(root, files: dict[str, bytes]) -> None:
    import gzip as _gzip

    for rel, body in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(_gzip.compress(body))


def test_clusterer_rederives_the_suffix_pattern_blind(tmp_path):
    """The gating test in miniature: real archived byte lines, an empty registry,
    and the cluster the human reads must be the `_Dt63`-shaped one. The full-corpus
    replays (84% / 81% canary, pattern in the top clusters) are recorded in the
    issue file and rerun via `measure.py residue --ignore-pattern`."""
    g1, g2 = tmp_path / "g1", tmp_path / "g2"
    files1 = {f"databricks/host/p{i}.html.gz": H2_GEN1 + TIME_OLD for i in range(3)}
    files2 = {f"databricks/host/p{i}.html.gz": H2_GEN2 + TIME_OLD for i in range(3)}
    _write_gen(g1, files1)
    _write_gen(g2, files2)

    clusters, sampled = measure.cluster_residue(
        g1, g2, sorted(files1), patterns=(), sample_files=10)

    assert sampled == 3
    top = clusters[0]
    assert top.files == 3
    assert "after '_'" in top.shape
    assert "anchorTargetStickyNavbar" in top.exemplars[0][0]


def test_disjoint_changes_yield_no_shared_cluster(tmp_path):
    """No shared byte pattern -> nothing reaches the candidate-pattern flag."""
    g1, g2 = tmp_path / "g1", tmp_path / "g2"
    _write_gen(g1, {"a/1.html.gz": RETENTION_GEN1, "a/2.html.gz": TIME_OLD,
                    "a/3.html.gz": LINK_GEN2})
    _write_gen(g2, {"a/1.html.gz": RETENTION_GEN2, "a/2.html.gz": TIME_NEW,
                    "a/3.html.gz": LINK_GEN3})

    clusters, sampled = measure.cluster_residue(
        g1, g2, ["a/1.html.gz", "a/2.html.gz", "a/3.html.gz"],
        patterns=(), sample_files=10)

    assert all(c.files < sampled / 2 for c in clusters)


def test_reconcile_flags_a_wrong_generation_pair():
    churn = measure.RawChurn(gen1="g1", gen2="g2")
    churn.survivors = ["anthropic/platform.claude.com/docs/en/other.md.gz"]
    rec = measure.reconcile(
        FEED, CAUSES, churn=churn,
        modified=[{"url": "https://docs.databricks.com/aws/en/nowhere",
                   "company": "databricks"}])
    assert rec.ok  # nothing collapsed — but the mapping failure is named
    assert "wrong generation pair" in rec.render()
