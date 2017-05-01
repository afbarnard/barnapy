"""Unix-like utilities"""

# Copyright (c) 2017 Aubrey Barnard.  This is free software released
# under the MIT license.  See LICENSE for details.


import io
import os


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
