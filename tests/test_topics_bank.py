from datetime import date

from pipeline import topics_bank


def test_pick_category_is_deterministic():
    d = date(2026, 3, 15)
    assert topics_bank.pick_category(d) == topics_bank.pick_category(d)


def test_pick_category_cycles_through_all_categories_over_a_year():
    categories = topics_bank.load()["categories"]
    seen = set()
    for day_offset in range(366):
        d = date(2026, 1, 1)
        d = date.fromordinal(d.toordinal() + day_offset)
        seen.add(topics_bank.pick_category(d)["id"])
    assert seen == {c["id"] for c in categories}


def test_is_near_duplicate_flags_identical_title():
    history = [{"title": "Rhymo Shares His Carrot", "premise": "Rhymo learns to share a carrot with a friend."}]
    assert topics_bank.is_near_duplicate(
        "Rhymo Shares His Carrot", "Rhymo learns to share a carrot with a friend.", history
    )


def test_is_near_duplicate_allows_distinct_story():
    history = [{"title": "Rhymo Shares His Carrot", "premise": "Rhymo learns to share a carrot with a friend."}]
    assert not topics_bank.is_near_duplicate(
        "Rhymo Counts the Stars", "Rhymo counts twinkling stars with an owl at bedtime.", history
    )


def test_is_near_duplicate_with_empty_history():
    assert not topics_bank.is_near_duplicate("Any Title", "Any premise.", [])
