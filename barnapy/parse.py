"""Collected parsing functions

The general pattern is to try to parse some text and convert it to a
value or otherwise return None.  If automatic exceptions or default
values are desired instead of None, consider `make_error_if_none` and
`make_default_if_none` in the `general` module.

Requires Python >= 3.4 for `re.fullmatch`.

"""

# Copyright (c) 2017 Aubrey Barnard.  This is free software released
# under the MIT license.  See LICENSE for details.


import builtins
import datetime
import re


# Datalog predicate

_predicate_pattern = re.compile(
    r'\s*(\w[\w!?@$_-]*)(?:\s*\((.*)\))?\s*')
_list_split_pattern = re.compile(r'\s*,\s*')

def predicate(text):
    match = _predicate_pattern.match(text)
    if match:
        name, args_text = match.groups()
        if (args_text is None
                or len(args_text) == 0
                or args_text.isspace()):
            args = ()
        else:
            args = _list_split_pattern.split(args_text.strip())
        return name, args
    else:
        return None


# Array indexing

_array_index_pattern = re.compile(r'\s*(\w+)\s*\[\s*(\d+)\s*\]\s*')

def array_index(text):
    """Parse the text as array indexing syntax (e.g. "a[0]") and return
    a (name, index) pair.
    """
    match = _array_index_pattern.match(text)
    if match is not None:
        return match.groups()
    else:
        return None


# Regular expressions and patterns for value literals

"""Pattern that matches integers"""
integer_pattern = re.compile(r'\s*[+-]?\d+\s*')

# The following float regex is optimized to avoid backtracking by
# repeating the exponent regex
_exponent_regex = r'[eE][+-]?\d+'
_float_regex = (r'\s*[+-]?(?:\d+(?:\.\d*(?:{0})?|{0})|\.\d+(?:{0})?)\s*'
                .format(_exponent_regex))

"""Pattern that matches floats"""
float_pattern = re.compile(_float_regex)

"""Pattern that matches True (and yes)"""
bool_true_pattern = re.compile(r'\s*(?:true|yes)\s*', re.IGNORECASE)
"""Pattern that matches False (and no)"""
bool_false_pattern = re.compile(r'\s*(?:false|no)\s*', re.IGNORECASE)

"""Pattern that matches None (and null, nil, and NA)"""
none_pattern = re.compile(r'\s*n(?:a|one|ull|il)\s*', re.IGNORECASE)

"""Pattern that matches whitespace or the empty string"""
empty_pattern = re.compile(r'\s*')


# General parsing algorithm

def parse(text, detectors, constructors, default=None):
    """Parse the given text and convert it into a value.

    Return a (value, ok) pair per Go style.  The pair is (<value>, True)
    on parsing success and (<default>, False) on failure.  (Go style has
    been used here since parsing can, in general, return any value, and
    thus parsing success cannot be determined from the value alone.)

    Intended mainly as a general template algorithm for making
    pattern-based parsers.

    text: String to parse

    patterns: List of detectors to try

    constructors: List of constructors corresponding to the detectors

    """
    # Detect the first match and use the corresponding constructor to
    # convert the text into a value
    for detector, constructor in zip(detectors, constructors):
        if detector(text):
            return constructor(text), True
    # Otherwise return default
    return default, False


# Detecting and parsing various literals


def is_int(text):
    """Whether the given text can be parsed as an integer."""
    return integer_pattern.fullmatch(text) is not None


def int(text, default=None):
    """Return an integer parsed from the given text, else `default`."""
    return builtins.int(text) if is_int(text) else default


def is_float(text):
    """Whether the given text can be parsed as a float."""
    return float_pattern.fullmatch(text) is not None


def float(text, default=None):
    """Return a float parsed from the given text, else `default`."""
    return builtins.float(text) if is_float(text) else default


def is_bool(text):
    """Whether the given text can be parsed as a boolean."""
    return (bool_true_pattern.fullmatch(text) is not None
            or bool_false_pattern.fullmatch(text) is not None)


def bool(text, default=None):
    """Return a boolean parsed from the given text, else `default`."""
    if bool_true_pattern.fullmatch(text) is not None:
        return True
    elif bool_false_pattern.fullmatch(text) is not None:
        return False
    else:
        return default


# The following "literals" only have functions for detection because
# there is no obvious value to construct or return.  In particular, it
# makes no sense to return None as a sentinel value from a function that
# would also return None on success.  Other sentinel values are possible
# but likely very application-specific.


def is_none(text):
    """Whether the given text is None or a synonym (null, nil, na)."""
    return none_pattern.fullmatch(text) is not None


def is_empty(text):
    """Whether the given text is empty or only whitespace characters."""
    return empty_pattern.fullmatch(text) is not None


def literal(text, default=None):
    """Parse a literal (int, float, bool, None) from the given text.

    Return a (value, ok) pair per Go style.  If parsing is successful,
    then (<value>, True) is returned, otherwise (<default>, False) is
    returned.  This is needed for distinguishable parsing of None.

    """
    # Try parsing the literal in order of (assumed) frequency of types

    # Return empty as is
    if not text:
        return text, True
    # Integer
    elif integer_pattern.fullmatch(text) is not None:
        return builtins.int(text), True
    # Float
    elif float_pattern.fullmatch(text) is not None:
        return builtins.float(text), True
    # Boolean
    elif bool_true_pattern.fullmatch(text) is not None:
        return True, True
    elif bool_false_pattern.fullmatch(text) is not None:
        return False, True
    # None / Null
    elif none_pattern.fullmatch(text) is not None:
        return None, True
    # Whitespace, symbols, strings, or non-literals
    else:
        return default, False


# Dates and times


timestamp_pattern = re.compile(
    r'\s*(?P<year>\d{4})(?P<d_sep>\D?)(?P<month>\d{2})(?P=d_sep)(?P<day>\d{2})'
    r'(?P<ts_sep>.)'
    r'(?P<hour>\d{2})(?P<t_sep>\D?)(?P<minute>\d{2})(?P=t_sep)(?P<second>\d{2})'
    r'(?:[.,](?P<fractional_second>\d+))?(?P<tz>[+-]\d{4})?\s*'
    )

def timestamp(text, default=None):
    match = timestamp_pattern.fullmatch(text)
    if match is not None:
        groups = match.groupdict()
        # Fix the fractional second if given
        microsecond = groups.get('fractional_second')
        if microsecond is not None:
            # The fractional second must be a microsecond and have at
            # most 6 digits
            if len(microsecond) < 6:
                microsecond += '0' * (6 - len(microsecond))
            elif len(microsecond) > 6:
                microsecond = microsecond[:6]
            # Parse as an integer
            microsecond = int(microsecond)
        # Construct a TZ object if needed
        tz = groups.get('tz')
        if tz is not None:
            tz_str = groups['tz']
            delta = datetime.timedelta(
                hours=int(tz_str[1:3]), minutes=int(tz_str[3:]))
            if tz_str[0] == '-':
                tz = datetime.timezone(-delta)
            else:
                tz = datetime.timezone(delta)
        # Parse the fields and return as a datetime
        return datetime.datetime(
            year=int(groups['year']),
            month=int(groups['month']),
            day=int(groups['day']),
            hour=int(groups['hour']),
            minute=int(groups['minute']),
            second=int(groups['second']),
            microsecond=(microsecond
                         if microsecond is not None
                         else 0),
            tzinfo=tz,
            )
    return default
