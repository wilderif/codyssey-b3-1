"""Command parsing and dispatch for the Mini Redis CLI."""

import shlex


def parse_line(line):
    """Split an input line while allowing quoted values."""
    try:
        return shlex.split(line)
    except ValueError as exc:
        return ["__parse_error__", str(exc)]


def execute_command(store, line):
    """Parse and execute one command line against a MiniRedis store."""
    parts = parse_line(line)
    if len(parts) == 0:
        return ""
    if parts[0] == "__parse_error__":
        return "(error) ERR " + parts[1]
    command = parts[0].upper()

    if command == "SET":
        if len(parts) != 3:
            return _wrong_args("SET")
        return store.set(parts[1], parts[2])
    if command == "GET":
        if len(parts) != 2:
            return _wrong_args("GET")
        return store.get(parts[1])
    if command == "DEL":
        if len(parts) != 2:
            return _wrong_args("DEL")
        return store.delete(parts[1])
    if command == "EXISTS":
        if len(parts) != 2:
            return _wrong_args("EXISTS")
        return store.exists(parts[1])
    if command == "DBSIZE":
        if len(parts) != 1:
            return _wrong_args("DBSIZE")
        return store.dbsize()
    if command == "KEYS":
        if len(parts) != 1:
            return _wrong_args("KEYS")
        return store.keys()
    if command == "CONFIG":
        if len(parts) != 4 or parts[1].upper() != "SET" or parts[2].lower() != "maxmemory":
            return _wrong_args("CONFIG")
        return store.config_set_maxmemory(parts[3])
    if command == "INFO":
        if len(parts) != 2 or parts[1].lower() != "memory":
            return _wrong_args("INFO")
        return store.info_memory()
    if command == "EXPIRE":
        if len(parts) != 3:
            return _wrong_args("EXPIRE")
        return store.expire(parts[1], parts[2])
    if command == "TTL":
        if len(parts) != 2:
            return _wrong_args("TTL")
        return store.ttl(parts[1])
    if command == "EXIT" or command == "QUIT":
        if len(parts) != 1:
            return _wrong_args(command)
        return None
    return "(error) ERR unknown command '" + parts[0] + "'"


def _wrong_args(command):
    """Return a Redis-style wrong-arity error."""
    return "(error) ERR wrong number of arguments for '" + command + "' command"

