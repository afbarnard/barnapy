# Wrapper module for the standard logging module that provides a
# sensible default configuration and {}-style formatting.

import logging as _logging

# Export same API as standard logging
from logging import *


class LogRecord(_logging.LogRecord):
    """LogRecord that does {}-style formatting."""

    def getMessage(self):
        return str(self.msg).format(*self.args)


def log_record_factory(*args, **kwargs):
    return LogRecord(*args, **kwargs)


def default_config():
    """Sets up the logging system with a default configuration."""
    _logging.basicConfig(
        format='{asctime} {levelname} {name}: {message}',
        datefmt='%Y-%m-%d %H:%M:%S',
        style='{',
        level=_logging.INFO,
        )
    _logging.setLogRecordFactory(log_record_factory)
