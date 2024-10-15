"""Stuff for coding or working with code."""

# Copyright (c) 2024 Aubrey Barnard.
#
# This is free, open software released under the MIT license.  See
# `LICENSE` for details.


from collections.abc import Callable
import warnings


class Deprecated:
    """A decorator for deprecating functions and classes."""
    # Based on https://github.com/DavidPageGroup/cdm-data/blob/4ecf881bbc6a9de223001044677a2da6327dbe31/pypkg/cdmdata/core.py#L85

    _deprecation_warning_template = (
        "'{module}.{name}' is deprecated since version {since_version} "
        "and will be removed in version {remove_version}.  {message}"
    )

    def __init__(
            self,
            message: str='',
            since_version: str='<none>',
            remove_version: str='<none>',
            template: str=_deprecation_warning_template,
    ):
        """
        Create a deprecation decoration that uses the given attributes in
        its warning message.

        The warning message is constructed from the given template,
        which should be a {}-style format string.  See
        'deprecation_warning' for details.

        This can be used to decorate multiple things that share
        attributes, especially intended for applying the same
        deprecation versions to multiple things.  See 'w_message'.
        """
        self._msg = message
        self._dpr_ver = since_version
        self._rm_ver = remove_version
        self._tmplt = template
        self._module = None
        self._name = None

    def deprecation_warning(self) -> str:
        """
        Build a deprecation warning message by filling in the message
        template (a {}-style format string) with the following keys:
        module, name, since_version, remove_version, message.
        """
        return self._tmplt.format(
            module=self._module,
            name=self._name,
            since_version=self._dpr_ver,
            remove_version=self._rm_ver,
            message=self._msg,
        )

    @staticmethod
    def mk_call_deprecated(message: str, function: Callable) -> Callable:
        """
        Make a wrapper function that emits a 'DeprecationWarning' with the
        given message and then calls the given function.
        """
        def call_deprecated(*args, **kwds):
            # The call site is two stack levels up
            warnings.warn(DeprecationWarning(message), stacklevel=2)
            return function(*args, **kwds)
        return call_deprecated

    def mk_deprecated_function(self, function: Callable) -> Callable:
        """
        Deprecate the given function by wrapping it with a deprecation
        warning using this object's message.

        Uses the name and module of the given function in the
        deprecation warning.
        """
        self._module = function.__module__
        self._name = function.__name__
        return Deprecated.mk_call_deprecated(
            self.deprecation_warning(), function)

    def mk_deprecated_class(self, cls: type) -> type:
        """
        Deprecate the given class by wrapping its '__init__' with a
        deprecation warning using this object's message.  Return the
        same class object.

        Uses the name and module of the given class in the deprecation
        warning.
        """
        self._module = cls.__module__
        self._name = cls.__name__
        cls.__init__ = Deprecated.mk_call_deprecated(
            self.deprecation_warning(), cls.__init__)
        return cls

    def mk_deprecated(self, function_or_class: Callable | type):
        """
        Deprecate the given function or class by delegating to the
        appropriate 'mk_deprecated_function' or 'mk_deprecated_class'.
        """
        return (self.mk_deprecated_class(function_or_class)
                if isinstance(function_or_class, type)
                else self.mk_deprecated_function(function_or_class))

    def __call__(self, *args, **kwds):
        """Invoke as a decorator.  Call 'mk_deprecated'."""
        return self.mk_deprecated(*args, **kwds)

    def w_message(self, message: str):
        """
        Set the given message and return self.

        This allows a single 'Deprecated' object to decorate multiple
        things by customizing the message while sharing other
        deprecation attributes such as versions.

        ```
        deprecated = Deprecated(since_version='0.5', remove_version='1.0')
        ...
        @deprecated.w_message("Use 'new_one' instead.")
        def one(...):
        ...
        @deprecated.w_message("Use 'new_two' instead.")
        def two(...):
        ```
        """
        self._msg = message
        return self
