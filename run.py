"""
Entry point — run the Voice Call AI Agent server.
"""

import uvicorn
from app.config import settings


if __name__ == "__main__":
    uvicorn.run(
        "app.api.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
        log_level="info",
    )
