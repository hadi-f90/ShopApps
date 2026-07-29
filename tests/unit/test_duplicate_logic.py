from src.apps.contacts.duplicate_logic import (
    cluster_duplicates,
    match_against_index,
    name_similarity,
    normalize_name,
    phone_match_keys,
    phones_equivalent,
)


def test_persian_name_normalize():
    assert normalize_name("احمد  کیوانلو") == normalize_name("احمد کیوانلو")


def test_iran_phone_equivalence():
    a = "+989123456789"
    b = "09123456789"
    c = "9123456789"
    d = "00989123456789"
    assert phones_equivalent(a, b)
    assert phones_equivalent(b, c)
    assert phones_equivalent(a, d)
    assert phone_match_keys(a) & phone_match_keys(b)


def test_match_phone_fuzzy_index():
    # Index built with all keys for 0912...
    keys = phone_match_keys("09123456789")
    by_mobile = {k: "7" for k in keys}
    mr = match_against_index(
        mobile="+989123456789",
        by_mobile=by_mobile,
        by_phone={},
        by_email={},
        name_entries=[],
    )
    assert mr is not None
    assert mr.key == "7"
    assert mr.reason == "mobile"


def test_fuzzy_similar_names():
    assert name_similarity("احمد کیوانلو", "احمد کیوانلو") == 1.0


def test_match_fuzzy_name():
    mr = match_against_index(
        name="علی احمدی",
        by_mobile={},
        by_phone={},
        by_email={},
        name_entries=[("علی احمدی", "5")],
    )
    assert mr is not None
    assert mr.reason == "name_fuzzy"


def test_cluster_phone_variants():
    class C:
        def __init__(self, id, name, mobile="", phone="", email=""):
            self.id, self.name = id, name
            self.mobile, self.phone, self.email = mobile, phone, email

    items = [
        C(1, "A", mobile="+989111111111"),
        C(2, "B", mobile="09111111111"),
        C(3, "C", mobile="09112222222"),
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
    assert {c.id for c in groups[0]} == {1, 2}
