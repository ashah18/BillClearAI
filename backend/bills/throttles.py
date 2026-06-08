from rest_framework.throttling import UserRateThrottle


class BillUploadThrottle(UserRateThrottle):
    """10 bill uploads per hour per authenticated user."""

    scope = "bill_upload"


class ChatThrottle(UserRateThrottle):
    """30 chat messages per hour per authenticated user."""

    scope = "chat"


class DisputeThrottle(UserRateThrottle):
    """10 dispute letter generations per hour per authenticated user."""

    scope = "dispute"


class ReanalyzeThrottle(UserRateThrottle):
    """5 bill re-analyses per hour per authenticated user."""

    scope = "reanalyze"
