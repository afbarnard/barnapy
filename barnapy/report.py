"""Tools for organizing data for display"""

# Copyright (c) 2019 Aubrey Barnard.
#
# This is free software released under the MIT license.  See `LICENSE`
# for details.


def reshape_table(
        records,
        fields=None,
        dimension1_fields=1,
        dimension2_fields=1,
        value_field=None,
):
    """
    Reshape a multidimensional array into a two-dimensional table and
    return it along with the keys of each dimension.

    It is common for data to be stored in a database in logical
    key-value format where the keys consist of several fields.  Such a
    DB table is effectively a multidimensional array.  This function
    reshapes such multidimensional data into a table with two dimensions
    so that it can be displayed.

    For example, imagine you have the following results from some
    experiments:

        algorithm | parameters | data set | score
        -----------------------------------------
        algA      | default    | synth    | 0.237
        algA      | tunedA     | synth    | 0.035
        algA      | default    | real     | 0.556
        algA      | tunedA     | real     | 0.485
        newB      | default    | synth    | 0.318
        newB      | tunedB     | synth    | 0.556
        newB      | default    | real     | 0.518
        newB      | tunedB     | real     | 0.920

    The above table of data is effectively a mapping from (alg, params,
    data) tuples to scores.  This function is for taking such data and
    organizing it for display, like in a table of scores that compares
    methods across data sets, for example:

        DS \ Alg | A-def | A-tun | B-def | B-tun
        ----------------------------------------
        synth    | 0.237 | 0.035 | 0.318 | 0.556
        real     | 0.556 | 0.485 | 0.518 | 0.920

    The above table organizes the data into two dimensions, each
    accessed by a compound key: (data set,) vs. (algorithm, parameters).

    Return a (table: dict[k1,k2]:object, dimension1-keys: set,
    dimension2-keys: set) triple where the table maps (key1, key2) pairs
    to values and the following two objects are the sets of keys for
    each dimension.

    records: Iterable<Sequence<object>>
        Tabular data as an iterable of records, where each record is an
        indexable collection.
    fields: Iterable<str> | Iterable<int> | N:int | None
        Names of the fields of each record as strings or integers.  If
        N, use `range(N)`.  If `None`, use `range(len(records[0]))`.
    dimension1_fields: Iterable<str> | Iterable<int> | int
        Names of the fields to include in the first dimension.  A subset
        of `fields`.
    dimension2_fields: Iterable<str> | Iterable<int> | int
        Names of the fields to include in the second dimension.  A
        subset of `fields` disjoint from `dimension1_fields`.
    value_field: str | int | None
        Name of the field in `fields` to use as the value.  May be
        omitted if only one field is left after excluding the
        dimensions.

    duplicate_key: # TODO how handle keys with multiple values (which happens easily with projection)
    """
    # Infer and convert all field arguments into tuples of indices /
    # names that can be interpreted as sets
    if fields is None:
        fields = len(records[0])
    if isinstance(fields, int):
        fields = range(fields)
    fields = tuple(fields)
    if (isinstance(dimension1_fields, int) and
            isinstance(dimension2_fields, int)):
        d1_flds = tuple(range(dimension1_fields))
        d2_flds = tuple(range(dimension1_fields,
                              dimension1_fields + dimension2_fields))
    elif isinstance(dimension1_fields, int):
        d2_flds = tuple(dimension2_fields)
        d1_flds = tuple(f for f in fields if f not in d2_flds)
        d1_flds = d1_flds[:dimension1_fields]
    elif isinstance(dimension2_fields, int):
        d1_flds = tuple(dimension1_fields)
        d2_flds = tuple(f for f in fields if f not in d1_flds)
        d2_flds = d2_flds[:dimension2_fields]
    else:
        d1_flds = tuple(dimension1_fields)
        d2_flds = tuple(dimension2_fields)
    # Map fields to indices
    fld2idx = {f: i for i, f in enumerate(fields)}
    # Check for sanity among arguments
    if not (set(d1_flds) < fld2idx.keys()):
        raise ValueError(
            'Bad dimension 1 fields: Not a proper subset of the fields '
            '{!r}: {!r}'.format(fields, d1_flds))
    if not (set(d2_flds) < fld2idx.keys()):
        raise ValueError(
            'Bad dimension 2 fields: Not a proper subset of the fields '
            '{!r}: {!r}'.format(fields, d2_flds))
    if len(set(d1_flds) & set(d2_flds)) > 0:
        raise ValueError(
            'Dimensions 1 and 2 have fields in common: {!r}'
            .format(set(d1_flds) & set(d2_flds)))
    # Infer the value field
    if value_field is None:
        value_field = fld2idx.keys() - set(d1_flds) - set(d2_flds)
        if len(value_field) != 1:
            raise ValueError(
                'Bad possible value fields: Does not contain a unique '
                'field: {!r}'.format(value_field))
        value_field = value_field.pop()
    if value_field not in fld2idx:
        raise ValueError(
            'Bad value field: Not among the fields {!r}: {!r}'
            .format(fields, value_field))
    # Sets for collecting the values in each dimension
    d1_keys = set()
    d2_keys = set()
    values = {}
    # Reorganize the records by the given dimensions
    for idx, record in enumerate(records):
        # Check the record format
        if len(record) != len(fld2idx):
            raise ValueError('Bad record: Record {} does not match '
                             'the fields {!r}: {!r}'
                             .format(idx, fields, record))
        # Extract the dimension values
        d1_key = tuple(record[fld2idx[f]] for f in d1_flds)
        d1_keys.add(d1_key)
        d2_key = tuple(record[fld2idx[f]] for f in d2_flds)
        d2_keys.add(d2_key)
        val = record[fld2idx[value_field]]
        key = (d1_key, d2_key)
        if key in values:
            raise ValueError('Key {!r} has 2 values: {!r} {!r}'
                             .format(key, values[key], val))
        else:
            values[d1_key, d2_key] = val
    return values, d1_keys, d2_keys


def matrix_from(table, keys1, keys2, default=0):
    return [[table.get((k1, k2), default) for k2 in keys2]
            for k1 in keys1]
