#!/usr/bin/env python3
"""Run a command holding the workspace test lock, so only one test run happens at a time.

Two sessions, or a session and a subagent, running tests or database commands at once
break each other (the test database is shared). This script takes a global OS advisory
lock (`flock`) on `.claude/state/test.lock` before running the command:

- a second caller waits, saying which command holds the lock;
- after `WORKFLOW_LOCK_TIMEOUT` seconds (default 100, inside the Bash tool's 120 s; the
  Stop hook waits 300, inside its 900 s hook timeout) it gives up with exit code 75
  (`EX_TEMPFAIL`), naming the holder, without running its command;
- the OS releases the lock when the holder exits or dies, so no stale lock remains;
- a command already inside the lock (`WORKFLOW_LOCK_HELD` names this lock file) runs
  at once, so nested calls do not deadlock.

Usage, from the folder the command needs (it runs in the current folder):

    python3 scripts/run_locked.py -- <workspace test_command>     (from the root)
    python3 ../scripts/run_locked.py -- .venv/bin/pytest -q       (from backend/)

The Stop hook and `tdd.py` take the same lock through `held()`.
"""

from __future__ import annotations

import fcntl
import os
import subprocess
import sys
import time
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime

from workflow import ROOT

LOCK = ROOT / ".claude" / "state" / "test.lock"
HELD_ENV = "WORKFLOW_LOCK_HELD"
TIMEOUT_ENV = "WORKFLOW_LOCK_TIMEOUT"
DEFAULT_TIMEOUT = 100.0
STOP_HOOK_TIMEOUT = 300.0
TIMEOUT_EXIT_CODE = 75
POLL_SECONDS = 0.1


class LockTimeoutError(Exception):
    """The lock stayed busy past the timeout; the message names its holder."""


def holder() -> str:
    """Who holds the lock, as written by the holder.

    Returns:
        The holder line, or "unknown" when it cannot be read.
    """
    try:
        return LOCK.read_text(encoding="utf-8").strip() or "unknown"
    except OSError:
        return "unknown"


def timeout(default: float = DEFAULT_TIMEOUT) -> float:
    """Seconds to wait for the lock.

    Args:
        default: the caller's wait when `WORKFLOW_LOCK_TIMEOUT` is unset.

    Returns:
        `WORKFLOW_LOCK_TIMEOUT` when set, else the default.
    """
    return float(os.environ.get(TIMEOUT_ENV) or default)


@contextmanager
def held(label: str, default_wait: float = DEFAULT_TIMEOUT) -> Iterator[None]:
    """Hold the test lock while the block runs, waiting for it when busy.

    Args:
        label: what runs under the lock, shown to whoever waits.
        default_wait: seconds to wait when `WORKFLOW_LOCK_TIMEOUT` is unset.

    Yields:
        Nothing; the lock is held until the block ends.

    Raises:
        LockTimeoutError: the lock stayed busy past the timeout.
    """
    if os.environ.get(HELD_ENV) == str(LOCK):
        yield
        return
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    with LOCK.open("a+", encoding="utf-8") as handle:
        deadline = time.monotonic() + timeout(default_wait)
        announced = False
        while True:
            try:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    raise LockTimeoutError(f"test lock still held by: {holder()}") from None
                if not announced:
                    print(f"Waiting for the test lock, held by: {holder()}", file=sys.stderr)
                    announced = True
                time.sleep(POLL_SECONDS)
        handle.truncate(0)
        handle.write(f"pid {os.getpid()} since {datetime.now():%H:%M:%S}: {label}\n")
        handle.flush()
        previous = os.environ.get(HELD_ENV)
        os.environ[HELD_ENV] = str(LOCK)
        try:
            yield
        finally:
            if previous is None:
                os.environ.pop(HELD_ENV, None)
            else:
                os.environ[HELD_ENV] = previous
            handle.truncate(0)


def main(argv: list[str]) -> int:
    """Run the command after `--` under the lock.

    Args:
        argv: arguments after the script name.

    Returns:
        The command's exit code; 75 on lock timeout, 127 when the command is missing,
        2 on bad usage.
    """
    command = argv[1:] if argv[:1] == ["--"] else argv
    if not command:
        print("usage: run_locked.py -- <command> [args...]", file=sys.stderr)
        return 2
    try:
        with held(" ".join(command)):
            return subprocess.run(command, check=False).returncode
    except LockTimeoutError as error:
        print(error, file=sys.stderr)
        return TIMEOUT_EXIT_CODE
    except FileNotFoundError:
        print(f"command not found: {command[0]}", file=sys.stderr)
        return 127


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
