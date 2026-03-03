from .api import router as api_router
from .web import configure_templates, router as web_router

__all__ = ["api_router", "web_router", "configure_templates"]
