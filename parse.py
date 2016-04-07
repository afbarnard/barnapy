# Collected parsing functions

import re


# TODO figure out how to handle options for failed parsing: returning a
# default value, raising an exception, logging a message (callable with
# a message), golang paradigm of returning (ok, value) pair

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

_integer_pattern = re.compile(r'\s*[+-]?\d+\s*')

_int = int
def int(text, otherwise=None):
    match = _integer_pattern.fullmatch(text)
    if match is not None:
        return _int(text)
    elif otherwise is None:
        return None
    elif (isinstance(otherwise, type) and
          issubclass(otherwise, BaseException)):
        raise otherwise('Could not parse as integer: {}'.format(text))
    else:
        return otherwise

# The following float regex is optimized to avoid backtracking
_exponent_regex = r'[eE][+-]?\d+'
_float_regex = r'\s*[+-]?(?:\d+(?:\.\d*(?:{0})?|{0})|\.\d+(?:{0})?)\s*'.format(_exponent_regex)
_float_pattern = re.compile(_float_regex)

_float = float
def float(text, otherwise=None):
    match = _float_pattern.fullmatch(text)
    if match is not None:
        return _float(text)
    elif otherwise is None:
        return None
    elif (isinstance(otherwise, type) and
          issubclass(otherwise, BaseException)):
        raise otherwise('Could not parse as float: {}'.format(text))
    else:
        return otherwise
