"""Wrapper module for the standard logging module that provides a
sensible default configuration and {}-style formatting.

Copyright (c) 2016 Aubrey Barnard.  This is free software released under
the MIT license.  See LICENSE for details.
"""

import io
import logging as _logging
import os
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


def log_runtime_environment(logger=None, level=_logging.INFO):
    # Get logger
    if logger is None:
        logger = getLogger()
    # Log environment
    logger.log(level, 'Python {}', sys.version.replace('\n', ' '))
    logger.log(level, 'executable: {}', sys.executable)
    logger.log(level,
               'version: {0.major}.{0.minor}.{0.micro}-{0.releaselevel}.'
                   '{0.serial} running on {1} {2.major}.{2.minor}.'
                   '{2.micro}-{2.releaselevel}.{2.serial}',
               sys.version_info,
               sys.implementation.name,
               sys.implementation.version)
    logger.log(level, 'sys.path: {}', sys.path)
    logger.log(level, 'uname: {}', ' '.join(os.uname()))
    logger.log(level, 'host: {}', socket.getfqdn())
    logger.log(level, 'pid: {}', os.getpid())
    logger.log(level, 'user: {}, uid: {}, euid: {}, gid: {}, egid: {}',
               os.getlogin(), os.getuid(), os.geteuid(),
               os.getgid(), os.getegid())
    logger.log(level, 'cwd: {}', os.getcwd())
    logger.log(level, 'command line: {}', sys.argv)
