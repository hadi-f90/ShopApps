
from src.apps.contacts.duplicate_logic import (
    cluster_duplicates,
    match_against_index,
    name_similarity,
    normalize_name,
)


def test_persian_name_normalize():
    assert normalize_name("احمد  کیوانلو") == normalize_name("احمد کیوانلو")


def test_fuzzy_similar_names():
    assert name_similarity("احمد کیوانلو", "احمد کیوانلو") == 1.0
    assert name_similarity("محمد رضایی", "محمد رضایی ") >= 0.95


def test_match_fuzzy():
    mr = match_against_index(
        name="علی احمدی",
        by_mobile={},
        by_phone={},
        by_email={},
        name_entries=[("علی احمدی", "5")],
    )
    assert mr is not None
    assert mr.reason == "name_fuzzy"
    assert mr.key == "5"


def test_cluster():
    class C:
        def __init__(self, id, name, mobile="", phone="", email=""):
            self.id, self.name = id, name
            self.mobile, self.phone, self.email = mobile, phone, email

    items = [
        C(1, "Test", mobile="09121111111"),
        C(2, "Other"),
        C(3, "X", mobile="09121111111"),
    ]
    groups = cluster_duplicates(
        items,
        get_id=lambda c: c.id,
        get_mobile=lambda c: c.mobile,
        get_phone=lambda c: c.phone,
        get_email=lambda c: c.email,
        get_name=lambda c: c.name,
    )
    assert len(groups) == 1
    assert {c.id for c in groups[0]} == {1, 3}
