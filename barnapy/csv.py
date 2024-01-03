"""
Utilities for working with tabular data in various separated values
formats.
"""

# Copyright (c) 2022-2023 Aubrey Barnard.
#
# This is free software released under the MIT License.  See LICENSE for
# details.


import csv
import io
import re

from . import parse


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
) -> tuple[bool,list[str],str]:
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
