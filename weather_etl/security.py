import hashlib
import secrets
from cryptography.fernet import Fernet
from datetime import datetime, timedelta
import structlog
from .config import settings

logger = structlog.get_logger()


class SecurityManager:
    def __init__(self):
        self.cipher = Fernet(settings.encryption_key_bytes)

    def encrypt_data(self, data: str) -> str:
        # encrypt sensitive data
        return self.cipher.encrypt(data.encode()).decode()

    def decrypt_data(self, encrypted_data: str) -> str:
        # decrypt sensitive data
        return self.cipher.decrypt(encrypted_data.encode()).decode()

    def anonymize_location(self, lat: float, lon: float) -> tuple:
        # Anonymize coords : GDPR Compilance
        # Round : reduce precision for privacy
        return round(lat, 2), round(lon, 2)

    def audit_log(self, action: str, user: str, resource: str):
        logger.info(
            "audit_event",
            action=action,
            user=user,
            resource=resource,
            timestamp=datetime.utcnow().isoformat(),
        )


class RateLimiter:
    def __init__(self, max_requests=100, window_seconds=3600):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}

    def is_allowed(self, client_id: str) -> bool:
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=self.window_seconds)

        if client_id not in self.requests:
            self.requests[client_id] = []

        # Clean old requests
        self.requests[client_id] = [
            req_time for req_time in self.requests[client_id] if req_time > window_start
        ]

        if len(self.requests[client_id]) >= self.max_requests:
            return False

        self.requests[client_id].append(now)
        return True


security_manager = SecurityManager()
rate_limiter = RateLimiter()
