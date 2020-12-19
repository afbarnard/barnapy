"""
Functions for handling arguments, both from the command line and for
APIs.
"""

# Copyright (c) 2017, 2020 Aubrey Barnard.
#
# This is free, open software released under the MIT license.  See
# `LICENSE` for details.


import collections
import re

from . import parse as parselib


long_option_pattern = re.compile(r'--([^=\s]+)(?:\s*=\s*(.*))?')


# A unique object that is not `None`.  Float values are not cached:
# `float('nan') is float('nan')` -> `False`.
_Unset = float('nan')


def parse(
        args,
        kv_pattern=long_option_pattern,
        value_parser=None,
        value_if_unspecified=True,
        unspecified_values=(),
        args_separator='--',
        reduce_values=None,
):
    """
    Parse the given iterable of argument tokens.

    Return a dictionary of (key: str, values: list[object]) pairs, the
    keyword arguments, and a list of values, the positional arguments.
    Each key maps to a list of values in order to accommodate multiple
    associated values.  Which of the values gets returned can be
    controlled with `reduce_values`.

    This is meant to be a simple alternative to things like `argparse`.
    As such, it supports a limited syntax and leaves validation to the
    client.  Every key is given a value, either from the same token
    (assignment style) or the next token, unless the next token looks
    like another key, in which case the value is `None`.  Thus, flags
    must precede other keys or use the assignment style to avoid
    consuming the following value.  All other tokens are treated as
    positional arguments.  For example, the following tokens

        --flag --key val1 pos1 --key=val2 --flag= pos2 --flag -- --pos3

    are parsed into the following keyword and positional arguments

        {'flag': [True, True, True], 'key': ['val1', 'val2']}
        ['pos1', 'pos2', '--pos3']

    `kv_pattern`: re.Pattern

        Regex that recognizes and parses key-value pairs.  The regex
        must have two groups: the key (required) and the value
        (optional).  The default is a regex that handles GNU-style long
        options, e.g. '--key val --key=val'.

    `value_parser`: f(str) -> object

        A function that converts each value argument into a Python
        value, if possible, and otherwise just returns the original
        argument.  See `parse_literal`.

    `reduce_values`: f(key: str, vals: list) -> value

        A function that post-processes each item in the dictionary of
        keyword arguments.  This is intended as a convenience for
        reducing a list of multiple values into a single value so that
        one doesn't need to deal with lists in the returned keyword
        arguments.  If `None`, no post-processing is done.

        See `pick_first_value`, `pick_last_value`,
        `unwrap_single_values`.
    """
    kw_args = collections.defaultdict(list)
    idx_args = []
    # Process each argument.  Use a simple state machine for keywords
    # awaiting values to allow `args` to be an iterable and to avoid
    # repeating code to check if an argument is a keyword.
    keys_enabled = True
    key_awaits_value = None
    for arg in args:
        # Track the presence of key and value.  `None` is a valid value
        # so use `_Unset` as the sentinel instead.
        key = None
        val = _Unset
        # Handle the "only arguments hereafter" separator
        if arg == args_separator:
            keys_enabled = False
            # Clear the arguments separator so it is no longer
            # recognized and subsequent occurrences will just be treated
            # as a plain argument
            args_separator = float('nan') # Nothing compares equal
            continue
        # Parse keyword arguments.  Attempt the match regardless of
        # `keys_enabled` to keep the branching structure flatter.
        match = kv_pattern.fullmatch(arg)
        if keys_enabled and match is not None:
            key, val = match.groups()
            if val is None:
                val = _Unset
        else:
            val = arg
        # Replace "unspecified" values
        if val in unspecified_values:
            val = value_if_unspecified
        # Otherwise parse the value (if any)
        elif value_parser is not None and val is not _Unset:
            val = value_parser(val)
        # Value argument
        if key is None:
            # Value argument for previous key
            if keys_enabled and key_awaits_value is not None:
                kw_args[key_awaits_value].append(val)
                key_awaits_value = None
            # Order argument
            else:
                idx_args.append(val)
        # Key argument (with a possible value)
        else:
            # If there is a key awaiting a value then it doesn't get one
            # because this is already another key
            if key_awaits_value is not None:
                kw_args[key_awaits_value].append(value_if_unspecified)
                key_awaits_value = None
            # Was a value given or is it in the next arg?
            if val is _Unset:
                key_awaits_value = key
            else:
                kw_args[key].append(val)
    # Give the default value to a trailing key
    if key_awaits_value is not None:
        kw_args[key_awaits_value].append(value_if_unspecified)
        key_awaits_value = None
    # Reduce multiple values if requested
    if reduce_values is not None:
        kw_args = {k: reduce_values(k, v) for (k, v) in kw_args.items()}
    # Return both the keyword and positional arguments
    return kw_args, idx_args


def pick_first_value(key, vals):
    """
    Pick the first item in each list in a mapping from keys to sequences
    of values.  Return a dictionary of keys and first values.
    """
    return vals[0]

def pick_last_value(key, vals):
    """
    Pick the last item in each list in a mapping from keys to sequences
    of values.  Return a dictionary of keys and last values.
    """
    return vals[-1]

def unwrap_single_values(key, vals):
    """
    Replace lists containing only a single item with that item.  Return
    a dictionary mapping the same keys to single values or lists of at
    least two values.
    """
    if len(vals) == 1:
        return vals[0]
    else:
        return vals


def parse_literal(text):
    """
    Parse the given text as a Python literal, if possible.  Otherwise
    just return the text.  Useful as a "value parser" for `parse`.

    A Python literal is anything recognized by `ast.literal_eval`.
    """
    obj, err = parselib.pyliteral_err(text)
    return obj if err is None else text


# TODO object to represent keyword and positonal arguments
# TODO provenance
