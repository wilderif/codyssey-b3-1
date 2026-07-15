"""CLI parsing and REPL behavior tests."""

from mini_redis.cli import PROMPT, execute_command, run_repl
from mini_redis.store import MiniRedis


def test_commands_are_case_insensitive_and_empty_input_is_ignored():
    """Command and subcommand case do not matter, and blank input is silent."""
    store = MiniRedis()

    assert execute_command(store, "set key value") == "OK"
    assert execute_command(store, "gEt key") == '"value"'
    assert execute_command(store, "config set MAXMEMORY 0") == "OK"
    assert execute_command(store, "info MEMORY").startswith("used_memory:")
    assert execute_command(store, "   ") == ""


def test_exit_and_quit_stop_command_execution():
    """EXIT and QUIT return the REPL stop signal with no arguments only."""
    store = MiniRedis()

    assert execute_command(store, "exit") is None
    assert execute_command(store, "QUIT") is None
    assert execute_command(store, "exit now") == (
        "(error) ERR wrong number of arguments for 'EXIT' command"
    )


def test_repl_uses_prompt_prints_results_and_stops_on_quit():
    """The REPL repeats input and output until a quit command."""
    commands = iter(["SET key value", "GET key", "quit"])
    prompts = []
    outputs = []

    def read_command(prompt):
        """Record each prompt and return the next command."""
        prompts.append(prompt)
        return next(commands)

    run_repl(input_func=read_command, output_func=outputs.append)

    assert prompts == [PROMPT, PROMPT, PROMPT]
    assert outputs == ["OK", '"value"']


def test_repl_stops_cleanly_on_end_of_input():
    """EOF exits without printing an error."""
    prompts = []
    outputs = []

    def end_input(prompt):
        """Record the prompt and simulate closed standard input."""
        prompts.append(prompt)
        raise EOFError

    run_repl(input_func=end_input, output_func=outputs.append)

    assert prompts == [PROMPT]
    assert outputs == []


def test_repl_stops_cleanly_on_keyboard_interrupt():
    """A keyboard interrupt exits without propagating an exception."""
    prompts = []
    outputs = []

    def interrupt_input(prompt):
        """Record the prompt and simulate Ctrl+C during input."""
        prompts.append(prompt)
        raise KeyboardInterrupt

    run_repl(input_func=interrupt_input, output_func=outputs.append)

    assert prompts == [PROMPT]
    assert outputs == [""]
