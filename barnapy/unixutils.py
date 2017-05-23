"""Unix-like utilities"""

# Copyright (c) 2017 Aubrey Barnard.  This is free software released
# under the MIT license.  See LICENSE for details.


import io
import os
import re


def head(filename, num_lines=10):
    lines = []
    # Read the first so many lines
    with open(filename, 'rt') as file:
        for idx, line in enumerate(file):
            if idx >= num_lines:
                break
            lines.append(line)
    return lines


def tail(filename, num_lines=10, chunk_size=1024):
    lines = []
    with open(filename, 'rt') as file:
        # Go to the end
        position = file.seek(0, io.SEEK_END)
        # Loop until far back enough in the file
        while len(lines) < num_lines and position > 0:
            # Go back a chunk (but not negative)
            position = max(position - chunk_size, 0)
            file.seek(position)
            # Read the lines from here on out
            lines = [line for line in file]
    # Return the last so many lines
    return lines[-num_lines:]


def ls(path='.'):
    walker = os.walk(path)
    _, directories, files = next(walker)
    return (directories, files)


_shell_pattern_metacharacter_pattern = re.compile(r'(\*|\?)')

def regex_from_pattern(pattern, case_sensitive=True):
    """only supports '*' and '?' for now"""
    # Pass through existing regexs.  (Work around private regex object
    # type.)
    if isinstance(pattern,
                  type(_shell_pattern_metacharacter_pattern)):
        return pattern
    # Build regex from shell pattern
    pieces = _shell_pattern_metacharacter_pattern.split(pattern)
    # Translate pieces
    for idx, piece in enumerate(pieces):
        # Convert shell pattern metacharacters to regexs
        match = _shell_pattern_metacharacter_pattern.match(piece)
        if match is not None:
            if piece == '*':
                pieces[idx] = '.*'
            elif piece == '?':
                pieces[idx] = '.'
            else:
                raise ValueError(
                    'Not a shell pattern metacharacter: {!r}'
                    .format(piece))
        # Handle other pieces
        else:
            pieces[idx] = re.escape(piece)
    # Build regex
    flags = 0
    if not case_sensitive:
        flags = re.IGNORECASE
    return re.compile(''.join(pieces), flags)


def glob(filenames, *patterns, case_sensitive=True):
    # Turn all shell patterns into regexs
    regexs = [regex_from_pattern(p, case_sensitive) for p in patterns]
    # Match each filename against each regex
    for filename in filenames:
        for regex in regexs:
            if regex.match(filename) is not None:
                yield filename
                break
