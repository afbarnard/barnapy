"""
Utilities for working with tabular data in various separated values
formats.
"""

# Copyright (c) 2022-2023 Aubrey Barnard.
#
# This is free software released under the MIT License.  See LICENSE for
# details.


import csv


def parse_csv_dialect(chars):
    """
    Interpret the given string as a dialect for the Python CSV
    module.

    As few or as many characters as desired can be given; any dialect
    parameter not specified will not be included in the dialect.  This
    allows default parameter values, such as those specified in the
    Python CSV module, to "show through".  This is intended to make CSV
    dialects easy to specify on the command line.

    Character.  Dialect Parameter.
    1. Delimiter.
    2. Quote character.
    3. Doubling or escaping: d=doubling, e=escaping.
       ('doublequote' parameter)
    4. Escape character.  Space (`' '`) means `None` [1].
    5. Quoting mode: m=minimal, a=all, n=none, o=objects (non-numeric
       values).
    6. Whether to trim (strip) whitespace from values: t=trim, k=keep.
       ('skipinitialspace' parameter)
    7. Whether all records need to have the same length: s=strict,
       l=loose.  ('strict' parameter)
    8. Line terminator (for the writer).  String of all remaining
       characters.


    ### Examples ###

    `',"d mkl\\r\\n'`: Python CSV module defaults.

    `'|"e\\\\mks\\n'`: Pipe-delimited, minimally quoted fields as for
        SQLite import on Unix.

    `' "E\\\\MTL\\n\\r'`: Space-aligned, human-readable tables on Acorn BBC.

    `'\\t"D OKS\\r'`: Excel-like TSV on old Mac.


    [1] While NUL (`'\\x00'`) would be a natural candidate for
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
    dialect = {}
    if len(chars) >= 1:
        dialect['delimiter'] = chars[0]
    if len(chars) >= 2:
        dialect['quotechar'] = chars[1]
    if len(chars) >= 3:
        if chars[2] in ('d', 'D'):
            dialect['doublequote'] = True
        elif chars[2] in ('e', 'E'):
            dialect['doublequote'] = False
        else:
            raise ValueError(
                "Unrecognized CSV dialect parameter: doubling or escaping: "
                f"'{chars[2]}' (not 'd' or 'e')")
    if len(chars) >= 4:
        if chars[3] == ' ':
            dialect['escapechar'] = None
        else:
            dialect['escapechar'] = chars[3]
    if len(chars) >= 5:
        if chars[4] in ('m', 'M'):
            dialect['quoting'] = csv.QUOTE_MINIMAL
        elif chars[4] in ('a', 'A'):
            dialect['quoting'] = csv.QUOTE_ALL
        elif chars[4] in ('n', 'N'):
            dialect['quoting'] = csv.QUOTE_NONE
        elif chars[4] in ('o', 'O'):
            dialect['quoting'] = csv.QUOTE_NONNUMERIC
        else:
            raise ValueError(
                "Unrecognized CSV dialect parameter: quoting mode: "
                f"'{chars[4]}' (not 'm', 'a', 'n', or 'o')")
    if len(chars) >= 6:
        if chars[5] in ('k', 'K'):
            dialect['skipinitialspace'] = False
        elif chars[5] in ('t', 'T'):
            dialect['skipinitialspace'] = True
        else:
            raise ValueError(
                "Unrecognized CSV dialect parameter: trim space: "
                f"'{chars[5]}' (not 'k' or 't')")
    if len(chars) >= 7:
        if chars[6] in ('l', 'L'):
            dialect['strict'] = False
        elif chars[6] in ('s', 'S'):
            dialect['strict'] = True
        else:
            raise ValueError(
                "Unrecognized CSV dialect parameter: strict length: "
                f"'{chars[6]}' (not 'l' or 's')")
    if len(chars) >= 8:
        dialect['lineterminator'] = chars[7:]
    return dialect
