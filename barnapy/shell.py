"""Shell-like functionality"""

# Copyright (c) 2018 Aubrey Barnard.  This is free software released
# under the MIT license.  See LICENSE for details.


import os.path
import shlex
import shutil
import subprocess
import sys


class ShellError(Exception):
    pass


def resolve_path(path):
    return os.path.abspath(os.path.expanduser(path))


def resolve_executable(path): # TODO check if path exists or not?
    if os.path.sep in path:
        return resolve_path(path)
    else:
        resolved = shutil.which(path)
        if resolved is None:
            raise ShellError('Executable not found: {!r}'.format(path))
        return resolved


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


class Pipeline:
    """
    A convenient way to construct a pipeline of processes and read their
    output.  The processes will run in parallel with Python.
    """

    def __init__(self, *args):
        """The arguments are the same as for `pipe`."""
        self._argss = []
        self._popens = None
        if args:
            self.pipe(*args)

    def pipe(self, *args):
        """
        Add a command to this pipeline and return itself.

        `args`: The command as a sequence of arguments.  If `args`
            contains only one item and it is a list (or tuple), then use
            it as the command and arguments as for `subprocess.Popen`.
            Otherwise, all of the items are used as the command and
            arguments.  All items are converted to strings, the first
            item is split according to shell rules, and all of the
            resulting strings become the command and arguments.  This
            allows one to form commands like

                .pipe('ls -lhAd --color=never', pathlib1, pathlib2)
        """
        if self._popens is not None:
            raise ShellError('Pipeline cannot be modified after it has been assembled')
        elif len(args) == 0:
            raise ShellError('No command specified')
        elif len(args) == 1 and isinstance(args[0], (list, tuple)):
            self._argss.append(args[0])
        else:
            # Make sure all arguments are strings
            new_args = [str(a) for a in args]
            # Split the first argument
            new_args[0:1] = shlex.split(new_args[0])
            # Add this command to the pipeline
            self._argss.append(new_args)
        return self

    def _assemble(self):
        if len(self._argss) == 0:
            raise ShellError('Empty pipeline')
        elif self._popens is not None:
            raise ShellError('Pipeline cannot be rerun')
        popens = []
        last_idx = len(self._argss) - 1
        for idx, args in enumerate(self._argss):
            # Create this process, pipe its input from the previous
            # process (if any), and pipe its output to the next process.
            # Let the IO be binary except for the last process.
            process = subprocess.Popen(
                args,
                stdin=(popens[-1].stdout if len(popens) > 0 else None),
                stdout=subprocess.PIPE,
                universal_newlines=(idx == last_idx))
            # Close the previous process's stdout so that SIGPIPE works
            # as described in
            # https://docs.python.org/3/library/subprocess.html#replacing-shell-pipeline
            if len(popens) > 0:
                popens[-1].stdout.close()
            popens.append(process)
        self._popens = popens

    def readlines(self):
        """Return an iterator over the lines of output from this pipeline."""
        if self._popens is None:
            self._assemble()
        return iter(self._popens[-1].stdout)

    __iter__ = readlines

    def cleanup(self):
        """Call `wait` on each process in the pipeline to clean it up."""
        # Exhaust remaining input
        for line in self:
            pass
        # Wait on each process # TODO wait forward or backward?
        for process in self._popens:
            process.wait()

    # TODO Pipeline.run? (without reading output of pipeline, e.g. if output to file)
    # TODO Pipeline.reset?
    # TODO Pipeline input?
    # TODO Pipeline output other than stdout?
    # TODO Pipeline exit status à la bash (is it last command unless error?)
    # TODO async?


# TODO function to process a sequence of strings as the shell would a command line: variable substitution, executable and filename resolution, globbing?

# TODO process object (wrapping subprocess.Popen) that deals better with IO?
