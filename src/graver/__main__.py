"""Run graver through Python's module-execution protocol."""

from graver.cli import app


def main() -> None:
    """Invoke the same command application as the installed console script."""
    app()


if __name__ == "__main__":  # pragma: no cover
    main()
