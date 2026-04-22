from __future__ import annotations

from _app.core.paths import safe_within


def test_safe_within_accepts_child(tmp_path):
    child = tmp_path / "a" / "b"
    assert safe_within(child, tmp_path) is not None


def test_safe_within_rejects_sibling(tmp_path):
    outside = tmp_path.parent / "elsewhere"
    assert safe_within(outside, tmp_path) is None


def test_safe_within_rejects_parent_traversal(tmp_path):
    sneaky = tmp_path / ".." / ".." / "etc"
    assert safe_within(sneaky, tmp_path) is None


def test_safe_within_accepts_nonexistent_child(tmp_path):
    future = tmp_path / "does" / "not" / "exist.txt"
    assert safe_within(future, tmp_path) is not None
