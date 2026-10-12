"""Seed consultants and availability rules (FR-BOOK-001..010)."""
import sys
from datetime import date, time
from decimal import Decimal

from app.db.session import get_db
from app.models.booking import AvailabilityRule, ConsultantProfile
from app.models.user import User, UserRole
from app.services.booking import availability as avail

CONSULTANTS_TO_SEED = [
    {
        'email': 'consultant@palmistry.example.com',
        'headline': 'Spiritual & Vedic Palmistry Consultant',
        'bio': 'Guided over 500+ seekers through deep palm line analysis, life-trend forecasting, and holistic spiritual guidance.',
        'specializations': ['palmistry', 'spiritual_growth', 'career', 'astrology'],
        'modalities': ['video', 'chat'],
        'languages': ['English', 'Hindi'],
        'years_experience': 8,
        'session_rate': Decimal('45.00'),
        'total_sessions': 42,
        'avg_rating': Decimal('4.90'),
        'review_count': 38,
        'rules': [
            {'weekday': 0, 'start': time(10, 0), 'end': time(17, 0)},
            {'weekday': 2, 'start': time(10, 0), 'end': time(17, 0)},
            {'weekday': 4, 'start': time(10, 0), 'end': time(17, 0)},
        ],
    },
    {
        'email': 'reader@palmistry.example.com',
        'headline': 'Intuitive Tarot Master & Archetype Reader',
        'bio': 'Over 6 years of experience guiding life, relationship, and career decisions using Rider-Waite and Thoth decks.',
        'specializations': ['tarot', 'love', 'career', 'spiritual_growth'],
        'modalities': ['video', 'chat'],
        'languages': ['English'],
        'years_experience': 6,
        'session_rate': Decimal('35.00'),
        'total_sessions': 28,
        'avg_rating': Decimal('4.85'),
        'review_count': 24,
        'rules': [
            {'weekday': 1, 'start': time(11, 0), 'end': time(18, 0)},
            {'weekday': 3, 'start': time(11, 0), 'end': time(18, 0)},
            {'weekday': 5, 'start': time(11, 0), 'end': time(18, 0)},
        ],
    },
    {
        'email': 'consultant@gmail.com',
        'headline': 'Holistic Astrologer & Life Path Consultant',
        'bio': 'Integrating Vedic astrology, numerology, and palm analysis to reveal your karmic blueprint and growth opportunities.',
        'specializations': ['astrology', 'numerology', 'career', 'spiritual_growth'],
        'modalities': ['video', 'chat'],
        'languages': ['English', 'Hindi'],
        'years_experience': 10,
        'session_rate': Decimal('50.00'),
        'total_sessions': 65,
        'avg_rating': Decimal('4.95'),
        'review_count': 52,
        'rules': [
            {'weekday': 2, 'start': time(10, 0), 'end': time(17, 0)},
            {'weekday': 4, 'start': time(10, 0), 'end': time(17, 0)},
        ],
    },
]

def seed_consultants():
    db = next(get_db())
    try:
        for item in CONSULTANTS_TO_SEED:
            user = db.query(User).filter_by(email=item['email']).first()
            if not user:
                print(f"User {item['email']} not found, skipping")
                continue
            profile = db.query(ConsultantProfile).filter_by(user_id=user.id).first()
            if not profile:
                profile = ConsultantProfile(
                    user_id=user.id,
                    headline=item['headline'],
                    bio=item['bio'],
                    specializations=item['specializations'],
                    modalities=item['modalities'],
                    languages=item['languages'],
                    years_experience=item['years_experience'],
                    session_rate=item['session_rate'],
                    currency='USD',
                    session_duration_minutes=45,
                    buffer_minutes=15,
                    timezone='UTC',
                    is_accepting_bookings=True,
                    total_sessions=item['total_sessions'],
                    avg_rating=item['avg_rating'],
                    review_count=item['review_count'],
                )
                db.add(profile)
                db.commit()
                db.refresh(profile)
                print(f"Created profile for {item['email']}")
            else:
                profile.is_accepting_bookings = True
                profile.session_rate = item['session_rate']
                profile.headline = item['headline']
                profile.specializations = item['specializations']
                db.commit()
                print(f"Updated profile for {item['email']}")

            for r in item['rules']:
                rule_exists = db.query(AvailabilityRule).filter_by(
                    consultant_id=profile.id,
                    weekday=r['weekday']
                ).first()
                if not rule_exists:
                    rule = AvailabilityRule(
                        consultant_id=profile.id,
                        weekday=r['weekday'],
                        start_time=r['start'],
                        end_time=r['end'],
                        slot_duration_minutes=45,
                        buffer_minutes=15,
                        timezone='UTC',
                        effective_from=date.today(),
                        is_active=True,
                    )
                    db.add(rule)
            db.commit()
            slots_created = avail.extend_horizon_for_consultant(db, profile.id)
            db.commit()
            print(f"Materialized slots for {item['email']}: {slots_created}")
    finally:
        db.close()

if __name__ == '__main__':
    seed_consultants()
