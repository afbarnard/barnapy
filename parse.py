# Collected parsing functions

import re


_predicate_pattern = re.compile(r'\s*(\w[\w!?@$_-]*)(?:\s*\((.*)\))?\s*')
_list_split_pattern = re.compile(r'\s*,\s*')

def predicate(text):
    match = _predicate_pattern.match(text)
    if match:
        name, args_text = match.groups()
        if (args_text is None or
                len(args_text) == 0 or
                args_text.isspace()):
            args = ()
        else:
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
        return match.groups()
    else:
        raise ValueError(
            'Could not parse as array and index: {}'.format(text))
