from __future__ import annotations

import logging

from fastapi import FastAPI

from .api.routes import router
from .config import get_settings
from .database import Base, engine
from . import models as _models

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name)
    app.include_router(router)

    @app.on_event("startup")
    def startup() -> None:
        if settings.environment in {"local", "test"}:
            Base.metadata.create_all(bind=engine)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
