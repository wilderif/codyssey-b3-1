"""Executable entry point for the Mini Redis CLI."""

from mini_redis.cli.repl import run_repl


def main():
    """Start the Mini Redis REPL."""
    run_repl()


if __name__ == "__main__":
    main()

