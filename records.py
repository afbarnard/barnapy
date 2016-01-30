# Record processing

import csv

from . import logging


def read_records_from_csv(
        file, record_constructor=None, commentchar='#'):
    """Reads records from a CSV-formatted file.

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
            if ((len(rawrow) == 1 and len(first) == 0) or
                    first.startswith(commentchar)):
                continue
            # Parse, validate, construct
            try:
                row = (record_constructor(rawrow)
                       if record_constructor is not None else rawrow)
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
