"""Domain errors for the live consultation & booking module."""
from __future__ import annotations


class BookingError(Exception):
    """Base class for every booking domain error."""

    code = "BOOKING_ERROR"
    status_code = 400

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.__class__.__doc__ or self.code
        super().__init__(self.message)


class NotAnConsultant(BookingError):
    """Only tarot readers, spiritual consultants and admins can offer sessions"""

    code = "NOT_AN_CONSULTANT"
    status_code = 403


class ConsultantProfileNotFound(BookingError):
    """Consultant profile not found"""

    code = "CONSULTANT_PROFILE_NOT_FOUND"
    status_code = 404


class ConsultantProfileIncomplete(BookingError):
    """This consultant profile is missing required details"""

    code = "CONSULTANT_PROFILE_INCOMPLETE"
    status_code = 400


class AvailabilityRuleNotFound(BookingError):
    """Availability rule not found"""

    code = "AVAILABILITY_RULE_NOT_FOUND"
    status_code = 404


class AvailabilityWindowInvalid(BookingError):
    """The availability window is invalid"""

    code = "AVAILABILITY_WINDOW_INVALID"
    status_code = 400


class AvailabilityRuleOverlap(BookingError):
    """This availability window overlaps a rule you already have"""

    code = "AVAILABILITY_RULE_OVERLAP"
    status_code = 409


class SlotNotFound(BookingError):
    """Availability slot not found"""

    code = "SLOT_NOT_FOUND"
    status_code = 404


class SlotNotBookable(BookingError):
    """This slot is no longer available"""

    code = "SLOT_NOT_BOOKABLE"
    status_code = 409


class BookingNotFound(BookingError):
    """Booking not found"""

    code = "BOOKING_NOT_FOUND"
    status_code = 404


class BookingNotAllowed(BookingError):
    """You are not allowed to perform this action on the booking"""

    code = "BOOKING_NOT_ALLOWED"
    status_code = 403


class InvalidBookingTransition(BookingError):
    """This booking cannot move to the requested status"""

    code = "INVALID_BOOKING_TRANSITION"
    status_code = 409


class BookingTooSoon(BookingError):
    """This session starts too soon to be booked"""

    code = "BOOKING_TOO_SOON"
    status_code = 409


class BookingTooFar(BookingError):
    """This session is outside the bookable horizon"""

    code = "BOOKING_TOO_FAR"
    status_code = 409


class BookingCancellationClosed(BookingError):
    """The free cancellation window for this session has closed"""

    code = "BOOKING_CANCELLATION_CLOSED"
    status_code = 409


class SessionNoteNotFound(BookingError):
    """Session note not found"""

    code = "SESSION_NOTE_NOT_FOUND"
    status_code = 404


class FeedbackNotAllowed(BookingError):
    """Feedback can only be left for a completed session"""

    code = "FEEDBACK_NOT_ALLOWED"
    status_code = 409


class FeedbackExists(BookingError):
    """You have already reviewed this session"""

    code = "FEEDBACK_EXISTS"
    status_code = 409

