#!/usr/bin/env python3
"""Checks for tools/upstream_status.py. Run with python3 -I tests/test_upstream_status.py."""
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
import upstream_status as us

ISSUE = {"number": 7, "title": "Wrong | result", "state": "closed", "state_reason": "completed",
         "created_at": "2026-11-01T10:00:00Z", "closed_at": "2026-11-03T09:00:00Z"}
NOT_PLANNED = dict(ISSUE, number=8, state_reason="not_planned")
PR = {"number": 9, "title": "Fix the result", "state": "closed", "pull_request": {"url": "u"},
      "created_at": "2026-11-02T00:00:00Z", "closed_at": "2026-11-04T00:00:00Z",
      "body": "This fixes #7.\nAlso closes other/repo#3."}
PR_MERGED = {"merged_at": "2026-11-04T00:00:00Z"}


class References(unittest.TestCase):
    def test_urls_and_short_forms(self):
        text = ("See https://github.com/a/b/issues/12 and https://github.com/a/b/pull/13#discussion,\n"
                "also a/b#14, c-d/e.f#5, not notes/findings.md#28 nor x/y.md#2.")
        self.assertEqual(us.references(text), [("a/b", 12), ("a/b", 13), ("a/b", 14), ("c-d/e.f", 5)])

    def test_scan_records_who_cites(self):
        with tempfile.TemporaryDirectory() as t:
            root = pathlib.Path(t)
            (root / "findings").mkdir()
            (root / "findings/f-1.md").write_text("a/b#1 and a/b#2")
            (root / "findings/f-2.md").write_text("https://github.com/a/b/issues/1")
            refs = us.scan([root / "findings/f-1.md", root / "findings/f-2.md"])
            self.assertEqual(refs, {("a/b", 1): {"f-1", "f-2"}, ("a/b", 2): {"f-1"}})

    def test_refs_file(self):
        with tempfile.TemporaryDirectory() as t:
            p = pathlib.Path(t) / "refs.txt"
            p.write_text("# repo#number cited_by...\na/b#1 F-1 F-2\n\nc/d#4\n")
            self.assertEqual(us.read_refs(p), {("a/b", 1): {"F-1", "F-2"}, ("c/d", 4): set()})


class Rows(unittest.TestCase):
    def test_issue_states(self):
        r = us.row("a/b", ISSUE, None, {"F-1"})
        self.assertEqual((r["kind"], r["state"], r["created"], r["closed"], r["merged"]), ("issue", "closed", "2026-11-01", "2026-11-03", ""))
        self.assertEqual(r["cited_by"], "F-1")
        self.assertEqual(us.row("a/b", NOT_PLANNED, None, set())["state"], "not planned")
        self.assertEqual(us.row("a/b", dict(ISSUE, state="open", closed_at=None), None, set())["state"], "open")

    def test_pull_requests(self):
        r = us.row("a/b", PR, PR_MERGED, set())
        self.assertEqual((r["kind"], r["state"], r["merged"]), ("pr", "merged", "2026-11-04"))
        self.assertEqual(r["fixes"], "a/b#7 other/repo#3")
        self.assertEqual(us.row("a/b", PR, {"merged_at": None}, set())["state"], "closed")

    def test_tsv_round_trip_escapes_tabs_and_newlines(self):
        rows = [us.row("a/b", dict(ISSUE, title="tab\there\nnewline"), None, {"F-2", "F-1"})]
        with tempfile.TemporaryDirectory() as t:
            p = pathlib.Path(t) / "s.tsv"
            us.write_tsv(p, rows)
            text = p.read_text()
            self.assertEqual(text.splitlines()[0].split("\t"), list(us.COLUMNS))
            back = us.read_tsv(p)
            self.assertEqual(back[("a/b", 7)]["title"], "tab here newline")
            self.assertEqual(back[("a/b", 7)]["cited_by"], "F-1 F-2")


class Refresh(unittest.TestCase):
    def test_refresh_keeps_the_previous_row_when_a_fetch_fails(self):
        old = {("a/b", 1): dict(us.row("a/b", dict(ISSUE, number=1, state="open", closed_at=None), None, set()))}

        def fetch(repo, number):
            if number == 1:
                raise OSError("offline")
            return ISSUE, None
        rows, failed = us.refresh({("a/b", 1): {"F"}, ("a/b", 7): set()}, fetch, old)
        self.assertEqual([(r["number"], r["state"]) for r in rows], [("1", "open"), ("7", "closed")])
        self.assertEqual(rows[0]["cited_by"], "F")
        self.assertEqual(failed, [("a/b", 1)])

    def test_rows_are_sorted_by_repository_and_number(self):
        def fetch(repo, number):
            return dict(ISSUE, number=number), None
        rows, _ = us.refresh({("b/c", 2): set(), ("a/b", 10): set(), ("a/b", 9): set()}, fetch, {})
        self.assertEqual([(r["repo"], r["number"]) for r in rows], [("a/b", "9"), ("a/b", "10"), ("b/c", "2")])


if __name__ == "__main__":
    unittest.main()
