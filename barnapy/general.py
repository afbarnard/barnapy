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


def exec_python_file(python_filename):
    # Load the given Python file
    with open(python_filename, 'rt') as python_file:
        lines = python_file.readlines()
    # Combine lines into a single source string
    source = ''.join(lines)
    code = compile(source, python_filename, 'exec')
    # Create an environment for the execution
    env = {}
    # Execute the compiled Python code
    exec(code, env) # Returns None
    # Return the environment corresponding to the file
    return env
