"""Tests for branchable, resumable AI writing sessions (AI-20)."""

from __future__ import annotations

import itertools
from pathlib import Path

import pytest

from quill.core.ai import sessions
from quill.core.ai.sessions import (
    ROLE_ASSISTANT,
    ROLE_USER,
    append_turn,
    branch_from,
    branch_points,
    branch_tips,
    compare_branches,
    current_path,
    describe_branches,
    list_sessions,
    load_session,
    most_recent_session,
    new_session,
    path_to,
    relabel_turn,
    resume,
    save_session,
    summarize_session,
)


@pytest.fixture
def data_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("QUILL_DATA_DIR", str(tmp_path))
    return tmp_path


def _ids():
    counter = itertools.count(1)
    return lambda: f"t{next(counter)}"


def _clock():
    counter = itertools.count(1)
    return lambda: f"2026-06-02T00:00:{next(counter):02d}+00:00"


def _build_branched() -> sessions.WritingSession:
    ids = _ids()
    clock = _clock()
    session = new_session("Draft intro", id_factory=lambda: "sess", clock=clock)
    session = append_turn(session, ROLE_USER, "Write an intro", id_factory=ids, clock=clock)
    session = append_turn(session, ROLE_ASSISTANT, "Intro version A", id_factory=ids, clock=clock)
    fork_id = session.current_turn_id
    assert fork_id is not None
    # Branch back to the user turn and try a second assistant rewrite.
    user_turn = path_to(session, fork_id)[0]
    session = branch_from(session, user_turn.turn_id, clock=clock)
    session = append_turn(session, ROLE_ASSISTANT, "Intro version B", id_factory=ids, clock=clock)
    return session


def test_append_builds_linear_path() -> None:
    ids = _ids()
    clock = _clock()
    session = new_session("Linear", id_factory=lambda: "s", clock=clock)
    session = append_turn(session, ROLE_USER, "Hello", id_factory=ids, clock=clock)
    session = append_turn(session, ROLE_ASSISTANT, "Hi there", id_factory=ids, clock=clock)

    path = current_path(session)
    assert [t.text for t in path] == ["Hello", "Hi there"]
    assert len(branch_tips(session)) == 1


def test_branch_creates_sibling_without_losing_state() -> None:
    session = _build_branched()

    tips = branch_tips(session)
    tip_texts = sorted(t.text for t in tips)
    assert tip_texts == ["Intro version A", "Intro version B"]

    # Both branches share the same first user turn as their fork point.
    forks = branch_points(session)
    assert len(forks) == 1
    assert forks[0].text == "Write an intro"

    # The current path follows version B (the active branch).
    assert [t.text for t in current_path(session)] == ["Write an intro", "Intro version B"]


def test_compare_branches_finds_fork_and_unique_turns() -> None:
    session = _build_branched()
    tips = sorted(branch_tips(session), key=lambda t: t.text)
    version_a, version_b = tips[0], tips[1]

    comparison = compare_branches(session, version_a.turn_id, version_b.turn_id)

    assert comparison.common_ancestor_id is not None
    ancestor = session.turn(comparison.common_ancestor_id)
    assert ancestor is not None and ancestor.text == "Write an intro"
    assert [t.text for t in comparison.left_only] == ["Intro version A"]
    assert [t.text for t in comparison.right_only] == ["Intro version B"]


def test_resume_sets_active_tip() -> None:
    session = _build_branched()
    version_a = next(t for t in branch_tips(session) if t.text == "Intro version A")

    resumed = resume(session, version_a.turn_id)

    assert resumed.current_turn_id == version_a.turn_id
    assert [t.text for t in current_path(resumed)] == ["Write an intro", "Intro version A"]


def test_relabel_turn_updates_label() -> None:
    session = _build_branched()
    tip = branch_tips(session)[0]
    relabeled = relabel_turn(session, tip.turn_id, "Formal tone")
    assert relabeled.turn(tip.turn_id).label == "Formal tone"  # type: ignore[union-attr]


def test_summaries_are_screen_reader_friendly() -> None:
    session = _build_branched()
    assert summarize_session(session) == "Draft intro: 3 turns, 2 branches."
    description = describe_branches(session)
    assert "Branch 1:" in description and "Branch 2:" in description
    assert "(current)" in description


def test_unknown_role_rejected() -> None:
    session = new_session("x", id_factory=lambda: "s")
    with pytest.raises(ValueError):
        append_turn(session, "robot", "nope")


def test_save_load_round_trip(data_dir: Path) -> None:
    session = _build_branched()
    save_session(session)

    loaded = load_session(session.session_id)
    assert loaded is not None
    assert loaded.to_dict() == session.to_dict()


def test_list_and_most_recent(data_dir: Path) -> None:
    first = new_session(
        "First", id_factory=lambda: "aaa", clock=lambda: "2026-06-01T00:00:00+00:00"
    )
    first = append_turn(first, ROLE_USER, "one", clock=lambda: "2026-06-01T00:00:01+00:00")
    save_session(first)

    second = new_session(
        "Second", id_factory=lambda: "bbb", clock=lambda: "2026-06-02T00:00:00+00:00"
    )
    save_session(second)

    summaries = list_sessions()
    assert [s.session_id for s in summaries] == ["bbb", "aaa"]

    recent = most_recent_session()
    assert recent is not None and recent.session_id == "bbb"


def test_unsafe_session_id_rejected() -> None:
    bad = new_session("bad", id_factory=lambda: "../escape")
    with pytest.raises(ValueError):
        save_session(bad)


def test_branch_rows_marks_current_branch() -> None:
    session = _build_branched()
    rows = sessions.branch_rows(session)

    assert len(rows) == 2
    # The active branch tip is flagged current and labelled accordingly.
    current_rows = [row for row in rows if row.is_current]
    assert len(current_rows) == 1
    assert "(current)" in current_rows[0].label
    assert all(row.depth == 2 for row in rows)
    # Every row carries a tip turn id usable for one-key jump.
    tip_ids = {tip.turn_id for tip in branch_tips(session)}
    assert {row.turn_id for row in rows} == tip_ids


def test_format_comparison_is_pageable_text() -> None:
    session = _build_branched()
    tips = sorted(branch_tips(session), key=lambda t: t.text)
    text = sessions.format_comparison(session, tips[0].turn_id, tips[1].turn_id)

    assert "Branches diverge after: Write an intro" in text
    assert "Only on the first branch (1 turns):" in text
    assert "Intro version A" in text
    assert "Intro version B" in text
