"""
Parse atomic and compound literals using functions and algorithms
for parsing and lexical analysis.

The parsing functions do not throw exceptions to indicate their
inability to parse a given text.  This is for flexibility and
efficiency.  (You can always raise the error yourself, if you please.)
Instead, many of the parsing functions handle errors using Go style.
For more information about programming with errors in Go style, see the
[introduction to error handling](
https://blog.golang.org/error-handling-and-go) on the Go Blog, the
[section on exceptions]( https://golang.org/doc/faq#exceptions) in the
FAQ, and the [manual]( https://golang.org/doc/effective_go.html#errors).
Functions that do not use Go style return a sentinel value.

Requires Python >= 3.4 for `re.fullmatch`.
"""
# To get an outline run: $ grep -i -e ' *##\+ ' barnapy/parse.py

# Copyright (c) 2015-2020, 2023-2024 Aubrey Barnard.
#
# This is free software released under the MIT license.  See LICENSE for
# details.


from collections.abc import Callable, Iterable
import ast
import builtins
import enum
import datetime as pydt
import re
import typing


##### Types #####


T = typing.TypeVar('T')
ValueErrorParser = Callable[[str], tuple[T | None, Exception | None]]


##### Parsing Errors #####


class ParseError(Exception):

    def __init__(
            self,
            message,
            bad_text,
            source=None,
            line=None,
            column=None,
            **kwds,
    ):
        super().__init__(message, bad_text, source, line, column, kwds)
        self.message = message
        self.bad_text = bad_text
        self.source = source
        self.line = line
        self.column = column

    def __str__(self):
        location = ''
        if self.source is not None:
            location += '{}: '.format(self.source)
        if self.line is not None:
            location += 'line {}: '.format(self.line)
        if self.column is not None:
            location += 'col {}: '.format(self.column)
        return '{}{}: {!r}'.format(location, self.message, self.bad_text)


class SequenceParseError(ParseError):

    def __init__(self, message, bad_text, index=None, **kwds):
        super().__init__(message, bad_text, index=index, **kwds)
        self.index = index

    def __str__(self):
        # Make sure to call '__str__' in order to "dereference" the
        # 'super'.  ('str(super())' doesn't work.)
        msg = super().__str__()
        if self.index is not None:
            msg = f'index {self.index}: {msg}'
        return msg

    @staticmethod
    def from_parse_error(error: ParseError, index: int):
        return SequenceParseError(
            error.message,
            error.bad_text,
            index,
            **{n: getattr(error, n) for n in ('source', 'line', 'column')}
        )


##### Useful Patterns / Regular Expressions for Parsing & Lexical Analysis #####


 #### Patterns for Atomic Literals (Atoms) ####


  ### Numbers ###


# TODO handle integers in various bases
# TODO allow underscores in numbers

"""Pattern that matches integers"""
integer_pattern = re.compile(r'[+-]?\d+')

"""Pattern that matches fractions (rationals)"""
fraction_pattern = re.compile(r'[-+]?\d+/\d+')

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

"""
Pattern that matches infinities or NaNs.

This is separate from `float_pattern` so that numbers and special values
can be distinguished.
"""
inf_nan_pattern = re.compile(
    r'[+-]?(?:inf(?:inity)?|nan)', re.IGNORECASE) # TODO support Yaml syntax, e.g. "-.nan"


  ### Constants ###


"""Pattern that matches True"""
bool_true_pattern = re.compile(r'true', re.IGNORECASE)

"""Pattern that matches common synonyms for True (yes, on)"""
bool_word_true_pattern = re.compile(r'(?:yes|on)', re.IGNORECASE)

"""Pattern that matches False"""
bool_false_pattern = re.compile(r'false', re.IGNORECASE)

"""Pattern that matches common synonyms for False (no, off)"""
bool_word_false_pattern = re.compile(r'(?:no|off)', re.IGNORECASE)

"""Pattern that matches None"""
none_pattern = re.compile(r'none', re.IGNORECASE)

"""Pattern that matches common synonyms for None (null, nil, na)"""
none_word_pattern = re.compile(r'n(?:a|ull|il)', re.IGNORECASE)


 #### Patterns for Compound Literals ####


  ### Ranges of Numbers ###


"""Pattern that matches integer range."""
integer_range_pattern = re.compile(
    '({0})?:({0})?'.format(integer_pattern.pattern))

"""Pattern that matches float range."""
float_range_pattern = re.compile('({0})?:({0})?'.format(float_pattern.pattern))


  ### Dates & Times ###


"""Pattern that matches dates in year-month-day order."""
date_ymd_pattern = re.compile(
    r'(?P<sign>[-+])?(?P<year>\d+)(?P<sep>[^:\d])(?P<month>\d{1,2})'
    r'(?P=sep)(?P<day>\d{1,2})'
)

"""
Pattern that matches times, including with fractional seconds and
optional time zone.
"""
time_pattern = re.compile(
    r'(?P<hour>\d{1,2})(?P<t_sep>[:h])(?P<minute>\d{2})'
    r'(?:[:m](?P<second>\d{2})(?:[.,](?P<fractional_second>\d+))?)?'
    r'\s*(?:am|pm|a\.m\.|p\.m\.)?'
    r'\s*(?P<tz>[+-]\d{4})?',
    re.IGNORECASE,
)

"""
Pattern that matches ISO and similar timestamps that have a date,
time, and optional timezone.
"""
datetime_pattern = re.compile(
    date_ymd_pattern.pattern +
    r'(?P<ts_sep>.)' +
    time_pattern.pattern
)

# TODO? strict pattern for ISO timestamps (i.e., rename below)
# TODO @deprecated
"""Pattern that matches various timestamps"""
timestamp_pattern = re.compile(
    r'(?P<year>\d{4})(?P<d_sep>\D?)(?P<month>\d{2})(?P=d_sep)(?P<day>\d{2})'
    r'(?P<ts_sep>.)'
    r'(?P<hour>\d{2})(?P<t_sep>\D?)(?P<minute>\d{2})(?P=t_sep)(?P<second>\d{2})'
    r'(?:[.,](?P<fractional_second>\d+))?(?P<tz>[+-]\d{4})?'
    )

"""
Pattern that matches amounts of time (only if match group 'delta'
isn't empty, though, so you have to check that yourself).
"""
timedelta_pattern = re.compile(
    r'(?P<sign>[-+])?(?P<delta>'
    r'(?P<years>\d+(?:[.,]\d+)?\s*y(?:(?:ea)?rs?)?\s*)?'
    r'(?P<weeks>\d+(?:[.,]\d+)?\s*w(?:(?:ee)?ks?)?\s*)?'
    r'(?P<days>\d+(?:[.,]\d+)?\s*d(?:a?ys?)?\s*)?'
    r'(?P<hours>\d+(?:[.,]\d+)?\s*h(?:(?:ou)?rs?)?\s*)?'
    r'(?P<mins>\d+(?:[.,]\d+)?\s*m(?:in(?:ute)?s?)?\s*)?'
    r'(?P<secs>\d+(?:[.,]\d+)?\s*s(?:ec(?:ond)?s?)?\s*)?'
    r')',
    re.IGNORECASE,
)


  ### Splitting and Lists ###


def mk_split_pattern(
        separator: str, allow_surrounding_whitespace: bool=True,
) -> re.Pattern:
    pat = re.escape(separator)
    if allow_surrounding_whitespace:
        pat = rf'\s*{pat}\s*'
    return re.compile(pat)


"""Pattern for splitting on commas."""
comma_split_pattern = re.compile(',')

"""Pattern for splitting on colons."""
colon_split_pattern = re.compile(':')

"""Pattern for splitting lists without nesting or quoting"""
naive_list_split_pattern = re.compile(r'\s*,\s*')


 #### Patterns for Syntax / Lexical Analysis ####


  ### Whitespace ###


"""Pattern that matches all whitespace"""
space_pattern = re.compile(r'\s+')

"""Pattern that matches plain (non-newline) whitespace"""
space_plain_pattern = re.compile(r'[ \t\f\v]+')

"""Pattern that matches all types of newlines"""
newline_pattern = re.compile(r'\r\n|\n|\r')

"""Pattern that matches whitespace or the empty string"""
empty_pattern = re.compile(r'\s*')


  ### Symbols, Words, Names, Identifiers, Etc. ###


"""Pattern that matches words made of letters, digits, underscores"""
word_pattern = re.compile(r'\w+')

"""
Pattern that matches names, keywords, or identifiers (words that
start with a letter or underscore)
"""
name_pattern = re.compile(r'[a-zA-Z_]\w*')


  ### Punctuation ###


"""Pattern that matches punctuation"""
punctuation_word_pattern = re.compile(
    '[-()\'".,:;=+*/`~!@#$%^&?_\\\\|[\\]{}<>]+')


  ### Strings & Quotes ###


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


  ### Comments ###


"""Template for single-line comment patterns"""
comment_single_line_pattern_template = r'{}[^\n]*'

"""Template for multi-line comment patterns"""
comment_multi_line_pattern_template = r'{}.*?{}'

"""Scripting-style (Bash, Python, Julia, etc.) single-line comment"""
comment_hash_single_pattern = re.compile(
    comment_single_line_pattern_template.format(re.escape('#')))


##### Functions for Parsing #####


 #### Detecting & Parsing Atomic Literals (Atoms) ####


  ### Numbers ###


def is_int(text: str) -> builtins.bool:
    """Whether the given text repesents an integer."""
    return integer_pattern.fullmatch(text.strip()) is not None

def int(text: str, default: object=None) -> builtins.int | object:
    """Return an integer parsed from the given text, else `default`."""
    return builtins.int(text) if is_int(text) else default

def int_err(text: str) -> tuple[builtins.int, ParseError]:
    """
    Parse an integer from the given text.

    Return a (value, error) pair per Go style.
    """
    if is_int(text):
        return (builtins.int(text), None)
    else:
        return (None, ParseError('Cannot parse an integer from', text))


def is_float(text: str, allow_inf_nan: builtins.bool=True) -> builtins.bool:
    """Whether the given text represents a float."""
    txt = text.strip()
    return (float_pattern.fullmatch(txt) is not None or
            (allow_inf_nan and
             inf_nan_pattern.fullmatch(txt) is not None))

def float(
        text: str, default: object=None, allow_inf_nan: builtins.bool=True,
) -> builtins.float | object:
    """Return a float parsed from the given text, else `default`."""
    txt = text.strip()
    return (builtins.float(txt)
            if is_float(txt, allow_inf_nan) or is_int(txt)
            else default)

def float_err(
        text: str, allow_inf_nan: builtins.bool=True,
) -> tuple[builtins.float, ParseError]:
    """
    Parse a float from the given text.

    Return a (value, error) pair per Go style.
    """
    txt = text.strip()
    if is_float(txt, allow_inf_nan) or is_int(txt):
        return (builtins.float(txt), None)
    else:
        return (None, ParseError('Cannot parse a float from', text))


  ### Constants / Nothings ###


def is_bool(text: str) -> builtins.bool:
    """Whether the given text represents a boolean."""
    txt = text.strip()
    return (bool_true_pattern.fullmatch(txt) is not None
            or bool_false_pattern.fullmatch(txt) is not None)

def bool(text: str, default: object=None) -> builtins.bool | object:
    """Return a boolean parsed from the given text, else `default`."""
    txt = text.strip()
    if bool_true_pattern.fullmatch(txt) is not None:
        return True
    elif bool_false_pattern.fullmatch(txt) is not None:
        return False
    else:
        return default

def bool_err(text: str) -> tuple[builtins.bool, ParseError]:
    """
    Parse a boolean from the given text.

    Return a (value, error) pair per Go style.
    """
    txt = text.strip()
    if bool_true_pattern.fullmatch(txt) is not None:
        return (True, None)
    elif bool_false_pattern.fullmatch(txt) is not None:
        return (False, None)
    else:
        return (None, ParseError('Cannot parse a boolean from', text))

def is_bool_word(text: str) -> builtins.bool:
    """
    Whether the given text is a boolean synonym word (no, yes, off,
    on).
    """
    txt = text.strip()
    return (bool_word_true_pattern.fullmatch(txt) is not None
            or bool_word_false_pattern.fullmatch(txt) is not None)

def bool_word(text: str, default: object=None) -> builtins.bool | object:
    """
    Return a boolean synonym word parsed from the given text, else
    `default`.
    """
    txt = text.strip()
    if bool_word_true_pattern.fullmatch(txt) is not None:
        return True
    elif bool_word_false_pattern.fullmatch(txt) is not None:
        return False
    else:
        return default

def bool_word_err(text: str) -> tuple[builtins.bool, ParseError]:
    """
    Parse a boolean synonym word from the given text.

    Return a (value, error) pair per Go style.
    """
    txt = text.strip()
    if bool_word_true_pattern.fullmatch(txt) is not None:
        return (True, None)
    elif bool_word_false_pattern.fullmatch(txt) is not None:
        return (False, None)
    else:
        return (None, ParseError(
            'Cannot parse a boolean synonym word from', text))


# The following atomic literals may only have functions for detection
# because there is no obvious value to construct or return.  In
# particular, it makes no sense to return None as a sentinel value from
# a function that would also return None on success.  Other sentinel
# values are possible but likely very application-specific.


def is_none(text: str) -> builtins.bool:
    """Whether the given text is None."""
    return none_pattern.fullmatch(text.strip()) is not None

def none_err(text: str) -> tuple[None, ParseError]:
    """Parse `None` from the given text or fail with an error."""
    if is_none(text):
        return (None, None)
    else:
        return (None, ParseError('Cannot parse `None` from', text))

def is_none_word(text: str) -> builtins.bool:
    """Whether the given text is a synonym word for None (null, nil, na)."""
    return none_word_pattern.fullmatch(text.strip()) is not None

def none_word_err(text: str) -> tuple[None, ParseError]:
    """
    Parse `None` from the given 'none' synonym text or fail with an
    error.
    """
    if is_none_word(text):
        return (None, None)
    else:
        return (None, ParseError(
            'Cannot parse a `None` synonym word from', text))


def is_empty(text: str) -> builtins.bool:
    """Whether the given text is empty or only whitespace characters."""
    return empty_pattern.fullmatch(text) is not None

def empty_err(text: str, value: object=None) -> tuple[object, ParseError]:
    """Return the given value if the given text is empty / whitespace."""
    if is_empty(text):
        return (value, None)
    else:
        return (None, ParseError('Not empty or whitespace', text))


  ### Symbols / Names / Identifiers ###


def is_name(text: str) -> builtins.bool:
    """
    Whether the given text is a name, keyword, or identifier.
    """
    return name_pattern.fullmatch(text.strip()) is not None

def name(text: str, default: object=None) -> str | object:
    """Return a name parsed from the given text, else `default`."""
    txt = text.strip()
    return txt if is_name(txt) else default

def name_err(text: str) -> tuple[str, ParseError]:
    """
    Parse a name from the given text.

    Return a (value, error) pair per Go style.
    """
    txt = text.strip()
    if is_name(txt):
        return (txt, None)
    else:
        return (None, ParseError('Cannot parse a name from', text))


  ### Any Atom ###


def is_atom(text: str, allow_inf_nan: builtins.bool=True) -> builtins.bool:
    """
    Whether the given text represents an atomic literal (int, float,
    bool, None, name).
    """
    txt = text.strip()
    return (is_int(txt) or
            is_float(txt, allow_inf_nan) or
            is_bool(txt) or
            is_none(txt) or
            is_name(txt))

def atom_err(
        text: str, default: object=None, allow_inf_nan: builtins.bool=True,
) -> tuple[object, ParseError]:
    """
    Parse an atomic literal (int, float, bool, None, name) from the
    given text.

    Return a (value, error) pair per Go style.  If parsing is successful,
    then (<value>, None) is returned, otherwise (<default>, ParseError) is
    returned.  This is needed for distinguishable parsing of None.

    This recognizes and parses all the atoms that are distinguishable by
    their appearance alone.
    """
    # Try parsing the literal in order of (assumed) frequency of types
    txt = text.strip()
    # Integer
    if integer_pattern.fullmatch(txt) is not None:
        return (builtins.int(txt), None)
    # Float
    elif (float_pattern.fullmatch(txt) is not None or
          (allow_inf_nan and
           inf_nan_pattern.fullmatch(txt) is not None)):
        return (builtins.float(txt), None)
    # Boolean
    elif bool_true_pattern.fullmatch(txt) is not None:
        return (True, None)
    elif bool_false_pattern.fullmatch(txt) is not None:
        return (False, None)
    # None
    elif none_pattern.fullmatch(txt) is not None:
        return (None, None)
    # Name / Keyword / Identifier.  This must come after the other atoms
    # whose representations are words.
    elif name_pattern.fullmatch(txt) is not None:
        return (txt, None)
    # Whitespace, strings, or non-atoms
    else:
        return (default, ParseError('Cannot parse an atom from', text))


 #### Detecting & Parsing Compound Literals ####


  ### Any Python Literal ###


def pyliteral_err(text: str, default: object=None) -> tuple[object, ParseError]:
    """
    Parse a Python literal (anything recognized by `ast.literal_eval`)
    from the given text.
    """
    try:
        return (ast.literal_eval(text), None)
    except (SyntaxError, ValueError) as err:
        return (default, err)


  ### Dates & Times ###


def is_date(
        text: str, date_pattern: re.Pattern=date_ymd_pattern,
) -> builtins.bool:
    """Whether the given text represents a date."""
    return date_pattern.fullmatch(text.strip()) is not None

def date_err(text: str, date_pattern: re.Pattern=date_ymd_pattern) -> tuple[
        pydt.date, ParseError]:
    """
    Parse a date from the given text using the given pattern.

    Return a (value, error) pair per Go style.

    The pattern must have the named match groups {year, month, day},
    which are integers.
    """
    txt = text.strip()
    mtch = date_pattern.fullmatch(txt)
    if mtch is None:
        return (None, ParseError('Could not parse a date from', text))
    # Parse the date components from the match
    grp_nm2txt = mtch.groupdict()
    components = []
    for comp_name in ('year', 'month', 'day'):
        (val, err) = int_err(grp_nm2txt[comp_name])
        if err is not None:
            return (None, ParseError(
                f'Could not parse a {comp_name} number from',
                grp_nm2txt[comp_name]))
        components.append(val)
    (year, month, day) = components
    # Handle an optional sign (even though Python's date class doesn't
    # allow BCE (negative) years despite it saying dates are
    # "indefinitely extended in both directions")
    if 'sign' in grp_nm2txt:
        sign = grp_nm2txt['sign']
        if sign in (None, '+'):
            pass
        elif sign == '-':
            year = -year
        else:
            return (None, ParseError('Not the sign of a number', sign))
    # Let the date constructor handle normalization / validation from
    # here
    try:
        return (pydt.date(year, month, day), None)
    except ValueError as err:
        return (None, err)

def date(
        text: str, default=None, date_pattern: re.Pattern=date_ymd_pattern,
) -> pydt.date:
    (date, err) = date_err(text, date_pattern)
    return date if err is None else default


def is_time(text: str) -> builtins.bool:
    """Whether the given text represents a time."""
    return time_pattern.fullmatch(text.strip()) is not None

def time(): # TODO
    return NotImplemented

def time_err(): # TODO
    return NotImplemented


def is_datetime(text: str) -> builtins.bool:
    """Whether the given text represents a datetime (timestamp)."""
    return datetime_pattern.fullmatch(text.strip()) is not None

def datetime(): # TODO
    return NotImplemented

def datetime_err(): # TODO
    return NotImplemented


def timestamp(text: str, default: object=None) -> pydt.datetime:
    match = timestamp_pattern.fullmatch(text.strip())
    if match is None:
        return default
    int = builtins.int
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
        delta = pydt.timedelta(
            hours=int(tz_str[1:3]), minutes=int(tz_str[3:]))
        if tz_str[0] == '-':
            tz = pydt.timezone(-delta)
        else:
            tz = pydt.timezone(delta)
    # Parse the fields and return as a datetime
    return pydt.datetime(
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


def is_timedelta(text: str) -> builtins.bool:
    """Whether the given text represents a time delta."""
    match = timedelta_pattern.fullmatch(text.strip())
    return match is not None and len(match.group('delta')) > 0

def timedelta(): # TODO
    return NotImplemented

def timedelta_err(): # TODO
    return NotImplemented


  ### CLI-Style (Naively-Structured) Literals Including Lists and Dicts ###


def cli_atom_err(
        text: str, default: object=None, allow_inf_nan: builtins.bool=True,
) -> tuple[object, ParseError]:
    """
    Parse an atomic CLI literal (int, float, bool) from the given
    text.

    Return a (value, error) pair per Go style.  If parsing is
    successful, then (<value>, None) is returned, otherwise (<default>,
    ParseError) is returned.

    This parses all the atoms that have unambiguous string
    representations and whose construction is invertible.  These are
    also the relatively language-agnostic atoms.
    """
    txt = text.strip()
    # Integer
    if integer_pattern.fullmatch(txt) is not None:
        return (builtins.int(txt), None)
    # Float
    elif (float_pattern.fullmatch(txt) is not None or
          (allow_inf_nan and
           inf_nan_pattern.fullmatch(txt) is not None)):
        return (builtins.float(txt), None)
    # Boolean
    elif bool_true_pattern.fullmatch(txt) is not None:
        return (True, None)
    elif bool_false_pattern.fullmatch(txt) is not None:
        return (False, None)
    else:
        return (default, ParseError('Cannot parse a CLI atom from', text))


def cli_list_err(
        text: str,
        parse_item: ValueErrorParser=None,
        split_pattern: re.Pattern=comma_split_pattern,
        strip: bool=True,
) -> tuple[list, Exception]:
    items = []
    if len(text) == 0:
        return (items, None)
    pieces = split_pattern.split(text)
    for (idx, piece) in enumerate(pieces):
        if strip:
            piece = piece.strip()
        if parse_item is not None:
            (val, err) = parse_item(piece)
            if err is not None:
                return (items, SequenceParseError.from_parse_error(err, idx))
        else:
            val = piece
        items.append(val)
    return (items, None)


def cli_kv_pair_err(
        text: str,
        parse_key: ValueErrorParser=None,
        parse_val: ValueErrorParser=None,
        split_pattern: re.Pattern=colon_split_pattern,
        strip: bool=True,
) -> tuple[tuple[object, object], Exception]:
    pieces = split_pattern.split(text, maxsplit=1)
    if len(pieces) != 2:
        return (None, ParseError(
            'Unable to split into a key and a value', text))
    (key_piece, val_piece) = pieces
    if strip:
        key_piece = key_piece.strip()
        val_piece = val_piece.strip()
    if parse_key is not None:
        (key, err) = parse_key(key_piece)
        if err is not None:
            return (None, err)
    else:
        key = key_piece
    if parse_val is not None:
        (val, err) = parse_val(val_piece)
        if err is not None:
            return (None, err)
    else:
        val = val_piece
    return ((key, val), None)


def cli_dict_err(
        text: str,
        parse_key: ValueErrorParser=None,
        parse_val: ValueErrorParser=None,
        item_split_pattern: re.Pattern=comma_split_pattern,
        kv_split_pattern: re.Pattern=colon_split_pattern,
        strip: bool=True,
) -> tuple[dict, Exception]:
    def parse_item(text: str) -> tuple[tuple[object, object], Exception]:
        return cli_kv_pair_err(
            text, parse_key, parse_val, kv_split_pattern, strip)
    (kv_pairs, err) = cli_list_err(text, parse_item, item_split_pattern, strip)
    return (dict(kv_pairs) if kv_pairs is not None else None, err)


 #### Detecting & Parsing Expressions ####


  ### Array Indexing ###


_array_index_pattern = re.compile(r'\s*(\w+)\s*\[\s*(\d+)\s*\]\s*')

def array_index(text: str, default: object=None) -> tuple[str, str] | object:
    """
    Parse the text as array indexing syntax (e.g. "a[0]") and return a
    (name, index) pair.
    """
    match = _array_index_pattern.match(text)
    if match is not None:
        return match.groups()
    else:
        return default

def array_index_err(text: str) -> tuple[tuple[str, str], ParseError]:
    """
    Parse an array index reference from the given text.

    Return a (value, error) pair per Go style.
    """
    result = array_index(text)
    if result is None:
        return (None, ParseError(
            'Cannot parse an array index from', text))
    else:
        return (result, None)


  ### Datalog Predicates ###


_predicate_pattern = re.compile(
    r'\s*(\w[\w!?@$_-]*)(?:\s*\((.*)\))?\s*')

def predicate(text: str, default: object=None) -> tuple[str, list] | object:
    match = _predicate_pattern.match(text)
    if match:
        (name, args_text) = match.groups()
        if (args_text is None
                or len(args_text) == 0
                or args_text.isspace()):
            args = ()
        else:
            args = naive_list_split_pattern.split(args_text.strip())
        return (name, args)
    else:
        return default

def predicate_err(text: str) -> tuple[tuple[str, list], ParseError]:
    """
    Parse a predicate from the given text.

    Return a (value, error) pair per Go style.
    """
    result = predicate(text)
    if result is None:
        return (None, ParseError('Cannot parse a predicate from', text))
    else:
        return (result, None)


 #### Generalized Parsing: Matcher–Constructors ####


# TODO @deprecated  # TODO remove in version XXX
def parse(text, detectors, constructors, default=None):
    """
    Parse the given text and construct a value.

    Return a (value, error) pair per Go style.  The pair is (<value>,
    None) on parsing success and (<default>, ParseError) on failure.
    (Go style has been used here since parsing can, in general, return
    any value, and thus parsing success cannot be determined from the
    value alone.)

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
            return constructor(text), None
    # Otherwise return default
    return default, ParseError('Cannot parse', text)


def mk_match(*matchers: Callable[[str], builtins.bool]) -> Callable[
        [str], builtins.int]:
    """
    Make a function for matching text according to the given
    sequence of matchers.

    The returned function, `match(text)`, applies the given matchers
    (functions for matching text) in order to the provided text and
    returns the index of the first matcher that matches or `None` if
    none of them matches.
    """
    def match(text: str) -> builtins.int:
        for (idx, matcher) in enumerate(matchers):
            if matcher(text):
                return idx
        return None
    return match


def mk_match_and_construct(
        *matchers_constructors: tuple[
            Callable[[str], builtins.bool],
            Callable[[str], tuple[object, ParseError]],
        ],
) -> Callable[[str, object], tuple[builtins.int, object, ParseError]]:
    """
    Make a function for matching text and constructing a value from
    that text according to the given sequence of matchers and
    constructors.

    The returned function, `match_and_construct(text, default=None)`,
    applies the given matchers (functions for matching text) in order to
    the provided text and returns the index of the first matcher that
    matches along with the result of applying the corresponding
    constructor, where each constructor returns a (value, error) pair
    per Go style.  These results are returned as the triple (index,
    constructed value, error).  If there is no match, then `(None,
    default, None)` is returned.
    """
    def match_and_construct(text: str, default: object=None) -> tuple[
            builtins.int, object, ParseError]:
        for (idx, (matcher, constructor)) in enumerate(matchers_constructors):
            if matcher(text):
                (val, err) = constructor(text)
                return (idx, val, err)
        return (None, default, None)
    return match_and_construct


def mk_try_construct(
        *try_constructors: Callable[[str], tuple[object, ParseError]]
) -> Callable[[str, object], tuple[builtins.int, object]]:
    """
    Make a function for trying to construct a value from text
    according to the given sequence of constructors.

    The returned function, `try_construct(text, default=None)`, applies
    the given try–constructors in order to the provided text and returns
    the index of the first constructor that succeeds (doesn't return an
    error) along with the value it constructed, where each
    try–constructor returns a (value, error) pair per Go style.  These
    results are returned as the pair (index, constructed value).  If no
    constructor succeeds, then `(None, default)` is returned.
    """
    def try_construct(text: str, default: object=None) -> tuple[
            builtins.int, object]:
        for (idx, constructor) in enumerate(try_constructors):
            (val, err) = constructor(text)
            if err is None:
                return (idx, val)
        return (None, default)
    return try_construct


def mk_parse_numeric_empty_date_bool_none(
        allow_inf_nan: builtins.bool=True,
        date_pattern: re.Pattern=date_ymd_pattern,
        empty_value: object=None,
) -> Callable[[str, object], tuple[builtins.int, object]]:
    return mk_try_construct(
        int_err,
        lambda text: float_err(text, allow_inf_nan),
        lambda text: empty_err(text, empty_value),
        lambda text: date_err(text, date_pattern),
        bool_err,
        none_err,
    )


##### Classes & Algorithms to Help with Lexical Analysis & Parsing #####


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
