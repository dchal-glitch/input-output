import structlog
import sys
from typing import Dict, Any
from core.config import get_settings

settings = get_settings()


def configure_logging():
    """Configure structured logging"""
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = __name__):
    """Get a structured logger"""
    return structlog.get_logger(name)


class LoggingMiddleware:
    """Middleware for request/response logging"""
    
    def __init__(self, app):
        self.app = app
        self.logger = get_logger("middleware")
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # Log request
            self.logger.info(
                "Request started",
                method=scope.get("method"),
                path=scope.get("path"),
                query_string=scope.get("query_string", b"").decode(),
            )
        
        await self.app(scope, receive, send)
