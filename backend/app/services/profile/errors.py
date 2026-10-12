"""Profile-domain errors mapped to API error codes (§49.14 envelope)."""


class ProfileError(Exception):
    code = "PROFILE_ERROR"
    status_code = 400

    def __init__(self, message: str = "Profile operation failed"):
        self.message = message
        super().__init__(message)


class AvatarTooLarge(ProfileError):
    code = "AVATAR_TOO_LARGE"
    status_code = 413


class UnsupportedAvatarFormat(ProfileError):
    code = "UNSUPPORTED_AVATAR_FORMAT"
    status_code = 415


class GoalNotFound(ProfileError):
    code = "GOAL_NOT_FOUND"
    status_code = 404


class AvatarNotFound(ProfileError):
    code = "AVATAR_NOT_FOUND"
    status_code = 404


class GoalLimitReached(ProfileError):
    code = "GOAL_LIMIT_REACHED"
    status_code = 400
