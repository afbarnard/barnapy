"""Collected parsing functionality

The parsing functions try to parse some text and convert it to a value
or otherwise return None.  If automatic exceptions or default values are
desired instead of None, consider `make_error_if_none` and
`make_default_if_none` in the `general` module.

Requires Python >= 3.4 for `re.fullmatch`.

"""

# Copyright (c) 2017 Aubrey Barnard.  This is free software released
# under the MIT license.  See LICENSE for details.


import builtins
import enum
import datetime
import re


# Patterns for lexical analysis


# Whitespace

"""Pattern that matches all whitespace"""
space_pattern = re.compile(r'\s+')

"""Pattern that matches plain (non-newline) whitespace"""
space_plain_pattern = re.compile(r'[ \t\f\v]+')

"""Pattern that matches all types of newlines"""
newline_pattern = re.compile(r'\r\n|\n|\r')

"""Pattern that matches whitespace or the empty string"""
empty_pattern = re.compile(r'\s*')

# Symbols, words, names, identifiers, etc.

"""Pattern that matches words made of letters, digits, underscores"""
word_pattern = re.compile(r'\w+')

"""Pattern that matches names (words that start with a letter)"""
name_pattern = re.compile(r'[a-zA-Z_]\w*')

# Punctuation

"""Pattern that matches punctuation"""
punctuation_word_pattern = re.compile('[-()\'".,:;=+*/`~!@#$%^&?_\\\\|[\\]{}<>]+')

# Strings

"""Template for strings without embedded quotes"""
string_simple_pattern_template = r'{0}[^{0}]*{0}'

"""Template for strings that embed quotes by escaping"""
string_escaped_pattern_template = r'{0}(?:[^{0}{1}]+|{1}.)*{0}'

"""Template for strings that embed quotes by doubling"""
string_doubled_pattern_template = r'{0}(?:[^{0}]+|{0}{0})*{0}'

"""Pattern that matches simple strings quoted with `'`"""
string_simple_single_quoted_pattern = re.compile(
    string_simple_pattern_template.format(re.escape("'")))

"""Pattern that matches simple strings quoted with `"`"""
string_simple_double_quoted_pattern = re.compile(
    string_simple_pattern_template.format(re.escape('"')))

"""Pattern that matches strings quoted with `'` and escaped with `\\`"""
string_escaped_single_quoted_pattern = re.compile(
    string_escaped_pattern_template.format(
        re.escape("'"), re.escape('\\')))

"""Pattern that matches strings quoted with `"` and escaped with `\\`"""
string_escaped_double_quoted_pattern = re.compile(
    string_escaped_pattern_template.format(
        re.escape('"'), re.escape('\\')))

"""Pattern that matches strings quoted with `'''` and escaped with `\\`"""
string_escaped_triple_single_quoted_pattern = re.compile(
    string_escaped_pattern_template.format(
        re.escape("'''"), re.escape('\\')))

"""Pattern that matches strings quoted with `\"\"\"` and escaped with `\\`"""
string_escaped_triple_double_quoted_pattern = re.compile(
    string_escaped_pattern_template.format(
        re.escape('"""'), re.escape('\\')))

"""Pattern that matches strings quoted with `'` and doubled embedding"""
string_doubled_single_quoted_pattern = re.compile(
    string_doubled_pattern_template.format(re.escape("'")))

"""Pattern that matches strings quoted with `"` and doubled embedding"""
string_doubled_double_quoted_pattern = re.compile(
    string_doubled_pattern_template.format(re.escape('"')))

# Comments

"""Template for single-line comment patterns"""
comment_single_line_pattern_template = r'{}[^\n]*'

"""Template for multi-line comment patterns"""
comment_multi_line_pattern_template = r'{}.*?{}'

"""Scripting-style (Bash, Python, Julia, etc.) single-line comment"""
comment_hash_single_pattern = re.compile(
    comment_single_line_pattern_template.format(re.escape('#')))


# Patterns for literal values


# Numbers

"""Pattern that matches integers"""
integer_pattern = re.compile(r'[+-]?\d+')

# The following float regex is optimized to avoid backtracking by
# repeating the exponent regex
_exponent_regex = r'[eE][+-]?\d+'
_float_regex = (
    r'[+-]?(?:' # Initial sign
    r'\d+(?:\.\d*(?:{0})?|{0})' # 1. 1.0 1.0e0 1e0
    r'|\.\d+(?:{0})?)' # .1 .1e1
    .format(_exponent_regex))

"""Pattern that matches floats"""
float_pattern = re.compile(_float_regex)

# Dates and times

"""Pattern that matches various timestamps"""
timestamp_pattern = re.compile(
    r'(?P<year>\d{4})(?P<d_sep>\D?)(?P<month>\d{2})(?P=d_sep)(?P<day>\d{2})'
    r'(?P<ts_sep>.)'
    r'(?P<hour>\d{2})(?P<t_sep>\D?)(?P<minute>\d{2})(?P=t_sep)(?P<second>\d{2})'
    r'(?:[.,](?P<fractional_second>\d+))?(?P<tz>[+-]\d{4})?'
    )

# Constants

"""Pattern that matches True (and yes)"""
bool_true_pattern = re.compile(r'(?:true|yes)', re.IGNORECASE)

"""Pattern that matches False (and no)"""
bool_false_pattern = re.compile(r'(?:false|no)', re.IGNORECASE)

"""Pattern that matches None (and null, nil, and NA)"""
none_pattern = re.compile(r'n(?:a|one|ull|il)', re.IGNORECASE)


# Lexical analysis


class TokenType(enum.Enum): # ENH convert to dynamic hierarchy of types
    """Types of tokens"""
    none = 0 # None or unknown, the null type
    # Words
    symbol = 10
    word = 10
    name = 10
    identifier = 10
    keyword = 11
    quoted_word = 12
    # Whitespace
    space = 20
    newline = 21
    # Punctuation
    punctuation = 30
    begin_group = 31
    end_group = 32
    delimiter = 33
    operator = 34
    # Numbers
    integer = 40
    long = 41
    unsigned = 42
    binary = 43
    octal = 44
    hexadecimal = 45
    float = 46
    double = 47
    # Strings
    string = 50
    single_quoted = 51
    double_quoted = 52
    multichar_quoted = 53
    triple_single_quoted = 54
    triple_double_quoted = 55
    # Comments
    comment = 60
    single_line = 61
    multi_line = 62


class Token:

    def __init__(self, type_, position, length, line=None, column=None):
        self._type = type_
        self._position = position
        self._length = length
        self._line = line
        self._column = column

    @property
    def type(self):
        return self._type

    @property
    def position(self):
        return self._position

    @property
    def length(self):
        return self._length

    @property
    def end(self):
        return self._position + self._length

    @property
    def line(self):
        return self._line

    @property
    def column(self):
        return self._column

    def __len__(self):
        return self._length

    def __repr__(self):
        return (
            'Token(type={!r}, position={!r}, length={!r}, line={!r},'
            ' column={!r})'
            .format(self._type, self._position, self._length,
                    self._line, self._column))

    def content(self, text):
        return text[self.position:self.end]


class Lexer:

    def __init__(self, regex_token_type_pairs):
        self._regex_token_pairs = tuple(regex_token_type_pairs)

    @staticmethod
    def _update_line_column_numbers(text, text_idx, end_idx, line_num, col_num):
        # Count the number of newlines in the given text slice
        newline_match = newline_pattern.search(
            text, pos=text_idx, endpos=end_idx)
        while newline_match is not None:
            line_num += 1
            col_num = 1
            text_idx = newline_match.end()
            newline_match = newline_pattern.search(
                text, pos=text_idx, endpos=end_idx)
        # Update the column number relative to the last newline
        col_num += end_idx - text_idx
        # Return the updated locations
        return line_num, col_num

    def lex(self, text):
        text_idx = 0
        line_num = 1
        col_num = 1
        unk_idx = None
        while text_idx < len(text):
            # Maintain as an indicator if anything matched
            match = None
            for regex, token_type in self._regex_token_pairs:
                match = regex.match(text, pos=text_idx)
                if match is not None:
                    # Match end index
                    end_idx = match.end()
                    # Yield any unmatched (unknown) text
                    if unk_idx is not None:
                        yield Token(
                            TokenType.none,
                            unk_idx,
                            text_idx - unk_idx,
                            line_num,
                            col_num,
                            )
                        # Update line and column numbers
                        line_num, col_num = (
                            self._update_line_column_numbers(
                                text, unk_idx, text_idx,
                                line_num, col_num))
                        # Clear unknown token
                        unk_idx = None
                    # Return this token
                    yield Token(
                        token_type,
                        text_idx,
                        end_idx - text_idx,
                        line_num,
                        col_num,
                        )
                    # Update line and column numbers
                    line_num, col_num = (
                        self._update_line_column_numbers(
                            text, text_idx, end_idx, line_num, col_num))
                    # Update position
                    text_idx = end_idx
                    # Continue while loop (no loop labels, so use the
                    # match as an indicator)
                    break
            # Continue while loop if match
            if match is not None:
                continue
            # No match.  Try again starting at the next character.
            if unk_idx is None:
                unk_idx = text_idx
            text_idx += 1
        # Yield any remaining unmatched text
        if unk_idx is not None:
            yield Token(
                TokenType.none,
                unk_idx,
                text_idx - unk_idx,
                line_num,
                col_num,
                )


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
    return integer_pattern.fullmatch(text.strip()) is not None


def int(text, default=None):
    """Return an integer parsed from the given text, else `default`."""
    return builtins.int(text) if is_int(text) else default


def is_float(text):
    """Whether the given text can be parsed as a float."""
    return float_pattern.fullmatch(text.strip()) is not None


def float(text, default=None):
    """Return a float parsed from the given text, else `default`."""
    return builtins.float(text) if is_float(text) else default


def is_bool(text):
    """Whether the given text can be parsed as a boolean."""
    text = text.strip()
    return (bool_true_pattern.fullmatch(text) is not None
            or bool_false_pattern.fullmatch(text) is not None)


def bool(text, default=None):
    """Return a boolean parsed from the given text, else `default`."""
    text = text.strip()
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

    # Empty is None
    if not text:
        return None, True
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


def timestamp(text, default=None):
    match = timestamp_pattern.fullmatch(text.strip())
    if match is None:
        return default
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
