"""Tests for delegation aggregation strategies (REQ-SUBAG-04)."""

import pytest
from moya.delegation.aggregation import aggregate, STRATEGIES


# ── concat ────────────────────────────────────────────────────────────────────

def test_concat_joins_with_blank_line():
    assert aggregate(["a", "b", "c"], "concat") == "a\n\nb\n\nc"


def test_concat_single():
    assert aggregate(["only"], "concat") == "only"


def test_concat_empty_list():
    assert aggregate([], "concat") == ""


# ── first ─────────────────────────────────────────────────────────────────────

def test_first_returns_first():
    assert aggregate(["x", "y", "z"], "first") == "x"


def test_first_empty_list():
    assert aggregate([], "first") == ""


# ── vote ──────────────────────────────────────────────────────────────────────

def test_vote_majority():
    assert aggregate(["a", "b", "a"], "vote") == "a"


def test_vote_unanimous():
    assert aggregate(["yes", "yes", "yes"], "vote") == "yes"


def test_vote_single():
    assert aggregate(["solo"], "vote") == "solo"


def test_vote_empty_list():
    assert aggregate([], "vote") == ""


# ── custom ────────────────────────────────────────────────────────────────────

def test_custom_calls_fn():
    result = aggregate(["a", "b"], "custom", custom_fn=lambda rs: "|".join(rs))
    assert result == "a|b"


def test_custom_without_fn_raises():
    with pytest.raises(ValueError, match="custom_fn"):
        aggregate(["a"], "custom")


# ── unknown strategy ──────────────────────────────────────────────────────────

def test_unknown_strategy_raises():
    with pytest.raises(ValueError, match="Unknown aggregation strategy"):
        aggregate(["a"], "nonexistent")


# ── default strategy ─────────────────────────────────────────────────────────

def test_default_strategy_is_concat():
    assert aggregate(["p", "q"]) == "p\n\nq"


# ── STRATEGIES constant ───────────────────────────────────────────────────────

def test_strategies_set_contains_all():
    assert {"concat", "first", "vote", "custom"} <= STRATEGIES
