"""Representing and processing records."""

# Copyright (c) 2015-2016, 2023 Aubrey Barnard.
#
# This is free, open software released under the MIT license.  See
# `LICENSE` for details.


from collections.abc import Iterable, Sequence
from typing import TypeAlias, Union
import csv
import itertools as itools

from . import logging


# Forward declarations
Header: TypeAlias = 'Header'
Record: TypeAlias = 'Record'


def read_records_from_csv(
        file, record_constructor=None, commentchar='#'):
    """Generate records by reading from a CSV-formatted file.

    Discards comment lines (ones that start with the given comment
    character) and whitespace lines.  Logs errors rather than
    propagating exceptions.  If given, the record constructor is
    responsible for parsing, validating, and converting the given fields
    and assembling them into a record.  (It may throw exceptions.)  It
    essentially defines a schema on the file.  If a record constructor
    is not given, the raw CSV records (lists of strings) are returned.
    """
    logger = logging.getLogger(__name__).getChild(
        'read_records_from_csv')
    rownum = 1
    num_bad = 0
    # Wrap the following in a try/finally so that the logging is
    # executed even if not all the rows are yielded
    try:
        for rawrow in csv.reader(file):
            # Discard empty rows
            if rawrow is None or len(rawrow) == 0:
                continue
            # Discard whitespace and comments
            first = rawrow[0].lstrip()
            if ((len(rawrow) == 1 and len(first) == 0)
                    or first.startswith(commentchar)):
                continue
            # Parse, validate, construct
            try:
                row = (record_constructor(rawrow)
                       if record_constructor is not None
                       else rawrow)
            except Exception as e:
                logger.exception(
                        'Discarding bad record {}: {}', rownum, rawrow)
                num_bad += 1
            else:
                # Return the row if not None
                if row is not None:
                    yield row
                    rownum += 1
    finally:
        # Log results of reading
        num_records = rownum - 1
        logger.info(
            'Processed {}/{} records.  Discarded {}/{} records.',
            num_records - num_bad, num_records, num_bad, num_records)


def is_pair(obj): # TODO where should this live?
    try:
        (one, two) = obj
        return True
    except (TypeError, ValueError):
        return False


FieldType = type | tuple[type]
Field = tuple[str, FieldType]


# Based on 'github.com: afbarnard/fitamord.git: fitamord/records.py:
# Header' @a8be1314 2018-04-11 which inherits from
# 'fitamord/collections.py: NamedItems' @8bd1064f 2017-12-06.
# Encompasses edits from 2016-2018 and 2017, respectively.  This is
# pretty much completely reimplemented, however, so I'm treating it as
# all new for purposes of copyright.
class Header:
    """
    A (read-only) description of an ordered collection of fields
    where each field has a name and a type; the type of a record or
    named tuple.  Conceptually a tuple of (name, type) pairs.
    """

    # Construct API

    @staticmethod
    def _collect_check_fields(*fields, names=None, types=None, **name2type):
        if names is not None:
            names = list(names)
        if types is not None:
            types = list(types)
        if names is not None:
            if types is not None and len(names) != len(types):
                raise ValueError(
                    "Lengths of 'names' and 'types' are not the same")
            elif types is None:
                types = [None] * len(names)
        # Collect and check fields
        ok_fields = []
        nms = set()
        for (name, typ_) in itools.chain(
            fields,
            zip(names, types, strict=True) if names is not None else (),
            name2type.items(),
        ):
            if not isinstance(name, str):
                raise ValueError(f"'name' is not a string: {name!r}")
            if name in nms:
                raise ValueError(f'Duplicate name: {name!r}')
            if not Header.is_type(type):
                raise ValueError(f'Not a type or tuple of types: {typ_!r}')
            ok_fields.append((name, typ_))
        if len(ok_fields) <= 0:
            raise ValueError('No fields, names, nor types were specified')
        return ok_fields

    __slots__ = ('_names', '_types', '_nm2idx')

    def __init__(self, *fields, names=None, types=None, **name2type):
        """
        Create a header from the given fields.

        The fields can be specified as any combination of (1) an
        iterable of (name, type) pairs, (2) both an iterable of names
        and a corresponding iterable of types, (3) just an iterable of
        names (fills in types as `None`), or (4) name=type keyword
        arguments.  A type of `None` means any type (to be distinguished
        from both `object` and `NoneType`).  A type is anything that can
        be the second argument to 'isinstance', so a subclass of 'type'
        or a tuple of types.
        """
        ok_fields = Header._collect_check_fields(
            *fields, names=names, types=types, **name2type)
        (names, types) = zip(*ok_fields)
        self._names = tuple(names)
        self._types = tuple(types)
        self._nm2idx = {n: i for (i, (n, t)) in enumerate(ok_fields)}

    # Query API

    @staticmethod
    def is_type(obj: object) -> bool:
        return isinstance(obj, type) or (
            isinstance(obj, tuple) and
            all(isinstance(t, type) for t in obj))

    @staticmethod
    def is_field(obj: object) -> bool:
        if not is_pair(obj):
            return False
        (name, type) = obj
        return isinstance(name, str) and Header.is_type(type)

    def n_fields(self) -> int:
        return len(self._names)

    def has_index(self, index: int) -> bool:
        return isinstance(index, int) and 0 <= index < self.n_fields()

    def has_name(self, name: str) -> bool:
        return name in self._nm2idx

    def has_type(self, type: FieldType) -> bool:
        return type in self.types()

    def has_field(self, field: Field) -> bool:
        if not Header.is_field(field):
            raise TypeError(f'Not a (name, type) pair: {field!r}')
        (name, type) = field
        idx = self._nm2idx.get(name)
        return idx is not None and self.type_at(idx) == type

    def names(self) -> tuple[str]:
        return self._names

    def types(self) -> tuple[FieldType]:
        return self._types

    def fields(self) -> Iterable[Field]:
        return zip(self._names, self._types, strict=True)

    def name_at(self, index: int) -> str:
        return self._names[index]

    def type_at(self, index: int) -> FieldType:
        return self._types[index]

    def field_at(self, index: int) -> Field:
        return (self._names[index], self._types[index])

    def index_of(self, name: str) -> int:
        return self._nm2idx[name]

    def type_of(self, name: str) -> FieldType:
        return self.type_at(self.index_of(name))

    def field_of(self, name: str) -> Field:
        return self.field_at(self.index_of(name))

    def index(self, key: int | str) -> int:
        if isinstance(key, int):
            return key
        return self.index_of(key)

    def get_index(self, key: int | str, default: object=None) -> int | object:
        if isinstance(key, int):
            return key if 0 <= key < self.n_fields() else default
        idx = self._nm2idx.get(key)
        return idx if idx is not None else default

    # Emulate a tuple of fields

    __len__ = n_fields

    def __getitem__(self, key: int | str) -> Field:
        return self.field_at(self.index(key))

    __iter__ = fields

    def __contains__(self, obj: object) -> bool:
        try:
            return self.has_field(obj)
        except TypeError:
            return False

    def __eq__(self, other: object) -> bool:
        return (type(self) == type(other) and
                self._names == other._names and
                self._types == other._types)

    def __hash__(self) -> int:
        return hash((self._names, self._types))

    def __repr__(self) -> str:
        return '{}{!r}'.format(type(self).__qualname__, self.fields())

    def __str__(self) -> str:
        return '{}({})'.format(
            type(self).__qualname__,
            ', '.join(f'{n}: {t}' for (n, t) in self.fields()),
        )

    # Useful functionality

    def has_instance(self, record: Union[Record, Sequence[object]]) -> bool:
        """
        Whether this header has the given record as an instance.
        (Whether the record is an instance of this header.)
        """
        if len(record) != len(self):
            return False
        for (type, value) in zip(self.types(), record, strict=True):
            if type is not None and not isinstance(value, type):
                return False
        return True

    def project(self, *keys: tuple[int | str]) -> Header:
        """
        Create a new header with only the given fields (specified by
        name or index).

        This is "project" in the relational algebra sense of select /
        reorder fields.
        """
        return Header(*(self[k] for k in keys))

    def add_fields(
            self, *fields, names=None, types=None, **name2type,
    ) -> Header:
        fields = Header._collect_check_fields(
            *fields, names=names, types=types, **name2type)
        return Header(*self.fields(), *fields)

    def del_fields(self, *keys: tuple[int | str]) -> Header:
        idxs = set(self.index(k) for k in keys)
        keep = [i for i in range(len(self)) if i not in idxs]
        return self.project(*keep)

    def rename_fields(self, **old2new: dict[str,str]) -> Header:
        fields = list(self.fields())
        for (idx, (old_name, type)) in enumerate(fields):
            new_name = old2new.get(old_name)
            if new_name is not None:
                fields[idx] = (new_name, type)
        return Header(*fields)

    def replace_types(self, **name2type: dict[str,FieldType]) -> Header:
        fields = list(self.fields())
        for (idx, (name, old_type)) in enumerate(fields):
            new_type = name2type.get(name)
            if new_type is not None:
                fields[idx] = (name, new_type)
        return Header(*fields)


class Record:

    __slots__ = ('_hdr', '_vals')

    def __init__(self, header: Header, values: Sequence[object]):
        if len(header) != len(values):
            raise ValueError(
                "Lengths of 'header' and 'values' are not the same")
        self._hdr = header
        self._vals = values

    @property
    def header(self):
        return self._hdr

    @property
    def values(self):
        return self._vals

    def __len__(self):
        return len(self._vals)

    def __iter__(self):
        return iter(self._vals)

    def __getitem__(self, key: int | str):
        return self.values[self.header.index(key)]

    def __setitem__(self, key: int | str, val: object):
        self.values[self.header.index(key)] = val

    def __getattr__(self, name: str):
        idx = self._hdr.get_index(name)
        if idx is None:
            raise AttributeError(f'Record has no such attribute: {name!r}')
        return self.values[idx]

    def __setattr__(self, name: str, value: object):
        if name in Record.__slots__:
            object.__setattr__(self, name, value)
            return
        idx = self._hdr.get_index(name)
        if idx is None:
            raise AttributeError(f'Record has no such attribute: {name!r}')
        self.values[idx] = value
