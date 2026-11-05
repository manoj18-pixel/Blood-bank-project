"""Blood compatibility unit tests (TC-SRCH-02..04)."""

from app.services.matching import (
    COMPATIBILITY,
    compatible_donor_groups,
    compatible_recipient_groups,
    donor_can_donate_to,
    find_matching_donors,
)

ALL_GROUPS = {"A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"}


def test_a_positive_recipient_groups():
    assert set(compatible_donor_groups("A+")) == {"A+", "A-", "O+", "O-"}


def test_ab_positive_is_universal_recipient():
    assert set(compatible_donor_groups("AB+")) == ALL_GROUPS


def test_o_negative_recipient_only_gets_o_negative():
    assert compatible_donor_groups("O-") == ["O-"]


def test_o_negative_donor_is_universal():
    for recipient in ALL_GROUPS:
        assert donor_can_donate_to("O-", recipient) is True


def test_ab_positive_donor_only_gives_to_ab_positive():
    assert compatible_recipient_groups("AB+") == ["AB+"]


def test_incompatible_pair():
    assert donor_can_donate_to("B+", "A+") is False


def test_every_group_has_a_mapping():
    assert set(COMPATIBILITY) == ALL_GROUPS


def test_ranking_prefers_exact_group_and_nearby(
    app, make_user, make_request
):
    requester = make_user(
        email="ravi@example.com", blood_group="A+", is_donor=False, city="Pune"
    )
    close = make_user(
        email="close@example.com",
        full_name="Close Match",
        blood_group="A+",
        city="Pune",
        latitude=18.5204,
        longitude=73.8567,
    )
    far = make_user(
        email="far@example.com",
        full_name="Far Match",
        blood_group="A+",
        city="Pune",
        latitude=19.5,
        longitude=74.5,
    )
    compatible = make_user(
        email="other@example.com",
        full_name="Compatible Other",
        blood_group="O-",
        city="Pune",
        latitude=18.5204,
        longitude=73.8567,
    )
    blood_request = make_request(
        requester,
        blood_group="A+",
        city="Pune",
        latitude=18.5204,
        longitude=73.8567,
    )

    results = find_matching_donors(blood_request)

    assert {item["donor"].id for item in results} == {
        close.id,
        far.id,
        compatible.id,
    }
    assert results[0]["donor"].id == close.id
    assert results[0]["score"] > results[1]["score"]
    assert results[0]["distance_km"] == 0.0
