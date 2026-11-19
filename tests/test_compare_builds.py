#!/usr/bin/env python3
"""Checks for tools/compare_builds.py. Run with python3 -I tests/test_compare_builds.py."""
import json
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
import compare_builds


def tree(root, files):
    root = pathlib.Path(root)
    for name, body in files.items():
        (root / name).parent.mkdir(parents=True, exist_ok=True)
        (root / name).write_bytes(body if isinstance(body, bytes) else body.encode())
    return root


class Compare(unittest.TestCase):
    def test_identical_builds(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            files = {"index.html": "<p>x</p>", "img/a.png": b"\x89PNG\x00", "llms.txt": "x\n"}
            self.assertEqual(compare_builds.compare(tree(a, files), tree(b, files)), [])

    def test_missing_extra_and_changed_files(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            tree(a, {"index.html": "<p>1</p>\n<p>same</p>", "only-a.html": ""})
            tree(b, {"index.html": "<p>2</p>\n<p>same</p>", "only-b.html": ""})
            diffs = compare_builds.compare(pathlib.Path(a), pathlib.Path(b))
            text = "\n".join(diffs)
            self.assertIn("only-a.html", text)
            self.assertIn("only-b.html", text)
            self.assertIn("index.html: line 1", text)
            self.assertEqual(len(diffs), 3)

    def test_volatile_patterns_are_masked(self):
        a_note = '<p class="footer">This document was generated with Documenter.jl version 1.8 on <span>Tuesday 18 November 2026</span>.</p>'
        b_note = a_note.replace("Tuesday 18", "Wednesday 19")
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            tree(a, {"index.html": a_note})
            tree(b, {"index.html": b_note})
            self.assertTrue(compare_builds.compare(pathlib.Path(a), pathlib.Path(b)))
            vol = [r"This document was generated with Documenter\.jl.*?</p>"]
            self.assertEqual(compare_builds.compare(pathlib.Path(a), pathlib.Path(b), vol), [])

    def test_a_missing_build_is_an_error(self):
        with tempfile.TemporaryDirectory() as a:
            with self.assertRaises(FileNotFoundError):
                compare_builds.compare(pathlib.Path(a) / "public", pathlib.Path(a) / "other")
            tree(a, {"x/index.html": ""})
            with self.assertRaises(FileNotFoundError):
                compare_builds.compare(pathlib.Path(a) / "x", pathlib.Path(a) / "other")

    def test_binary_files_are_not_masked(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            tree(a, {"x.png": b"\x00\x01"})
            tree(b, {"x.png": b"\x00\x02"})
            self.assertEqual(compare_builds.compare(pathlib.Path(a), pathlib.Path(b), [r"."]), ["x.png: content differs"])

    def test_main_reads_volatile_from_site_kit_json(self):
        import contextlib
        import io
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b, tempfile.TemporaryDirectory() as c:
            tree(a, {"index.html": "built 1"})
            tree(b, {"index.html": "built 2"})
            cfg = pathlib.Path(c) / "site-kit.json"
            cfg.write_text(json.dumps({"volatile": [r"built \d"]}))
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(compare_builds.main([a, b]), 1)
                self.assertEqual(compare_builds.main([a, b, "--config", str(cfg)]), 0)


if __name__ == "__main__":
    unittest.main()
