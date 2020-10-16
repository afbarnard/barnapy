"""
Wrapper module for the standard logging module that provides a
sensible default configuration and {}-style formatting.
"""

# Copyright (c) 2017 Aubrey Barnard.  This is free software released
# under the MIT license.  See LICENSE for details.


import collections
import io
import logging as _logging
import os
import platform
import socket
import sys

# Export same API as standard logging
from logging import *


class LogRecord(_logging.LogRecord):
    """LogRecord that does {}-style formatting."""

    def getMessage(self):
        return str(self.msg).format(*self.args)

    # FIXME Note that in the following an extra argument is passed when
    # logging a dict.  This is because the logging module interprets a
    # single dict argument as like **kwargs.  (!)  See
    # `LogRecord.__init__` in
    # https://hg.python.org/cpython/file/3.4/Lib/logging/__init__.py.


def log_record_factory(*args, **kwargs):
    return LogRecord(*args, **kwargs)


def default_config(file=None, level=_logging.INFO):
    """Set up the logging system with a default configuration."""
    format='{asctime} {levelname} {name}: {message}'
    datefmt='%Y-%m-%dT%H:%M:%S'
    style='{'
    # Handle filenames, streams, and default.  This has to be done with
    # separate calls because basicConfig won't allow multiple
    # conflicting arguments to be specified, even if they are None.
    if file is None:
        _logging.basicConfig(
            format=format, datefmt=datefmt, style=style, level=level)
    elif isinstance(file, str):
        _logging.basicConfig(
            format=format, datefmt=datefmt, style=style, level=level,
            filename=file)
    elif isinstance(file, io.IOBase):
        _logging.basicConfig(
            format=format, datefmt=datefmt, style=style, level=level,
            stream=file)
    else:
        raise ValueError('Not a file or filename: {}'.format(file))
    # Set factory to handle {}-style formatting in messages
    _logging.setLogRecordFactory(log_record_factory)


# Provide stubs for functions that are not universally available
try:
    osgetresuid = os.getresuid
except:
    def osgetresuid():
        return (None, None, None)
try:
    osgetresgid = os.getresgid
except:
    def osgetresgid():
        return (None, None, None)


runtime_environment_elements = collections.OrderedDict((
    # Python context
    ('python', ('Python {}', lambda: sys.version.replace('\n', ' '))),
    ('version', (
        'version: {0[0].major}.{0[0].minor}.{0[0].micro}-'
        '{0[0].releaselevel}.{0[0].serial} running on {0[1]} '
        '{0[2].major}.{0[2].minor}.{0[2].micro}-'
        '{0[2].releaselevel}.{0[2].serial}',
        lambda: (sys.version_info,
                 sys.implementation.name,
                 sys.implementation.version))),
    ('executable', lambda: sys.executable),

    # Calling context
    ('argv', lambda: sys.argv),
    ('path', lambda: sys.path),
    ('cwd', os.getcwd),

    # OS context
    ('os', ('os: {0.system} {0.node} {0.release} ({0.version}) '
            '{0.machine} {0.processor}',
            platform.uname)),
    ('host', socket.getfqdn),

    # Process context
    ('pid', os.getpid),
    ('user', os.getlogin),
    ('uid', ('uid: real: {0[0]}, eff: {0[1]}, saved: {0[2]}',
             osgetresuid)),
    ('gid', ('gid: real: {0[0]}, eff: {0[1]}, saved: {0[2]}',
             osgetresgid)),
))
"""
Keys, messages, and value-getting functions for gathering
information about the runtime environment.
"""


def log_runtime_environment(
        logger=None,
        level=_logging.INFO,
        what=runtime_environment_elements.keys(),
):
    """
    Log information about the current runtime environment.

    `what`: What elements of `runtime_environment_elements` to log.
    """
    if logger is None:
        logger = getLogger()
    for key in what:
        # Returns `None` if bad key
        val = runtime_environment_elements.get(key)
        if isinstance(val, tuple):
            message, function = val
        elif val:
            message = key + ': {}'
            function = val
        else:
            # Invalid key or value.  Just skip to the next one.
            continue
        logger.log(level, message, function())

# Names of logging levels
level_names = {
    'CRITICAL',
    'FATAL',
    'ERROR',
    'WARN',
    'WARNING',
    'INFO',
    'DEBUG',
    'NOTSET',
}
