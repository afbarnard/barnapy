# Collected parsing functions

import re


_predicate_pattern = re.compile(r'\s*(\w+)\s*\((.*)\)\s*')
_list_split_pattern = re.compile(r'\s*,\s*')

def predicate(text):
    match = _predicate_pattern.match(text)
    if match:
        name, args_text = match.groups((1, 2))
        args = _list_split_pattern.split(args_text.strip())
        return name, args
    else:
        raise ValueError(
            'Could not parse as predicate: {}'.format(text))

_array_index_pattern = re.compile(r'\s*(\w+)\s*\[\s*(\d+)\s*\]\s*')

def array_index(text):
    """Parses the text as array indexing syntax (e.g. "a[0]").  Returns
    a (name, index) pair.
    """
    match = _array_index_pattern.match(text)
    if match is not None:
        return match.groups((1, 2))
    else:
        raise ValueError(
            'Could not parse as array and index: {}'.format(text))
