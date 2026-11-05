"""Donor eligibility tests (TC-DON-02, TC-DON-03, TC-PROF-07)."""

from datetime import date

from freezegun import freeze_time

from app.services.eligibility import cooldown_days_left, eligibility, is_eligible


@freeze_time("2026-01-01")
def test_cooldown_blocks_donor_for_90_days(app, make_user):
    donor = make_user(last_donation_date=date(2025, 12, 1))

    ok, reason = eligibility(donor)

    assert ok is False
    assert reason == "cooldown"


@freeze_time("2026-03-02")
def test_donor_is_eligible_after_cooldown(app, make_user):
    donor = make_user(last_donation_date=date(2025, 12, 1))

    assert is_eligible(donor) is True


@freeze_time("2026-01-01")
def test_unavailable_donor_is_not_eligible(app, make_user):
    donor = make_user(is_available=False)

    ok, reason = eligibility(donor)

    assert ok is False
    assert reason == "unavailable"


@freeze_time("2026-01-01")
def test_underage_donor_is_not_eligible(app, make_user):
    donor = make_user(date_of_birth=date(2010, 1, 1))

    ok, reason = eligibility(donor)

    assert ok is False
    assert reason == "age"


@freeze_time("2026-01-01")
def test_requester_is_not_a_donor(app, make_user):
    user = make_user(is_donor=False)

    ok, reason = eligibility(user)

    assert ok is False
    assert reason == "not_donor"


@freeze_time("2026-01-01")
def test_cooldown_days_left(app, make_user):
    donor = make_user(last_donation_date=date(2025, 12, 1))

    assert cooldown_days_left(donor) == 59


@freeze_time("2026-01-01")
def test_donor_without_previous_donation_is_eligible(app, make_user):
    donor = make_user()

    assert is_eligible(donor) is True
