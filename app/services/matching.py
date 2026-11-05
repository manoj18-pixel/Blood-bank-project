"""Blood-group compatibility and donor ranking."""

from math import asin, cos, radians, sin, sqrt

from sqlalchemy import func

from app.constants import URGENCY_LEVELS
from app.extensions import db
from app.models import BloodRequest, User
from app.services.eligibility import eligibility
from app.utils.time import utcnow

# recipient -> compatible donor groups (one source of truth)
COMPATIBILITY: dict[str, tuple[str, ...]] = {
    "O-": ("O-",),
    "O+": ("O-", "O+"),
    "A-": ("O-", "A-"),
    "A+": ("O-", "O+", "A-", "A+"),
    "B-": ("O-", "B-"),
    "B+": ("O-", "O+", "B-", "B+"),
    "AB-": ("O-", "A-", "B-", "AB-"),
    "AB+": ("O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"),
}


def compatible_donor_groups(recipient_group: str) -> list[str]:
    """Groups that may donate to ``recipient_group``."""
    return list(COMPATIBILITY.get(recipient_group, ()))


def donor_can_donate_to(donor_group: str, recipient_group: str) -> bool:
    return donor_group in COMPATIBILITY.get(recipient_group, ())


def compatible_recipient_groups(donor_group: str) -> list[str]:
    """Recipient groups a donor can help."""
    return [
        recipient
        for recipient, donor_groups in COMPATIBILITY.items()
        if donor_group in donor_groups
    ]


def haversine_km(lat1, lon1, lat2, lon2) -> float:
    radius = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = (
        sin(dlat / 2) ** 2
        + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    )
    return 2 * radius * asin(sqrt(a))


def _distance(request: BloodRequest, donor: User) -> float | None:
    coords = (request.latitude, request.longitude, donor.latitude, donor.longitude)
    if any(value is None for value in coords):
        return None
    return round(haversine_km(*coords), 1)


def _score(donor: User, request: BloodRequest, distance: float | None, same_city: bool) -> int:
    score = 40 if donor.blood_group == request.blood_group else 25
    if distance is not None:
        score += max(0, round(30 - distance * 3))
    elif same_city:
        score += 12
    score += 20 if donor.is_available else 0
    score += 10 if donor.email_verified else 0
    score += 5 if donor.last_donation_date is None else 0
    score += min(10, donor.donation_count * 2)
    return score


def _query_donors(request: BloodRequest, city: str | None):
    groups = compatible_donor_groups(request.blood_group)
    query = User.query.filter(
        User.is_donor.is_(True),
        User.status == "active",
        User.blood_group.in_(groups),
    )
    if city:
        query = query.filter(func.lower(User.city) == city.strip().lower())
    return query.all()


def find_matching_donors(
    request: BloodRequest,
    include_unavailable: bool = False,
    broaden: bool = True,
) -> list[dict]:
    """Return ranked compatible donors for a request.

    Each item contains donor, score, distance_km, same_city, eligible and
    eligibility_reason. Suspended / under-age donors are never returned.
    """
    city = (request.city or "").strip()
    donors = _query_donors(request, city)
    results: dict[int, dict] = {}

    def add(donor: User, same_city: bool) -> None:
        if donor.id in results:
            return
        ok, reason = eligibility(donor)
        if not ok:
            if not include_unavailable:
                return
            if reason in {"suspended", "not_donor", "age", "unverified"}:
                return
        distance = _distance(request, donor)
        results[donor.id] = {
            "donor": donor,
            "score": _score(donor, request, distance, same_city),
            "distance_km": distance,
            "same_city": same_city,
            "eligible": ok,
            "eligibility_reason": reason,
        }

    for donor in donors:
        add(donor, same_city=True)

    if broaden and len(results) < 3:
        for donor in _query_donors(request, city=None):
            add(donor, same_city=False)

    ranked = sorted(
        results.values(),
        key=lambda item: (
            -item["score"],
            item["distance_km"] if item["distance_km"] is not None else 9999,
            item["donor"].last_donation_date or utcnow().date(),
        ),
    )
    return ranked


def matching_requests_for_donor(donor: User, limit: int = 6) -> list[dict]:
    """Open requests the donor's blood group can help with."""
    if not donor.blood_group:
        return []
    requests = (
        BloodRequest.query.filter(
            BloodRequest.status == "open",
            BloodRequest.needed_by > utcnow(),
        )
        .order_by(BloodRequest.needed_by.asc())
        .limit(200)
        .all()
    )
    urgency_rank = {level: index for index, level in enumerate(URGENCY_LEVELS)}
    matches = []
    for request in requests:
        if not donor_can_donate_to(donor.blood_group, request.blood_group):
            continue
        matches.append(
            {
                "request": request,
                "same_city": request.city.strip().lower() == donor.city.strip().lower(),
                "urgency_rank": urgency_rank.get(request.urgency, 0),
            }
        )
    matches.sort(
        key=lambda item: (
            0 if item["same_city"] else 1,
            item["urgency_rank"],
            item["request"].needed_by,
        )
    )
    return matches[:limit]


# Keep a reference to db so tests / future SQL filtering can extend this module.
__all__ = [
    "COMPATIBILITY",
    "compatible_donor_groups",
    "donor_can_donate_to",
    "compatible_recipient_groups",
    "find_matching_donors",
    "matching_requests_for_donor",
    "haversine_km",
    "db",
]
