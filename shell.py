"""Shell-like functionality

Copyright (c) 2016 Aubrey Barnard.  This is free software released under
the MIT license.  See LICENSE for details.
"""

import os.path
import shutil
import subprocess
import sys


class ShellError(Exception):
    pass


def resolve_path(path):
    return os.path.abspath(os.path.expanduser(path))


def resolve_executable(path):
    if os.path.sep in path:
        return resolve_path(path)
    else:
        return shutil.which(path)


def run(executable, *args):
    executable = resolve_executable(executable)
    command = [executable]
    command.extend(args)
    # Run program
    with subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=sys.stderr,
            universal_newlines=True) as process:
        # Capture stdout.  Stderr is inherited, not captured.
        out, err = process.communicate()
        assert err is None
        if process.returncode == 0:
            return out
        elif process.returncode < 0:
            raise ShellError(
                'Process exited with signal: {}'
                .format(-process.returncode),
                out)
        else:
            raise ShellError(
                'Process exited with error status: {}'
                .format(process.returncode),
                out)

# TODO function to process a sequence of strings as the shell would a command line: variable substitution, executable and filename resolution, globbing?

# TODO process object (wrapping subprocess.Popen) that deals better with IO?
