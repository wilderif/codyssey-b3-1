"""Interactive REPL loop for Mini Redis."""

from mini_redis.cli.parser import execute_command
from mini_redis.core.store import MiniRedis


PROMPT = "mini-redis> "


def run_repl(input_func=input, output_func=print):
    """Run the interactive command loop until exit, quit, or EOF."""
    store = MiniRedis()
    while True:
        try:
            line = input_func(PROMPT)
        except EOFError:
            break
        result = execute_command(store, line)
        if result is None:
            break
        if result != "":
            output_func(result)

