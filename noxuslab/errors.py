"""Typed errors raised by `noxuslab`. One base, three concrete cases."""


class NoxusLabError(Exception):
    """Anything noxuslab raises on purpose."""


class NotFound(NoxusLabError):
    """A resource referenced by id does not exist (locally or remotely)."""


class BadFile(NoxusLabError):
    """A file is missing, malformed, or refuses an unsafe overwrite."""


class AuthMissing(NoxusLabError):
    """`NOXUS_API_KEY` is unset and we need it to call the backend."""
