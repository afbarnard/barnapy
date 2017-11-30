"""
Functions for handling arguments, both from the command line and for
APIs
"""

# Copyright (c) 2017 Aubrey Barnard.  This is free software released
# under the MIT license.  See LICENSE for details.


import collections
import re


long_option_assignment_pattern = re.compile(
    r'--([^=\s]+)(?:\s*=\s*(.*))?')


def parse(args, key_value_pattern=long_option_assignment_pattern):
    """
    Parse the given iterable of argument tokens.

    Returns a dictionary of the key-value pairs and a list of the
    positional arguments.

    This is meant to be a simple alternative to things like `optparse`.
    As such, it supports a limited syntax and leaves validation to the
    client.  Every key is given a value, either from the same token
    (assignment style) or the next token, unless the next token looks
    like another key, in which case the value is `None`.  Thus, flags
    must precede other keys or use the assignment style to avoid
    consuming the following value.  All other tokens are treated as
    positional arguments.  For example, the following tokens

        --flag --key val1 pos1 --key=val2 --flag= pos2 --flag

    are parsed into the following keyword and positional arguments

        {'flag': [None, '', None], 'key': ['val1', 'val2']}
        ['pos1', 'pos2']

    `key_value_pattern`: Regex that recognizes and parses key-value
        pairs.  The regex must have two groups: the key (required) and
        the value (optional).  The default is a regex that handles
        GNU-style long options, e.g. '--key val --key=val'.
    """
    kw_args = collections.defaultdict(list)
    idx_args = []
    # Process each argument.  Use a state machine for keywords awaiting
    # values to allow `args` to be an iterable and to avoid repeating
    # code to check if an argument is a keyword.
    key_awaits_value = None
    for arg in args:
        # Is this argument a keyword?
        match = key_value_pattern.match(arg)
        # This argument is a keyword
        if match is not None:
            # If there is a key awaiting a value then it doesn't get one
            # because this is already another key
            if key_awaits_value:
                kw_args[key_awaits_value].append(None)
                key_awaits_value = None
            # Unpack the match
            key, value = match.group(1, 2)
            # Was a value given or is it in the next arg?
            if value is not None:
                kw_args[key].append(value)
            else:
                key_awaits_value = key
        # This argument is a value
        elif key_awaits_value:
            kw_args[key_awaits_value].append(arg)
            key_awaits_value = None
        # This argument is positional
        else:
            idx_args.append(arg)
    # Give a null value to a trailing key
    if key_awaits_value:
        kw_args[key_awaits_value].append(None)
        key_awaits_value = None
    # Return both the keyword and positional arguments
    return kw_args, idx_args


# TODO object to represent keyword and positonal arguments
# TODO provenance
