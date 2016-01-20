# Convenient, high-level file API

import io
import os.path


# TODO how handle streams? can they be effectively wrapped?
# TODO how handle resolving names of executables?
# TODO path templates? shell names/tokens/words?

def new(filename_or_stream):
    if isinstance(filename_or_stream, str):
        return File(filename_or_stream)
    elif isinstance(filename_or_stream, io.IOBase):
        return Stream(filename_or_stream)
    else:
        raise TypeError('Not a filename or stream: {}'.format())


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

    @property
    def path(self):
        return self._path

    @property
    def name(self):
        return os.path.basename(self._path)

    @property
    def parent(self):
        if self._path == '.':
            return self # Avoids storing self reference
        elif self._parent is None:
            parent, name = os.path.split(self._path)
            if parent:
                self._parent = File(parent)
            else:
                self._parent = File('.')
        return self._parent

    @property
    def stem(self):
        return os.path.splitext(self.name)[0]

    @property
    def suffix(self):
        suffix = os.path.splitext(self.name)[1]
        if suffix.startswith('.'):
            suffix = suffix[1:]
        return suffix

    def abspath(self):
        # Note: must be method as relies on IO and may change over time
        return os.path.abspath(self._path)

    def exists(self):
        return os.path.exists(self._path)

    def is_readable(self):
        return (os.access(self._path, os.R_OK, effective_ids=True) and
                os.path.isfile(self._path))

    def assert_readable(self): # TODO better name? check/assert/?
        if not self.is_readable():
            raise ValueError('Not a readable file: {}'.format(self))

    def is_writable(self):
        if os.path.exists(self._path):
            return (os.path.isfile(self._path) and
                    os.access(self._path, os.W_OK, effective_ids=True))
        else:
            parent = self.parent.path
            return (os.path.exists(parent) and
                    os.path.isdir(parent) and
                    os.access(parent, os.W_OK, effective_ids=True))

    def assert_writable(self): # TODO better name? check/assert/?
        if not self.is_writable():
            raise ValueError('Not a writable file: {}'.format(self))

    # TODO is_executable

    def open(self, mode):
        # Handle compressed files
        suffix = self.suffix.lower()
        if suffix in ('bz2', 'bzip2'):
            import bz2
            return bz2.open(self._path, mode)
        elif suffix in ('xz', 'lzma'):
            import lzma
            return lzma.open(self._path, mode)
        elif suffix in ('gz', 'zip'):
            raise NotImplementedError(
                'Zip (de)compression not implemented.') # TODO
        else:
            return open(self._path, mode)

    def generate_lines(self):
        with self.open('rt') as file:
            for line in file:
                yield line

    def __repr__(self):
        return 'File({})'.format(repr(self._path))


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

    def open(self, mode):
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
        return self._stream

    def generate_lines(self):
        with self.open('rt') as file:
            for line in file:
                yield line

    def __repr__(self):
        return 'Stream({})'.format(self._name)
