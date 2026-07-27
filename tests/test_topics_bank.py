from datetime import date

from pipeline import topics_bank


def test_pick_category_is_deterministic():
    d = date(2026, 3, 15)
    assert topics_bank.pick_category(d) == topics_bank.pick_category(d)


def test_pick_category_cycles_through_all_categories_over_a_year():
    categories = topics_bank.load()["categories"]
    seen = set()
    for day_offset in range(366):
        d = date.fromordinal(date(2026, 1, 1).toordinal() + day_offset)
        seen.add(topics_bank.pick_category(d)["id"])
    assert seen == {c["id"] for c in categories}


def test_history_window_exceeds_category_count():
    """The model must see several full rotations of history, otherwise old
    themes roll out of the window and stories start repeating — the pattern
    YouTube's mass-produced content policy targets."""
    cfg = topics_bank.load()
    assert cfg["recent_history_window"] > len(cfg["categories"])


def test_category_ids_are_unique():
    ids = [c["id"] for c in topics_bank.load()["categories"]]
    assert len(ids) == len(set(ids))


def test_is_near_duplicate_flags_identical_title():
    history = [{"title": "Hoplin Shares His Carrot", "premise": "Hoplin learns to share a carrot with a friend."}]
    assert topics_bank.is_near_duplicate(
        "Hoplin Shares His Carrot", "Hoplin learns to share a carrot with a friend.", history
    )


def test_is_near_duplicate_allows_distinct_story():
    history = [{"title": "Hoplin Shares His Carrot", "premise": "Hoplin learns to share a carrot with a friend."}]
    assert not topics_bank.is_near_duplicate(
        "Hoplin Counts the Stars", "Hoplin counts twinkling stars with an owl at bedtime.", history
    )


def test_is_near_duplicate_with_empty_history():
    assert not topics_bank.is_near_duplicate("Any Title", "Any premise.", [])


def test_is_near_duplicate_tolerates_missing_premise_in_history():
    history = [{"title": "Hoplin Shares His Carrot", "premise": None}]
    assert not topics_bank.is_near_duplicate("Hoplin Counts the Stars", "A bedtime counting story.", history)
