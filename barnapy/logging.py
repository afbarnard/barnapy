"""
Wrapper module for the standard logging module that provides a
sensible default configuration and {}-style formatting.
"""

# Copyright (c) 2015-2018, 2020, 2023 Aubrey Barnard.
#
# This is free software released under the MIT license.  See LICENSE for
# details.


import collections
import io
import logging as _logging
import os
import platform
import socket
import string
import sys

# Export same API as standard logging
from logging import *


class CurlyBraceFormatLogRecord(_logging.LogRecord):
    """LogRecord that does {}-style formatting."""

    def getMessage(self):
        return str(self.msg).format(*self.args, **self.__dict__)

    # FIXME Note that in the following an extra argument is passed when
    # logging a dict.  This is because the logging module interprets a
    # single dict argument as like **kwargs.  (!)  See
    # `LogRecord.__init__` in
    # https://hg.python.org/cpython/file/3.4/Lib/logging/__init__.py.


# For backwards compatibility (although I can't find any references to
# 'LogRecord' in my code)
class LogRecord(CurlyBraceFormatLogRecord): # TODO remove in v0.5

    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)
        warnings.warn(
            "'barnapy.logging.LogRecord' is deprecated "
            "and will be removed in v0.5.  "
            "Use 'barnapy.logging.CurlyBraceFormatLogRecord' instead.",
            DeprecationWarning, stacklevel=2)


class TemplateStringLogRecord(_logging.LogRecord):
    """
    'LogRecord' that does formatting with template strings
    (https://docs.python.org/3/library/string.html#template-strings).
    """

    def getMessage(self):
        # Always convert the message to a string first because it may be
        # some sort of object (e.g., see
        # https://docs.python.org/3/howto/logging-cookbook.html#use-of-alternative-formatting-styles)
        template = string.Template(str(self.msg))
        return template.safe_substitute(self.__dict__)


def log_record_factory(*args, **kwargs):
    return CurlyBraceFormatLogRecord(*args, **kwargs)


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


class ConfigurableLogger(_logging.Logger):
    """
    Logger that can be configured with a message formatting style so
    that multiple loggers with different formatting styles can be used
    simultaneously.
    """

    def config(self, *, msg_fmt_style='{'):
        if msg_fmt_style not in _logging._STYLES:
            raise ValueError('Style must be one of: {}'.format(
                ','.join(_logging._STYLES.keys())))
        if msg_fmt_style == '{':
            self._LogRecord = CurlyBraceFormatLogRecord
        elif msg_fmt_style == '$':
            self._LogRecord = TemplateStringLogRecord
        else:
            self._LogRecord = _logging.LogRecord

    def makeRecord(self, name, level, fn, lno, msg, args, exc_info,
                   func=None, extra=None, sinfo=None):
        # Don't use the log record factory as that is global and can't
        # be configured per logger.  Just directly construct a log
        # record with the appropriate arguments.
        record = self._LogRecord(
            name, level, fn, lno, msg, args, exc_info, func, sinfo)
        if extra is not None:
            record.__dict__.update(extra)
        return record

    def _log(self, level, msg, args, exc_info=None, extra=None, stack_info=None, **kwds):
        if isinstance(extra, dict):
            extra.update(kwds)
        elif extra is None:
            extra = kwds
        super()._log(level, msg, args, exc_info, extra, stack_info)


def getLogger(name=None, msg_fmt_style=None):
    """
    Return a logger configured with the given arguments (if any).
    """
    # Temporarily switch the Logger class to a configurable logger.
    # Acquire the logging lock since this messes around with the module
    # state.
    if msg_fmt_style is None:
        return _logging.getLogger(name)
    try:
        _logging._lock.acquire()
        # Save the original logger class
        logger_class = _logging.getLoggerClass()
        # Get a configurable logger
        _logging.setLoggerClass(ConfigurableLogger)
        logger = _logging.getLogger(name)
        # Restore the original logger class
        _logging.setLoggerClass(logger_class)
        # Configure the logger
        logger.config(msg_fmt_style=msg_fmt_style)
        return logger
    finally:
        _logging._lock.release()


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


"""
Names of recognized logging levels and their corresponding level numbers
"""
name2level = {
    'critical': CRITICAL,
    'fatal': FATAL,
    'error': ERROR,
    'warn': WARNING,
    'warning': WARNING,
    'info': INFO,
    'debug': DEBUG,
    'notset': NOTSET,
}
for (name, level) in list(name2level.items()):
    name2level[name.upper()] = level


def parse_level_name(
        name: str | None,
        default: int=None,
) -> tuple[int | None, str | None]:
    """
    Interpret the given name as a log level name and return the
    corresponding log level number in a (level number, error message)
    pair.

    Per Go error handling style, if there was an error, then the message
    explains it.  Otherwise, `None` indicates no error.
    """
    if name is None:
        return (default, None)
    if not isinstance(name, str):
        return (default, f'Log level name is not a string: {name!r}')
    name = name.strip()
    level = name2level.get(name.lower())
    if level is None:
        names = ', '.join(name2level.keys())
        return (default, f'Unrecognized log level name: {name!r}\n'
                f'  Expected one of: {names}')
    return (level, None)
