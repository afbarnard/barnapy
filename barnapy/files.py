"""Convenient, high-level file API"""

# Copyright (c) 2015-2018, 2023 Aubrey Barnard.
#
# This is free, open software released under the MIT license.  See
# `LICENSE` for details.


import contextlib
import io
import os.path


# TODO deprecate all this in favor of `pathlib` and a generic `open` function that works for a variety of inputs

# TODO how handle streams? can they be effectively wrapped?
# TODO how handle resolving names of executables?
# TODO path templates? shell names/tokens/words?


def new(file):
    if isinstance(file, File):
        return file
    elif isinstance(file, str):
        return File(file)
    elif isinstance(file, io.IOBase):
        return Stream(file)
    else:
        raise TypeError('Not a filename or stream: {}'.format(file))

def open(path, mode='rt', **opts):
    return new(path).open(mode=mode, **opts)


class File:
    """File paths as objects, like pathlib."""

    # TODO consider subclassing pathlib with Python 3.4

    def __init__(self, *path_components):
        num_components = len(path_components)
        if num_components == 0 or path_components[0] == '':
            self._path = '.'
        elif num_components == 1:
            self._path = path_components[0]
        else:
            self._path = os.path.join(*path_components)
        # Strip trailing separator
        if self._path.endswith(os.path.sep):
            self._path = self._path[:-1]
        # Properties for lazy construction
        self._parent = None
        self._pieces = None

    @property
    def path(self):
        return self._path

    @property
    def name(self):
        return os.path.basename(self.path)

    @property
    def parent(self):
        if self.path == '.':
            return self # Avoids storing self reference
        elif self._parent is None:
            parent, name = os.path.split(self.path)
            if parent:
                self._parent = File(parent)
            else:
                self._parent = File('.')
        return self._parent

    @property
    def pieces(self):
        if self._pieces is None:
            # Split on dots
            raw_pieces = self.name.split('.')
            # Add dots back to all pieces except the first piece
            pieces = ['.' + p for p in raw_pieces[1:]]
            # Add the first piece back if not empty
            if raw_pieces[0] != '':
                pieces.insert(0, raw_pieces[0])
            self._pieces = pieces
        return self._pieces

    @property
    def stem(self):
        return self.pieces[0]

    @property
    def suffix(self):
        pieces = self.pieces
        if len(pieces) > 1:
            return pieces[-1]
        else:
            return ''

    @property
    def suffixes(self):
        return self.pieces[1:]

    def abspath(self):
        # Note: must be method as relies on IO and may change over time
        return os.path.abspath(self.path)

    def exists(self):
        return os.path.exists(self.path)

    def is_readable(self):
        return os.access(self.path, os.R_OK, effective_ids=(
            os.access in os.supports_effective_ids))

    def is_executable(self):
        return os.access(self.path, os.X_OK, effective_ids=(
            os.access in os.supports_effective_ids))

    def is_file(self):
        return os.path.isfile(self.path)

    def is_directory(self):
        return os.path.isdir(self.path)

    def is_readable_file(self):
        return self.exists() and self.is_file() and self.is_readable()

    def is_readable_directory(self):
        return (self.exists()
                and self.is_directory()
                and self.is_readable()
                and self.is_executable())

    def assert_readable(self): # TODO better name? check/assert/?
        if not self.is_readable():
            raise ValueError('Not readable: {}'.format(self))

    def is_writable(self):
        if os.path.exists(self.path):
            return os.access(self.path, os.W_OK, effective_ids=(
                os.access in os.supports_effective_ids))
        else:
            parent = self.parent.path
            return (os.path.exists(parent) and
                    os.path.isdir(parent) and
                    os.access(parent, os.W_OK, effective_ids=(
                        os.access in os.supports_effective_ids)))

    def assert_writable(self): # TODO better name? check/assert/?
        if not self.is_writable():
            raise ValueError('Not writable: {}'.format(self))

    def open(self, mode='rt', **opts):
        # Handle compressed files
        suffix = self.suffix.lower().lstrip('.')
        if suffix in ('bz2', 'bzip2'):
            import bz2
            return bz2.open(self.path, mode=mode, **opts)
        elif suffix in ('xz', 'lzma'):
            import lzma
            return lzma.open(self.path, mode=mode, **opts)
        # Use gzip for all common Lempel-Ziv compression suffixes
        elif suffix in ('gz', 'z', 'Z'):
            import gzip
            return gzip.open(self.path, mode=mode, **opts)
        else:
            return io.open(self.path, mode=mode, **opts)

    def generate_lines(self):
        with self.open(mode='rt') as file:
            for line in file:
                yield line

    def __repr__(self):
        return 'File({})'.format(repr(self.path))

    def __str__(self):
        return self.path

    def join(self, *path_components):
        return File(self.path, *path_components)


class Stream:

    def __init__(self, stream, name=None):
        # Check for subclass of IOBase
        if not isinstance(stream, io.IOBase):
            raise TypeError(
                'Not an instance of IOBase: {!r}'.format(stream))
        self._stream = stream
        self._name = name
        if name is None:
            if hasattr(stream, 'name'):
                self._name = stream.name
            else:
                self._name = repr(stream)

    @property
    def name(self):
        return self._name

    def is_readable(self):
        return self._stream.readable()

    def assert_readable(self):
        if not self.is_readable():
            raise ValueError('Not a readable stream: {}'.format(self))

    def is_writable(self):
        return self._stream.writable()

    def assert_writable(self):
        if not self.is_writable():
            raise ValueError('Not a writable stream: {}'.format(self))

    def open(self, mode='rt', **opts): # FIXME return a file-like object that behaves properly
        """
        Return a context manager (not a file-like object) for this
        stream.
        """
        # Check mode is compatible with the existing stream
        mode = mode.lower()
        if 'r' in mode:
            self.assert_readable()
        if 'w' in mode or 'a' in mode:
            self.assert_writable()
        if '+' in mode:
            self.assert_readable()
            self.assert_writable()
        text_stream = isinstance(self._stream, io.TextIOBase)
        if text_stream and 'b' in mode:
            raise TypeError(
                'Text stream not compatible with binary mode: {}'
                .format(mode))
        if not text_stream and 't' in mode:
            raise TypeError(
                'Binary stream not compatible with text mode: {}'
                .format(mode))
        # Wrap the stream so that the wrapper can be closed without
        # closing the stream
        return contextlib.nullcontext(self._stream)

    def generate_lines(self):
        with self.open(mode='rt') as file:
            for line in file:
                yield line

    def __repr__(self):
        return 'Stream({})'.format(self._name)
