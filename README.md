Barnapy
=======

Barnapy is a motley collection of Python born of the common code in my
research projects.  It is essentially infrastructure for data
processing.  I hope you find it interesting or useful.

While I intend for this to be good, useful software, this is more a
public record of my work and a resource for others than a mature
package.  As such, I put more effort into building functionality than
into having good documentation, maintaining API stability, or similar
concerns.  With that said, I aim to have well-designed APIs with
reasonable, intuitive functionality backed by clear, quality
implementations.  I will continue to improve this software as I can,
both in terms of features and quality.  If interest and use increases,
then I will emphasize making this more like an "official" set of
modules.  In the meantime, you will just have to browse around or even
read the code!


Requirements
------------

See `setup.py`.


License
-------

Barnapy is free, open source software, released under the MIT license.
See the `LICENSE` file for details.


Install
-------

Use [Pip]( https://pip.pypa.io/) to install Barnapy directly from GitHub.

    python3 -m pip install --user --upgrade https://github.com/afbarnard/barnapy/archive/master.zip#egg=barnapy

If you need a specific version, replace "master" with the branch, tag,
or commit name.

You can also download using Git by changing the URL.

    python3 -m pip install --user --upgrade git+https://github.com/afbarnard/barnapy.git@master#egg=barnapy

Again, replace "master" to get what you want.  This becomes more
valuable in combination with the [`--editable`](
https://pip.pypa.io/en/stable/reference/pip_install/#editable-installs)
option which keeps the Git repository around for later use ("development
mode").  Note that to use such a URL you must have Git installed.

You may find it helpful to isolate the install by creating a [Python
virtual environment](
https://packaging.python.org/tutorials/installing-packages/#creating-virtual-environments)
or a [Conda environment](
https://conda.io/docs/user-guide/getting-started.html#managing-envs)
before installing.  In these cases, omit the `--user` option.


Contact
-------

I prefer contact through GitHub.  [Open an issue](
https://github.com/afbarnard/esal/issues/new) to ask a question, request
an enhancement, or report a bug.  To contribute, use the regular fork
and pull request work flow.


-----

Copyright (c) 2015-2023 Aubrey Barnard, all files in this repository.
Copyright (c) 2016, 2018, 2023 Aubrey Barnard, this file.

This is free software released under the MIT license.  See `LICENSE` for
details.
