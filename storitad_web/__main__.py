from __future__ import annotations

import uvicorn

from . import config
from .app import create_app


def main() -> None:
    cfg = config.load()
    uvicorn.run(create_app(cfg), host="127.0.0.1", port=cfg.port)


if __name__ == "__main__":
    main()
