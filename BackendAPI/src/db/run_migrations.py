"""Run Alembic migrations programmatically.

Usage:
    python -m src.db.run_migrations [upgrade|downgrade] [target]
Examples:
    python -m src.db.run_migrations upgrade head
    python -m src.db.run_migrations downgrade -1
"""

import sys
from typing import List

from alembic import command
from alembic.config import Config
from dotenv import load_dotenv

load_dotenv()


def main(argv: List[str]) -> None:
    cfg = Config("alembic.ini")
    if not argv:
        print("No arguments provided. Defaulting to 'upgrade head'.")
        command.upgrade(cfg, "head")
        return

    action = argv[0]
    target = argv[1] if len(argv) > 1 else "head"

    if action == "upgrade":
        command.upgrade(cfg, target)
    elif action == "downgrade":
        command.downgrade(cfg, target)
    else:
        print(f"Unknown action: {action}. Use 'upgrade' or 'downgrade'.")


if __name__ == "__main__":
    main(sys.argv[1:])
