Barnapy
=======

Barnapy is a motley collection of Python born of the common code in my
research projects.  It is essentially infrastructure for data
processing.  I hope you find it interesting or useful.

This is more a public record of my work and a resource for others than a
project.  As such, I make no promises regarding API stability,
correctness, documentation, and the like.  I aim to continually improve
this software, and I will emphasize making this more like an "official"
set of modules as interest and use increases.


Requirements
------------

* Python >= 3.4 (which introduced re.fullmatch)


License
-------

Barnapy is free, open source software, released under the MIT license.
See the `LICENSE` file for details.


Install
-------

Use [Pip](https://pip.pypa.io/) to install Barnapy directly from GitHub.

    python3 -m pip install --user --upgrade https://github.com/afbarnard/barnapy/archive/master.zip#egg=barnapy

If you need a specific version, replace "master" with the branch, tag,
or commit name.

You can also download using Git by changing the URL.  Again, replace
"master" to get what you want.  This becomes more valuable in
combination with the [`--editable`](
https://pip.pypa.io/en/stable/reference/pip_install/#editable-installs)
option which keeps the Git repository around for later use ("development
mode").  Note that to use such a URL you must have Git installed.

    python3 -m pip install --user --upgrade git+https://github.com/afbarnard/barnapy.git@master#egg=barnapy

You may find it helpful to isolate the install by creating a [Python
virtual environment](
https://packaging.python.org/tutorials/installing-packages/#creating-virtual-environments)
or a [Conda environment](
https://conda.io/docs/user-guide/getting-started.html#managing-envs)
before installing.  In these cases, omit the `--user` option.

[Conda](https://conda.io/docs/index.html) is valuable particularly for
working with multiple versions of Python simultaneously and for managing
scientific packages.  (Pip sometimes tries to recompile NumPy and SciPy,
for example, but Conda always uses pre-built packages.)  I recommend
using the minimal [Miniconda](https://conda.io/miniconda.html) in these
cases.


Contact
-------

I prefer contact through GitHub.  [Open an
issue](https://github.com/afbarnard/esal/issues/new) to ask a question,
request an enhancement, or report a bug.  To contribute, use the regular
fork and pull request work flow.


-----

Copyright (c) 2017 Aubrey Barnard.  This is free software released under
the MIT license.  See LICENSE for details.
