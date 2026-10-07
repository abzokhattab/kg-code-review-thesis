#!/usr/bin/env python3
"""Check that what pilot/index.html sends is what analyze_responses.py accepts.

    python3 check_payload_schema.py                    # bundled fixture
    python3 check_payload_schema.py payloads.json      # payloads pulled from a browser

`analyze_responses.py --selftest` cannot catch this. Its fixtures are written by
hand in the same file as the code that reads them, so the two agree by
construction and stay agreeing even when the client starts sending something
else. The fixture here was captured from the deployed build, out of the browser
outbox, and is the only artefact in the repo that shows the payload as the
client actually emits it.

Both ingestion routes are exercised, because either may be used at analysis
time: the sheet exported as CSV with the payload JSON in a cell, and a folder of
the browser's own backup JSON files. A single JSON file is not a supported
input to `iter_payloads` and is silently read as CSV, yielding nothing.

Re-run after any edit to the payload built in `submitCurrent()`, and after any
bump of `INSTRUMENT_VERSION`.
"""
import csv
import json
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import analyze_responses as A  # noqa: E402

FIXTURE = HERE / "fixtures" / "client_payloads.json"

REQUIRED_PAYLOAD_FIELDS = {"study_id", "instrument_version", "rater_id",
                           "completed_at", "demographics", "ratings"}
REQUIRED_RATING_FIELDS = {"pr_id", "comparison", "mode_A", "mode_B", "criteria",
                          "overall", "difficulty", "time_spent_ms",
                          "github_clicks", "highlight_used"}


def main(argv):
    src = Path(argv[1]) if len(argv) > 1 else FIXTURE
    payloads = json.loads(src.read_text())
    print("payloads: %s (%d)" % (src, len(payloads)))
    print("analyser expects instrument_version %s" % A.INSTRUMENT_VERSION)

    failures = []

    sent = {k for p in payloads for k in p}
    sent_rating = {k for p in payloads for r in p.get("ratings", []) for k in r}
    for label, missing in (("payload", REQUIRED_PAYLOAD_FIELDS - sent),
                           ("rating", REQUIRED_RATING_FIELDS - sent_rating)):
        if missing:
            failures.append("client omits %s field(s): %s"
                            % (label, ", ".join(sorted(missing))))
    print("payload fields sent: %s" % ", ".join(sorted(sent)))
    print("rating fields sent:  %s" % ", ".join(sorted(sent_rating)))

    # Pilot ids start with "pilot"/"test" and are excluded by design, so rename
    # them; the point here is to exercise the accept path, not the filter.
    renamed = []
    for i, p in enumerate(payloads):
        q = json.loads(json.dumps(p))
        q["rater_id"] = "rater_schema_%d" % i
        renamed.append(q)
    expected = sum(1 for p in renamed
                   if p.get("instrument_version") == A.INSTRUMENT_VERSION)
    if not expected:
        failures.append("no payload carries the current instrument version; "
                        "recapture the fixture from the deployed build")

    tmp = Path(tempfile.mkdtemp(prefix="payload_schema_"))
    try:
        csv_path = tmp / "sheet_export.csv"
        with csv_path.open("w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["timestamp", "rater_id", "raw_log"])
            for p in renamed:
                w.writerow([p.get("completed_at", ""), p["rater_id"],
                            json.dumps(p)])

        dir_path = tmp / "backups"
        dir_path.mkdir()
        (dir_path / "backup.json").write_text(
            json.dumps({"study_id": A.STUDY_ID, "payloads": renamed}))

        for label, route in (("sheet CSV", csv_path),
                             ("backup folder", dir_path)):
            ratings, _feedback, audit = A.load_ratings(route)
            accepted = audit.get("rows_accepted", 0)
            rejected = audit.get("rows_rejected", 0)
            stale = audit.get("wrong_instrument", 0)
            print("\n%s: %d accepted, %d rejected, %d on an older instrument"
                  % (label, accepted, rejected, stale))
            for rid, tasks in sorted(ratings.items()):
                for t in tasks:
                    # 1.0 = the rater picked the KG review, 0.0 = the baseline,
                    # 0.5 = equal. The side labels A and B are what the rater
                    # saw; un-blinding to this scale is what is being checked.
                    print("  %-16s pr=%s  chose %-5s -> kg_score %.1f"
                          % (rid, t["pr_id"], t["overall_choice"],
                             t["overall"]))
            if accepted != expected:
                failures.append("%s accepted %d rows, expected %d"
                                % (label, accepted, expected))
            if rejected:
                failures.append("%s rejected %d row(s) the client sent"
                                % (label, rejected))
            if stale != len(renamed) - expected:
                failures.append("%s counted %d stale payloads, expected %d"
                                % (label, stale, len(renamed) - expected))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print()
    if failures:
        for f in failures:
            print("FAIL: %s" % f)
        return 1
    print("SCHEMA OK: the deployed client's payload is ingested by both routes, "
          "and payloads from an older instrument are held back.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
