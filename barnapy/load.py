"""Utilities for loading / executing files"""

# Copyright (c) 2018 Aubrey Barnard.  This is free software released
# under the MIT license.  See LICENSE for details.


import importlib.util
import pathlib


def search_path(target, *dirs, allow_files=False):
    """
    Search the given directories for the given file.  Return a
    `pathlib.Path` if found, else `None`.

    target: Filename as string or `pathlib.Path`.
    dirs: Directories to search as strings or `pathlib.Path`s.
    allow_files: Whether to allow files in `dirs`.  If so, `target` will
        be searched for in a file's parent directory, as a sibling of
        that file.  If not, all paths in `dirs` will be assumed to be
        directories.
    """
    if not isinstance(target, pathlib.Path):
        target = pathlib.Path(target)
    for dir in dirs:
        if not isinstance(dir, pathlib.Path):
            dir = pathlib.Path(dir)
        dir = dir.expanduser()
        if not dir.exists():
            continue
        if allow_files and dir.is_file():
            dir = dir.parent
        candidate = dir.joinpath(target)
        if candidate.exists():
            return candidate
    return None


def py_file(filename):
    """
    Execute the given Python file and return its namespace.

    This function is very similar to `runpy.run_path` but guarantees
    that the executed definitions will work after it returns, whereas
    `run_path` does not make this guarantee.

    filename: String or `pathlib.Path`.
    """
    # Read the given Python file
    with open(filename, 'rt') as file:
        lines = file.readlines()
    # Combine lines into a single source string
    source = ''.join(lines)
    code = compile(source, str(filename), 'exec', dont_inherit=True)
    # Create an environment for the execution
    env = {}
    # Execute the compiled Python code
    exec(code, env) # Returns None
    # Return the environment corresponding to the file
    return env


def py_module(filename):
    """
    Execute the given Python file and return it as module.

    filename: String or `pathlib.Path`.
    """
    # Make sure `filename` is a `Path`
    if not isinstance(filename, pathlib.Path):
        filename = pathlib.Path(filename)
    # Prepare the file for importing as a module
    mod_spec = importlib.util.spec_from_file_location(filename.stem, filename)
    # Initialize a module object from the spec
    mod = importlib.util.module_from_spec(mod_spec)
    # Construct the module object
    mod_spec.loader.exec_module(mod)
    return mod
