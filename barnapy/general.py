"""General-purpose functionality and utilities"""

# Copyright (c) 2017 Aubrey Barnard.  This is free software released
# under the MIT license.  See LICENSE for details.


def make_error_if_none(
        function,
        error=ValueError,
        message='Expected not None but got: {}',
        ):
    """Return a function that will raise an error if the given function
    returns None.

    function: Any callable

    error: Exception type to raise

    message: Error message, optionally containing the substitutions
       '{args}' or '{kwargs}' for the failing arguments.

    """
    def error_if_none(*args, **kwargs):
        # Make the call
        value = function(*args, **kwargs)
        # Return the value if not None
        if value is not None:
            return value
        # Otherwise raise error
        else:
            raise error(message.format(args=args, kwargs=kwargs))
    return error_if_none


def make_default_if_none(function, default):
    """Return a function that will return the given default value if the
    given function returns None.

    """
    def default_if_none(*args, **kwargs):
        # Make the call
        value = function(*args, **kwargs)
        if value is not None:
            return value
        else:
            return default
    return default_if_none


def track_iterator( # TODO implement adaptive, time-based frequency
        iterator,
        tracker,
        track_every=100,
        track_init=False,
        track_end=False,
):
    count = 0
    if track_init:
        tracker(count)
    for item in iterator:
        yield item
        count += 1
        if count % track_every == 0:
            tracker(count)
    if track_end and count % track_every != 0:
        tracker(count)
