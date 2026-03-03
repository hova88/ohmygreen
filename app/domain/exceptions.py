class DomainError(Exception):
    """Base class for domain-level errors."""


class InvalidCredentialsError(DomainError):
    pass


class NotAuthenticatedError(DomainError):
    pass


class InvalidSessionError(DomainError):
    pass


class InvalidInputError(DomainError):
    pass
