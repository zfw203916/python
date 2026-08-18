from __future__ import annotations
from pathlib import Path

from src.app.models.student import Student

DEFAULT_OUTPUT_DIR = Path("data/fixtures")


def main(self) -> None:
    """CLI entry point."""

    self.test_function = Student.test_get_function


if __name__ == "__main__":
    main(10)
