#

import os.path


# TODO how handle streams? can they be effectively wrapped?

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

    def is_readable(self):
        return (os.access(self._path, os.R_OK, effective_ids=True) and
                os.path.isfile(self._path))

    def is_writeable(self):
        if os.path.exists(self._path):
            return (os.path.isfile(self._path) and
                    os.access(self._path, os.W_OK, effective_ids=True))
        else:
            parent = self.parent.path
            return (os.path.exists(parent) and
                    os.path.isdir(parent) and
                    os.access(parent, os.W_OK, effective_ids=True))

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
