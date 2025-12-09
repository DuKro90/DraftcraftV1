"""
Custom Throttling Classes for DraftCraft API
Rate limiting to prevent abuse and DDoS attacks
"""

from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class AnonBurstRateThrottle(AnonRateThrottle):
    """
    Anonymous users: 10 requests per minute (burst protection)
    """
    scope = 'anon_burst'


class AnonSustainedRateThrottle(AnonRateThrottle):
    """
    Anonymous users: 100 requests per hour (sustained load)
    """
    scope = 'anon_sustained'


class UserBurstRateThrottle(UserRateThrottle):
    """
    Authenticated users: 60 requests per minute
    """
    scope = 'user_burst'


class UserSustainedRateThrottle(UserRateThrottle):
    """
    Authenticated users: 1000 requests per hour
    """
    scope = 'user_sustained'


class DocumentUploadRateThrottle(UserRateThrottle):
    """
    Document uploads: 10 per hour (processing-intensive)
    """
    scope = 'document_upload'


class AuthenticationRateThrottle(AnonRateThrottle):
    """
    Authentication endpoints: 5 per minute (brute-force protection)
    """
    scope = 'auth'
