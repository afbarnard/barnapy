"""
Utilities for working with tabular data in various separated values
formats.
"""

# Copyright (c) 2022-2023 Aubrey Barnard.
#
# This is free software released under the MIT License.  See LICENSE for
# details.


from collections.abc import Iterable
from typing import ForwardRef
import csv
import dataclasses
import datetime
import decimal
import io
import re

from . import parse
from . import records


##### CSV Formats #####


def parse_format(chars) -> dict:
    """
    Interpret the given string as a CSV format specification (syntax
    specification or "dialect") for the Python CSV module.

    A CSV format specification is a mapping from format parameter names
    to values [1].  As few or as many characters as desired can be
    given; any format parameter not specified will not be included in
    the format.  This allows default parameter values, such as those
    specified in the Python CSV module, to "show through".  This is
    intended to make CSV formats easy to specify on the command line.

    Character.  Format Parameter.
    1. Delimiter.
    2. Quote character ('quotechar').
    3. Doubling or escaping ('doublequote'): d=doubling, e=escaping.
    4. Escape character ('escapechar').  Space (`' '`) means `None` [2],
       which disables escaping.
    5. Quoting mode ('quoting'): m=minimal, a=all, n=none, o=objects
       (non-numeric values).
    6. Whether to trim (strip) whitespace from values
       ('skipinitialspace'): t=trim, k=keep.
    7. Whether all records need to have the same length ('strict'):
       s=strict, l=loose.
    8. Line terminator (for the writer) ('lineterminator').  String of
       all remaining characters.


    ### Examples ###

    `',"d mkl\\r\\n'`: Python CSV module defaults.

    `'|"e\\\\mks\\n'`: Pipe-delimited, minimally quoted fields as for
        SQLite import on Unix.

    `' "E\\\\MTL\\n\\r'`: Space-aligned, human-readable tables on Acorn BBC.

    `'\\t"D OKS\\r'`: Excel-like TSV on old Mac.


    [1] https://docs.python.org/3/library/csv.html#dialects-and-formatting-parameters

    [2] While NUL (`'\\x00'`) would be a natural candidate for
        representing `None`, there are many problems with having NUL
        bytes in strings due to their prevailing use as string
        terminators.  For example, strings including NUL are not
        interpreted correctly as command line arguments.  Other control
        characters might be possible candidates, but Python encodes some
        control characters as surrogates (e.g., Python represents
        `'\\x80'` as `'\\udc80'`), which is a complication best avoided
        here.  The consequence is that a space cannot be an escape
        character (which seems extremely reasonable).
    """
    format = {}
    if len(chars) >= 1:
        format['delimiter'] = chars[0]
    if len(chars) >= 2:
        format['quotechar'] = chars[1]
    if len(chars) >= 3:
        if chars[2] in ('d', 'D'):
            format['doublequote'] = True
        elif chars[2] in ('e', 'E'):
            format['doublequote'] = False
        else:
            raise ValueError(
                "Unrecognized CSV format parameter: doubling or escaping: "
                f"'{chars[2]}' (not 'd' or 'e')")
    if len(chars) >= 4:
        if chars[3] == ' ':
            format['escapechar'] = None
        else:
            format['escapechar'] = chars[3]
    if len(chars) >= 5:
        if chars[4] in ('m', 'M'):
            format['quoting'] = csv.QUOTE_MINIMAL
        elif chars[4] in ('a', 'A'):
            format['quoting'] = csv.QUOTE_ALL
        elif chars[4] in ('n', 'N'):
            format['quoting'] = csv.QUOTE_NONE
        elif chars[4] in ('o', 'O'):
            format['quoting'] = csv.QUOTE_NONNUMERIC
        else:
            raise ValueError(
                "Unrecognized CSV format parameter: quoting mode: "
                f"'{chars[4]}' (not 'm', 'a', 'n', or 'o')")
    if len(chars) >= 6:
        if chars[5] in ('k', 'K'):
            format['skipinitialspace'] = False
        elif chars[5] in ('t', 'T'):
            format['skipinitialspace'] = True
        else:
            raise ValueError(
                "Unrecognized CSV format parameter: trim space: "
                f"'{chars[5]}' (not 'k' or 't')")
    if len(chars) >= 7:
        if chars[6] in ('l', 'L'):
            format['strict'] = False
        elif chars[6] in ('s', 'S'):
            format['strict'] = True
        else:
            raise ValueError(
                "Unrecognized CSV format parameter: strict length: "
                f"'{chars[6]}' (not 'l' or 's')")
    if len(chars) >= 8:
        format['lineterminator'] = chars[7:]
    return format

parse_csv_dialect = parse_format # TODO deprecate


"""Default C-style CSV on Unix"""
_default_format = dict(
    delimiter=',',
    doublequote=False,
    escapechar='\\',
    lineterminator='\n',
    quotechar='"',
    quoting=csv.QUOTE_MINIMAL,
)

# TODO put hierarchy here


##### Format and Header Detection #####

 #### Format Detection ####


def detect_format(delimited_text: str) -> dict:
    """
    Try to detect the format parameters of the given (sample of)
    delimited text.  Return a dictionary of only those CSV module format
    parameters that were actually detected.

    This is a replacement for `csv.Sniffer` that avoids returning
    default parameters when they weren't explicitly detected.
    """
    # Based on 'fitamord.delimited.Format.detect'.
    # Detect delimiter and quoting using the Sniffer internals to avoid
    # defaulting of quote character.  (This follows
    # 'csv.Sniffer.sniff'.)
    sniffer = csv.Sniffer()
    (quote_char, doubling, delimiter, skip_space) = (
        sniffer._guess_quote_and_delimiter(delimited_text, None))
    if delimiter:
        # Only return what was actually detected
        return dict(
            delimiter=delimiter,
            quotechar=quote_char if quote_char != '' else None,
            doublequote=doubling,
            skipinitialspace=skip_space,
        )
    # That didn't work because no quotes.  Try again.
    (delimiter, skip_space) = sniffer._guess_delimiter(delimited_text, None)
    if delimiter:
        # Only return what was actually detected
        return dict(
            delimiter=delimiter,
            skipinitialspace=skip_space,
        )
    # If that also didn't work, give up and return what was detected
    # (nothing)
    return {}


 #### Header Detection ####

  ### Heuristics ###


_col_decl_pattern = re.compile(
    r'{0}[?!]?(?:\s*:\s*{0}(?:\s*\|\s*{0})*)?'.format(r'[a-zA-Z_]\w*')
)

def header_heuristic__declarations(header: list[str]) -> float:
    """
    Return the fraction of fields that look like declaration.

    A declaration looks like '<name> ":" <type> ("|" <type>)*' (with
    optional whitespace).
    """
    txts = [txt.strip().strip('"\'') for txt in header]
    n_decls = sum(int(_col_decl_pattern.fullmatch(txt) is not None)
                  for txt in txts)
    return n_decls / len(txts)


def _is_structured(text):
    text = text.strip()
    for (beg, end) in ['[]', '()', '{}', '<>']:
        if text[0] == beg and text[-1] == end:
            return True
    return False

_nonstr_value_matcher = parse.mk_match(
    parse.is_int,
    parse.is_float,
    parse.is_bool,
    parse.is_none,
    parse.is_date,
    parse.is_datetime,
    parse.is_time,
    parse.is_timedelta,
    _is_structured,
)

def header_heuristic__non_string_values(header: list[str]) -> float:
    """
    Return the fraction of fields that would not parse as non-string
    values.

    Non-string values are ints, floats, bools, None, dates, times,
    datetimes, timedeltas, and compound literals (lists, tuples, sets,
    dicts).  See '_nonstr_value_matcher'.
    """
    txts = [txt.strip().strip('"\'') for txt in header]
    n_nonstrs = sum(int(_nonstr_value_matcher(txt) is not None) for txt in txts)
    n_cols = len(header)
    return (n_cols - n_nonstrs) / n_cols


def header_heuristic__names_values(first_rows: list[list[str]]) -> float:
    """
    Return the fraction of fields where the first row has a name and
    the second row has a non-string value.

    This heuristic is very similar to the one used by
    'csv.Sniffer.has_header' except it compares only the first two rows.
    See 'header_heuristic__non_string_values' for the non-string values.
    """
    if len(first_rows) < 2:
        raise ValueError('At least 2 rows are needed, not '
                         f'{len(first_rows)} rows')
    txts = [[txt.strip().strip('"\'') for txt in first_rows[row_idx]]
            for row_idx in range(2)]
    name_idxs = set(i for (i, s) in enumerate(txts[0])
                    if parse.name_pattern.match(s) is not None)
    value_idxs = set(i for (i, s) in enumerate(txts[1])
                     if _nonstr_value_matcher(s) is not None)
    # The number of columns where row 1 has a name and row 2 has a
    # non-string value
    n_nm_val_pairs = len(name_idxs & value_idxs)
    return n_nm_val_pairs / len(txts[0])


  ### Scoring ###


def score_header(
        rows: list[list[str]],
        declarations_weight: float=5,
        non_strings_weight: float=3,
        names_values_weight: float=4,
) -> float:
    decls = header_heuristic__declarations(rows[0])
    nstrs = header_heuristic__non_string_values(rows[0])
    nmvls = header_heuristic__names_values(rows)
    total_weight = (
        declarations_weight + non_strings_weight + names_values_weight)
    score = (declarations_weight * decls +
             non_strings_weight * nstrs +
             names_values_weight * nmvls) / total_weight
    return score


def detect_header(
        delimited_text: str,
        csv_format: dict,
        threshold: float=1/2,
) -> tuple[bool, list[str], str]:
    """
    Detect the header of the given (sample of) delimited text.
    Return (has header?, first row (header fields), error).

    The header is the first row of the given delimited text if that row
    contains column descriptions (names, types) rather than data.  The
    detection is based on whether a convex combination of heuristics
    meets the given threshold.  (See 'score_header'.)
    """
    # Read the first line
    if len(delimited_text) == 0:
        return (None, None, 'Empty text')
    file = io.StringIO(delimited_text)
    reader = csv.reader(file, **csv_format)
    rows = list(reader)
    if len(rows) == 0:
        return (None, None, 'CSV reader returned no rows')
    score = score_header(rows)
    return (score >= threshold, rows[0], None)


##### Specifying Headers #####


# Based on the data types supported by Python, Julia, Rust, SQLite,
# Postgres, BigQuery
data_type_name2type = { # TODO probably should be in its own data types module, e.g., for parsing data type parameters like width / precision; TODO? separate by language, e.g., records of the form (name, langs, equivalent Python type, constructor); TODO got to be able to parse union types
    # Integers
    'int': int,
    'int8': int,
    'int16': int,
    'int32': int,
    'int64': int,
    'int128': int,
    'uint': int,
    'uint8': int,
    'uint16': int,
    'uint32': int,
    'uint64': int,
    'uint128': int,

    # Boolean
    'bool': bool,
    'boolean': bool,

    # Floating point numbers
    'float': float,
    'float16': float,
    'float32': float,
    'float64': float,
    'real': float,

    # Arbitrary precision
    'numeric': decimal.Decimal,
    'decimal': decimal.Decimal,
    'bigdecimal': decimal.Decimal,

    # Dates & times
    'date': datetime.date,
    'time': datetime.time,
    'datetime': datetime.datetime,

    # Strings
    'char': str,
    'varchar': str,
    'str': str,
    'string': str,
    'text': str,

    # Binary
    'bytes': bytes,
    'blob': bytes,

    # None / null
    'none': type(None),
    'null': type(None),

    # Any / object / looks like
    'any': object,
    'object': object,
}


# Forward declaration
FieldSpecification = ForwardRef('FieldSpecification')

_range_pattern = re.compile('({0})?-({0})?'.format(
    parse.integer_pattern.pattern))

@dataclasses.dataclass(slots=True, order=True)
class FieldSpecification:
    """
    A description of a field, or contiguous range of fields, in
    terms of its number (or range of numbers), name, and type.  All
    pieces of information are optional and can be omitted.  When a range
    of numbers is specified, the name is interpreted as a base name to
    which a sequence number is appended.  The type is the same for all
    fields in a range.
    """

    number: int | range = None
    name: str = None
    type: records.FieldType = None

    @staticmethod
    def parse(
            field_spec: str,
            name2type: dict[str, type]=data_type_name2type,
            sep: str=':',
            name_signifier: str=None,
    ) -> tuple[FieldSpecification | None, str | None]:
        """
        Parse the given string as a field specification and return
        (field specification, error).  Parsing was sucessful if 'error'
        is `None`.

        A field specification string is a sequence of pieces delimited
        by colons (or 'sep') where the pieces describe the number (or
        range), name, and type of the field.  All pieces are optional
        and they may be given in any order.  All pieces not specified
        are returned as `None`.  Here is a grammar:

        ```
        <field-spec> ::= <piece>? (<sep> <piece>?)*
        <piece> ::= <number> | <name> | <type>
        <number> ::= <integer> | <range>
        <range> ::= <integer> "-" <integer>
        <name> ::= <identifier> | <name-signifier> <char>*
        <type> ::= <identifier> ("|" <identifier>)*
        ```

        name2type: dict[name,type]

            Map of all recognized type names to their corresponding
            types.  A piece will only parse as a type if it is a name in
            this map or if it looks like a type union.

        name_signifier: str | None

            While names of fields and names of types are typically
            disjoint, you can use this to specify a prefix that
            signifies the piece is a name rather than a type.  The
            prefix is removed from the returned name.
        """
        fs = FieldSpecification()
        if len(field_spec) == 0:
            return (fs, None)
        pieces = field_spec.split(sep)
        if len(pieces) > 3:
            return (fs, 'Expected at most 3 field specification pieces, '
                    f'(number, name, type), not {len(pieces)} pieces: {pieces}')
        for (idx, piece) in enumerate(pieces):
            piece = piece.strip()
            if len(piece) == 0:
                continue
            elif parse.is_int(piece):
                if fs.number is not None:
                    return (fs, 'Field specification piece is an integer, '
                            'but the field number was already assigned: '
                            f'Piece {idx + 1} of {field_spec!r}: {piece!r}')
                number = int(piece)
                if number < 1:
                    return (fs, f'Field number negative or zero: {number!r}')
                fs.number = int(piece)
            elif (match := _range_pattern.fullmatch(piece)) is not None:
                if fs.number is not None:
                    return (fs, 'Field specification piece is a range, '
                            'but the field number was already assigned: '
                            f'Piece {idx + 1} of {field_spec!r}: {piece!r}')
                lo = int(match.group(1))
                hi = int(match.group(2))
                if not (1 <= lo <= hi):
                    return (fs, 'Field specification piece is a range, '
                            'but the range is bad (negative, zero, or empty):'
                            f'Piece {idx + 1} of {field_spec!r}: {piece!r}')
                fs.number = range(lo, hi + 1)
            elif piece in name2type or piece.lower() in name2type or (
                    '|' in piece):
                if fs.type is not None:
                    return (fs, 'Field specification piece is a type, '
                            'but the field type was already assigned: '
                            f'Piece {idx + 1} of {field_spec!r}: {piece!r}')
                type_names = [t.strip() for t in piece.split('|')]
                types = [name2type.get(t, name2type.get(t.lower()))
                         for t in type_names]
                if None in types:
                    idx_none = types.index(None)
                    return (fs, 'Unrecognized type name: '
                            f'{type_names[idx_none]!r} in '
                            f'piece {idx + 1} of {field_spec!r}: {piece!r}')
                fs.type = types[0] if len(types) == 1 else tuple(types)
            elif parse.is_name(piece) or (name_signifier is not None and
                                          piece.startswith(name_signifier)):
                if fs.name is not None:
                    return (fs, 'Field specification piece is a name, '
                            'but the field name was already assigned: '
                            f'Piece {idx + 1} of {field_spec!r}: {piece!r}')
                fs.name = (piece
                           if name_signifier is None
                           else piece[len(name_signifier):])
            else:
                return (fs, 'Unrecognized field specification piece: '
                        f'not a number, name, or type: {piece!r}')
        return (fs, None)


# Forward declaration
HeaderSpecification = ForwardRef('HeaderSpecification')

class HeaderSpecification:
    """
    Representation of a user-specified tabular header as a
    collection of field specifications.

    Exists primarily to parse and validate user-specified headers so as
    to produce a working 'records.Header'.

    The main purpose of a header specification is to give names and
    types to fields, but it can also reference only a subset of fields
    and reorder them as for SQL 'select'.  This is accomplished by
    referencing fields by number.  Each field is implicitly numbered
    according to the order of its occurrence in the data.  Using this
    number allows one to refer to and select fields independently of one
    another.  For example, consider the following header.

        one:int, two:str, tre:float, fur:bool, fiv:any

    Because numbers are automatically assigned in sequence, this is the
    same as if one had written,

        1:one:int, 2:two:str, 3:tre:float, 4:fur:bool, 5:fiv:any

    and so one could select and reorder fields as desired,

        5:fiv:any, 1:one:int, 2:two:str, 4:fur:bool, 3:tre:float

    Numbers also allow one to give names and types in bulk, e.g., for
    data containing 1000 genes, weights, and responses,

        4-1003:gene:float, 1:id:int, y:float, wgt:float

    When not specified, numbers follow in sequence from the
    previously-specified number.  So 'y' and 'wgt' above are fields 2
    and 3 respectively.  Lastly, "|" can be used to form union types,
    e.g., `optional_number:int|float|null`.
    """

    @staticmethod
    def parse_from_text(
            text: str,
            csv_format: dict | str=_default_format,
            name2type: dict[str, type]=data_type_name2type,
            sep: str=':',
            name_signifier: str=None,
    ) -> tuple[HeaderSpecification | None, str | None]:
        """
        Create a 'HeaderSpecification' by parsing the given text.
        Return (header specification, error).

        First splits the text into fields using the given CSV format and
        then parses each field as a field specification.  The arguments
        'name2type', 'sep', and 'name_signifier' are passed to
        'FieldSpecification.parse'.

        Examples:
        * 'int, str, float, bool'
        * '"1-10:X:int|float"|Y:float'
        * 'id:int|lo:date|hi:date|lbl:int|wgt:float'
        * '4:lbl:int,wgt:float,10-20:X:float,6-9:X:int'
        """
        if isinstance(csv_format, str):
            csv_format = parse_format(csv_format)
        ifile = io.StringIO(text)
        reader = csv.reader(ifile, **csv_format)
        rows = iter(reader)
        first_row = next(rows, None)
        if first_row is None:
            excerpt = text[:79] + '…' if len(text) > 80 else text
            return (None, 'Could not parse a HeaderSpecification from: '
                    f'{excerpt!r}')
        return HeaderSpecification.parse_from_fields(
            first_row, name2type, sep, name_signifier)

    @staticmethod
    def parse_from_fields(
            field_specs: Iterable[str],
            name2type: dict[str, type]=data_type_name2type,
            sep: str=':',
            name_signifier: str=None,
    ) -> tuple[HeaderSpecification | None, str | None]:
        """
        Create a 'HeaderSpecification' by parsing each of the given
        strings as a field specification.  Return (header specification,
        error).

        The arguments 'name2type', 'sep', and 'name_signifier' are
        passed to 'FieldSpecification.parse'.
        """
        (fss, errs) = zip(*(
            FieldSpecification.parse(spec, name2type, sep, name_signifier)
            for spec in field_specs))
        for (idx, err) in enumerate(errs):
            if err is not None:
                return (
                    None, f'Error parsing field specification {idx + 1}: {err}')
        hs = HeaderSpecification(*fss)
        return (hs, None)

    @staticmethod
    def parse(
            specification: str | Iterable[str],
            csv_format: dict | str=_default_format,
            name2type: dict[str, type]=data_type_name2type,
            sep: str=':',
            name_signifier: str=None,
    ) -> HeaderSpecification:
        """
        Create a 'HeaderSpecification' by parsing the given header
        specification (string) or field specifications (strings).

        Operates by calling either 'parse_from_text' or
        'parse_from_fields' but throws an exception rather than
        returning an error.
        """
        (hs, err) = (
            HeaderSpecification.parse_from_text(
                specification, csv_format, name2type, sep, name_signifier)
            if isinstance(specification, str)
            else HeaderSpecification.parse_from_fields(
                    specification, name2type, sep, name_signifier))
        if err is not None:
            raise ValueError(err)
        return hs

    def __init__(self, *field_specs: Iterable[FieldSpecification]):
        self._field_specs = list(field_specs)
        self._number_range = None

    def __len__(self) -> int:
        return len(self._field_specs)

    def __iter__(self) -> Iterable[FieldSpecification]:
        return iter(self._field_specs)

    n_fields = __len__

    def number_range(self):
        """Return the range of the field numbers."""
        if self._number_range is None:
            if len(self) == 0:
                self._number_range = range(1, 1)
            else:
                min_num = min(r.start for (r, _) in self.numbered_fields())
                max_num = max(r.stop for (r, _) in self.numbered_fields())
                self._number_range = range(min_num, max_num)
        return self._number_range

    def numbered_fields(self) -> Iterable[tuple[range, FieldSpecification]]:
        """
        Generate this HS's field specifications along with their numbers.

        That is, infers the numbers for field specifications that don't
        have numbers.  Returns all the numbers as ranges for type
        stability.
        """
        num = 1
        for fs in self:
            if fs.number is None:
                yield (range(num, num + 1), fs)
                num += 1
            elif isinstance(fs.number, int):
                yield (range(fs.number, fs.number + 1), fs)
                num = fs.number + 1
            elif isinstance(fs.number, range):
                yield (fs.number, fs)
                num = fs.number.stop
            else:
                raise ValueError(f'Not a number or range: {fs.number!r}')

    def is_uniquely_numbered(self) -> bool:
        """
        Whether the field numbers are unique and ranges do not
        overlap.

        (A HS might reference a field multiple times.)
        """
        seen = set()
        for (range, _) in self.numbered_fields():
            if not seen.isdisjoint(range):
                return False
            seen.update(range)
        return True

    def is_contiguous(self) -> bool:
        """
        Whether the field numbers are contiguous, that is, have no
        gaps.

        (A HS might specify only certain fields and not others.)
        """
        seen = set()
        for (range, _) in self.numbered_fields():
            seen.update(range)
        range = self.number_range()
        return len(seen) == (range.stop - range.start)

    def is_in_order(self) -> bool:
        """
        Whether the field numbers are in order.

        (A HS might select fields in an arbitrary order.)
        """
        prev = None
        for (range, _) in self.numbered_fields():
            if prev is not None and range.start < prev.stop:
                return False
            prev = range
        return True

    def number_fields(self) -> HeaderSpecification:
        """
        Update this HS by numbering all fields whose number is
        `None`.
        """
        for (range, fs) in self.numbered_fields():
            if fs.number is None:
                fs.number = range if len(range) > 1 else range.start
        return self

    def expand_ranges(self) -> HeaderSpecification:
        """
        Update this HS by replacing all ranges with
        individually-numbered field specifications.
        """
        new_specs = []
        for fs in self:
            if isinstance(fs.number, range):
                new_specs.extend(FieldSpecification(number, fs.name, fs.type)
                                 for number in fs.number)
            else:
                new_specs.append(fs)
        self._field_specs = new_specs
        self._number_range = None
        return self

    def generate_names(self, name_prefix='_') -> HeaderSpecification:
        """
        Update this HS by generating names for all fields whose name
        is `None`.

        The generated name is the given prefix plus the field number.
        """
        for (range, fs) in self.numbered_fields():
            if fs.name is None:
                fs.name = f'{name_prefix}{range.start}'
                if len(range) > 1:
                    fs.name += f'-{range.stop - 1}'
        return self

    def sort_fields(self) -> HeaderSpecification:
        """Update this HS by ordering the fields by number."""
        ordered = sorted(self.numbered_fields(),
                         key=lambda rng_fs: (rng_fs[0].start, rng_fs[0].stop))
        self._field_specs = [fs for (_, fs) in ordered]
        self._number_range = None
        return self

    def fill_in_fields(self, n_fields=None) -> HeaderSpecification:
        """
        Update this HS by adding fields to fill in where there are
        gaps in the numbers.
        """
        num_stop = self.number_range().stop
        if n_fields is not None:
            num_stop = max(num_stop, n_fields + 1)
        nums = set(range(1, num_stop))
        for (range_, _) in self.numbered_fields():
            nums.difference_update(range_)
        if len(nums) == 0:
            return self
        nums = sorted(nums)
        range_start = nums[0]
        for idx in range(1, len(nums)):
            prev_num = nums[idx - 1]
            curr_num = nums[idx]
            if (curr_num - prev_num) > 1:
                self._field_specs.append(FieldSpecification(
                    range(range_start, prev_num + 1), None, None))
                range_start = curr_num
        self._field_specs.append(FieldSpecification(
            range(range_start, nums[-1] + 1), None, None))
        self._number_range = None
        return self

    def field_indices(self) -> list[int]:
        """
        Return a list of indices of the fields this header
        specification references (in the order they are referenced).

        These are the indices of the fields this specification selects.
        """
        idxs = []
        for (range_, _) in self.numbered_fields():
            idxs.extend(range(range_.start - 1, range_.stop - 1))
        return idxs

    def header(self) -> records.Header:
        """
        Create a header from this specification.

        The header is created from a copy of this HS whose ranges have
        been expanded and whose names have been generated.
        """
        # Copy so as to not modify self
        hs = HeaderSpecification(*self).expand_ranges().generate_names()
        names_types = ((fs.name, fs.type) for fs in hs)
        return records.Header(*names_types)
