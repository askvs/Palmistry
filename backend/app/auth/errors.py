# Auth errors mapped to API error codes.
class AuthError(Exception):
    code = "AUTH_ERROR"
    status_code = 401

    def __init__(self, message: str = "Authentication failed"):
        self.message = message
        super().__init__(message)


class InvalidCredentials(AuthError):
    code = "AUTH_FAILED"
    status_code = 401


class EmailAlreadyRegistered(AuthError):
    code = "EMAIL_ALREADY_REGISTERED"
    status_code = 409


class InvalidRefreshToken(AuthError):
    code = "INVALID_REFRESH_TOKEN"
    status_code = 401


class OAuthNotConfigured(AuthError):
    code = "OAUTH_NOT_CONFIGURED"
    status_code = 503


class WrongPortalError(AuthError):
    # Raised when account belongs to a different role portal.
    code = "WRONG_PORTAL"
    status_code = 403


class AdminSignupForbidden(AuthError):
    # Raised for admin signup without a valid invite code.
    code = "ADMIN_SIGNUP_FORBIDDEN"
    status_code = 403
