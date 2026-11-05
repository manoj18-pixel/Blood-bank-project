"""Seed the database with demo donors, requests and donations.

Usage:
    python seed.py            # seed an empty database
    python seed.py --reset    # drop everything and seed again
"""

import argparse
from datetime import date, timedelta

from app import create_app
from app.extensions import db
from app.models import BloodRequest, Donation, DonorResponse, Notification, User
from app.utils.time import utcnow

app = create_app("development")


def make_user(
    name,
    email,
    password,
    group,
    city,
    area=None,
    pincode=None,
    *,
    lat=None,
    lng=None,
    last_donation=None,
    available=True,
    donor=True,
    status="active",
    verified=True,
    role="user",
):
    user = User(
        full_name=name,
        email=email,
        phone=f"9{abs(hash(email)) % 900000000 + 100000000:09d}",
        blood_group=group,
        city=city,
        area=area,
        pincode=pincode,
        latitude=lat,
        longitude=lng,
        is_donor=donor,
        is_available=available,
        last_donation_date=last_donation,
        email_verified=verified,
        status=status,
        role=role,
        date_of_birth=date(1992, 6, 15),
    )
    user.set_password(password)
    db.session.add(user)
    return user


def seed(reset: bool = False) -> None:
    with app.app_context():
        if reset:
            db.drop_all()
            db.create_all()
        else:
            db.create_all()
            if User.query.count() > 0:
                print("Database already contains data. Use --reset to rebuild it.")
                return

        admin = make_user(
            "BloodLink Admin",
            "admin@bloodlink.local",
            "Admin@12345",
            "O+",
            "Pune",
            role="admin",
            donor=False,
        )
        requester = make_user(
            "Ravi Kulkarni",
            "ravi@example.com",
            "Requester@12345",
            "A+",
            "Pune",
            "Shivajinagar",
            "411005",
            lat=18.5308,
            lng=73.8478,
            donor=False,
        )
        requester2 = make_user(
            "Meera Joshi",
            "meera@example.com",
            "Requester@12345",
            "B+",
            "Mumbai",
            "Andheri",
            "400053",
            lat=19.1197,
            lng=72.8464,
            donor=False,
        )

        today = date.today()

        donors = [
            # name, email, group, city, area, pincode, lat, lng, last donation, available, status
            ("Asha Rao", "asha@example.com", "O-", "Pune", "Kothrud", "411038", 18.5074, 73.8077, None, True, "active"),
            ("Vikram Patil", "vikram@example.com", "O+", "Pune", "Baner", "411045", 18.5590, 73.7868, today - timedelta(days=130), True, "active"),
            ("Neha Shah", "neha@example.com", "A+", "Pune", "Viman Nagar", "411014", 18.5679, 73.9143, today - timedelta(days=20), True, "active"),
            ("Arjun Deshmukh", "arjun@example.com", "A-", "Pune", "Hadapsar", "411028", 18.5089, 73.9260, None, True, "active"),
            ("Sneha Iyer", "sneha@example.com", "B+", "Pune", "Camp", "411001", 18.5122, 73.8780, today - timedelta(days=200), True, "active"),
            ("Karan Mehta", "karan@example.com", "B-", "Pune", "Wakad", "411057", 18.5970, 73.7620, None, False, "active"),
            ("Priya Nair", "priya@example.com", "AB+", "Pune", "Aundh", "411007", 18.5590, 73.8070, None, True, "active"),
            ("Rohan Gupta", "rohan@example.com", "AB-", "Pune", "Magarpatta", "411013", 18.5150, 73.9270, None, True, "active"),
            ("Divya Menon", "divya@example.com", "O-", "Mumbai", "Bandra", "400050", 19.0596, 72.8295, None, True, "active"),
            ("Aditya Kulkarni", "aditya@example.com", "B+", "Mumbai", "Dadar", "400014", 19.0186, 72.8440, today - timedelta(days=95), True, "active"),
            ("Isha Verma", "isha@example.com", "A+", "Nagpur", "Dharampeth", "440010", 21.1389, 79.0594, None, True, "suspended"),
            ("Sameer Khan", "sameer@example.com", "O+", "Nagpur", "Sadar", "440001", 21.1610, 79.0820, None, True, "active"),
        ]

        created = {}
        for row in donors:
            name, email, group, city, area, pincode, lat, lng, last, available, status = row
            created[email] = make_user(
                name,
                email,
                "Donor@12345",
                group,
                city,
                area,
                pincode,
                lat=lat,
                lng=lng,
                last_donation=last,
                available=available,
                status=status,
            )
        db.session.flush()

        # ---- open requests -------------------------------------------------
        request1 = BloodRequest(
            requester=requester,
            patient_name="Anita Kulkarni",
            patient_age=54,
            blood_group="A+",
            units_needed=2,
            hospital_name="Sassoon General Hospital",
            address="Near Pune Railway Station, Agarkar Nagar",
            city="Pune",
            pincode="411001",
            latitude=18.5250,
            longitude=73.8740,
            urgency="critical",
            needed_by=utcnow() + timedelta(hours=18),
            contact_phone=requester.phone,
            notes="Surgery scheduled tomorrow morning. Ward 12, bed 4.",
            status="open",
        )
        request2 = BloodRequest(
            requester=requester2,
            patient_name="Sanjay Joshi",
            patient_age=41,
            blood_group="B+",
            units_needed=1,
            hospital_name="Lilavati Hospital",
            address="A-791, Bandra Reclamation",
            city="Mumbai",
            pincode="400050",
            latitude=19.0509,
            longitude=72.8397,
            urgency="urgent",
            needed_by=utcnow() + timedelta(days=2),
            contact_phone=requester2.phone,
            notes="Patient is stable but needs a transfusion within 48 hours.",
            status="open",
        )
        request3 = BloodRequest(
            requester=requester,
            patient_name="Ramesh Patil",
            patient_age=67,
            blood_group="O-",
            units_needed=1,
            hospital_name="Ruby Hall Clinic",
            address="40, Sassoon Road",
            city="Pune",
            pincode="411001",
            latitude=18.5310,
            longitude=73.8770,
            urgency="normal",
            needed_by=utcnow() + timedelta(days=4),
            contact_phone=requester.phone,
            notes="Rare group. Please call before visiting.",
            status="open",
        )

        # matched request (accepted offer)
        request4 = BloodRequest(
            requester=requester,
            patient_name="Sunita Deshmukh",
            patient_age=35,
            blood_group="O+",
            units_needed=1,
            hospital_name="Deenanath Mangeshkar Hospital",
            address="Erandwane, Karve Road",
            city="Pune",
            pincode="411004",
            latitude=18.5010,
            longitude=73.8290,
            urgency="urgent",
            needed_by=utcnow() + timedelta(days=1),
            contact_phone=requester.phone,
            notes="Donor has been accepted. Donation planned for tomorrow.",
            status="matched",
        )

        # fulfilled request + donation
        request5 = BloodRequest(
            requester=requester2,
            patient_name="Farhan Shaikh",
            patient_age=29,
            blood_group="B+",
            units_needed=1,
            hospital_name="Kokilaben Dhirubhai Ambani Hospital",
            address="Rao Saheb Achutrao Patwardhan Marg, Andheri West",
            city="Mumbai",
            pincode="400053",
            latitude=19.1310,
            longitude=72.8250,
            urgency="normal",
            needed_by=utcnow() - timedelta(days=118),
            contact_phone=requester2.phone,
            status="fulfilled",
            fulfilled_at=utcnow() - timedelta(days=120),
        )

        db.session.add_all([request1, request2, request3, request4, request5])
        db.session.flush()

        accepted = DonorResponse(
            request=request4,
            donor=created["vikram@example.com"],
            status="accepted",
            message="I am O+ and can reach the hospital tomorrow morning.",
        )
        donated = DonorResponse(
            request=request5,
            donor=created["aditya@example.com"],
            status="donated",
            message="Happy to help.",
        )
        offered = DonorResponse(
            request=request1,
            donor=created["asha@example.com"],
            status="offered",
            message="I am O- and nearby. Available this evening.",
        )
        db.session.add_all([accepted, donated, offered])
        db.session.flush()

        donation = Donation(
            donor=created["aditya@example.com"],
            request=request5,
            hospital_name=request5.hospital_name,
            donated_on=today - timedelta(days=120),
            units=1,
            notes="Seeded historical donation.",
            verified_by=admin.id,
        )
        db.session.add(donation)
        created["aditya@example.com"].last_donation_date = today - timedelta(days=120)
        created["aditya@example.com"].is_available = True

        notifications = [
            Notification(
                user_id=requester.id,
                type="offer_received",
                title="New donor offer",
                body="Asha Rao (O-) offered to help with the request for Anita Kulkarni.",
                link=f"/requests/{request1.id}",
            ),
            Notification(
                user_id=created["asha@example.com"].id,
                type="request_nearby",
                title="A compatible request is nearby",
                body="An A+ request in Pune needs donors. Your O- group is compatible.",
                link=f"/requests/{request1.id}",
                is_read=True,
            ),
            Notification(
                user_id=created["vikram@example.com"].id,
                type="offer_accepted",
                title="Your offer was accepted",
                body=f"Ravi Kulkarni accepted your offer. Contact them on {requester.phone}.",
                link=f"/requests/{request4.id}",
            ),
        ]
        db.session.add_all(notifications)
        db.session.commit()

        print("Seed complete.")
        print("  Admin:      admin@bloodlink.local / Admin@12345")
        print("  Requester:  ravi@example.com / Requester@12345")
        print("  Donor:      asha@example.com / Donor@12345 (O-, Pune)")
        print("  Donor:      vikram@example.com / Donor@12345 (O+, Pune)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed BloodLink demo data")
    parser.add_argument("--reset", action="store_true", help="drop and recreate all tables")
    args = parser.parse_args()
    seed(reset=args.reset)
