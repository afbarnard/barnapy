"""Collected parsing functions

The general pattern is to try to parse some text and convert it to a
value or otherwise return None.  If automatic exceptions or default
values are desired instead of None, consider `make_error_if_none` and
`make_default_if_none` in the `general` module.

Requires Python >= 3.4 for `re.fullmatch`.

Copyright (c) 2016 Aubrey Barnard.  This is free software released under
the MIT license.  See LICENSE for details.

"""

import builtins
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


# General parsing algorithm

def parse(text, patterns, constructors):
    """Parse the given text and convert it into a value or return None.

    Intended mainly as a general template algorithm for making
    pattern-based parsers.

    text: String to parse

    patterns: List of patterns to try

    constructors: List of constructors corresponding to the patterns

    """
    # Find the first matching pattern and use the corresponding
    # constructor to convert the text into a value
    for pattern, constructor in zip(patterns, constructors):
        match = pattern.fullmatch(text)
        if match is not None:
            return constructor(text)
    # Otherwise return None
    return None


# Parsing various literals

def int(text):
    """Return an integer parsed from the given text or None."""
    if integer_pattern.fullmatch(text) is not None:
        return builtins.int(text)
    else:
        return None


def float(text):
    """Return a float parsed from the given text or None."""
    if float_pattern.fullmatch(text) is not None:
        return builtins.float(text)
    else:
        return None


def bool(text):
    """Return a boolean parsed from the given text or None."""
    if bool_true_pattern.fullmatch(text) is not None:
        return True
    elif bool_false_pattern.fullmatch(text) is not None:
        return False
    else:
        return None


def literal(text):
    """Return a literal (int, float, bool, None) parsed from the given text.

    If the text is not parseable as a literal it is returned unharmed.

    """
    # Try parsing the literal in order of (assumed) frequency of types

    # Return empty as is
    if not text:
        return text
    # Integer
    elif integer_pattern.fullmatch(text) is not None:
        return builtins.int(text)
    # Float
    elif float_pattern.fullmatch(text) is not None:
        return builtins.float(text)
    # Boolean
    elif bool_true_pattern.fullmatch(text) is not None:
        return True
    elif bool_false_pattern.fullmatch(text) is not None:
        return False
    # None / Null
    elif none_pattern.fullmatch(text) is not None:
        return None
    # Whitespace, symbols, strings, or non-literals
    else:
        return text
