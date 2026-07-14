"""Command parsing, dispatch, and REPL for Mini Redis."""

import shlex

from mini_redis.store import MiniRedis


PROMPT = "mini-redis> "


def execute_command(store, line):
    """Parse and execute one command line against a MiniRedis store."""
    try:
        parts = shlex.split(line)
    except ValueError as error:
        return f"(error) ERR {error}"

    if not parts:
        return ""
    command = parts[0].upper()

    if command == "SET":
        if len(parts) != 3:
            return _wrong_args(command)
        return store.set(parts[1], parts[2])
    if command == "GET":
        if len(parts) != 2:
            return _wrong_args(command)
        return store.get(parts[1])
    if command == "DEL":
        if len(parts) != 2:
            return _wrong_args(command)
        return store.delete(parts[1])
    if command == "EXISTS":
        if len(parts) != 2:
            return _wrong_args(command)
        return store.exists(parts[1])
    if command == "DBSIZE":
        if len(parts) != 1:
            return _wrong_args(command)
        return store.dbsize()
    if command == "KEYS":
        if len(parts) != 1:
            return _wrong_args(command)
        return store.keys()
    if command == "CONFIG":
        valid_config = (
            len(parts) == 4
            and parts[1].upper() == "SET"
            and parts[2].lower() == "maxmemory"
        )
        if not valid_config:
            return _wrong_args(command)
        return store.config_set_maxmemory(parts[3])
    if command == "INFO":
        if len(parts) != 2 or parts[1].lower() != "memory":
            return _wrong_args(command)
        return store.info_memory()
    if command == "EXPIRE":
        if len(parts) != 3:
            return _wrong_args(command)
        return store.expire(parts[1], parts[2])
    if command == "TTL":
        if len(parts) != 2:
            return _wrong_args(command)
        return store.ttl(parts[1])
    if command in ("EXIT", "QUIT"):
        if len(parts) != 1:
            return _wrong_args(command)
        return None
    return f"(error) ERR unknown command '{parts[0]}'"


def _wrong_args(command):
    """Return a Redis-style wrong-arity error."""
    return f"(error) ERR wrong number of arguments for '{command}' command"


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
        if result:
            output_func(result)
