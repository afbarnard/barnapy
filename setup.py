"""Barnapy package definition and install configuration"""

# Copyright (c) 2017 Aubrey Barnard.  This is free software released
# under the MIT license.  See `LICENSE` for details.


import setuptools

import barnapy


# Extract the short and long descriptions from the documentation
_desc_paragraphs = barnapy.__doc__.strip().split('\n\n')
# Make sure to keep the short description to a single line
_desc_short = _desc_paragraphs[0].replace('\n', ' ')
# Include all the package documentation in the long description except
# for the first and last paragraphs which are the short description and
# the copyright notice, respectively
_desc_long = '\n\n'.join(_desc_paragraphs[1:-1])


# Define package attributes
setuptools.setup(

    # Basics
    name='barnapy',
    version=barnapy.__version__,
    url='https://github.com/afbarnard/barnapy',
    license='MIT',
    author='Aubrey Barnard',
    #author_email='',

    # Description
    description=_desc_short,
    long_description=_desc_long,
    keywords=[
        'data processing',
        'personal standard library',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Scientific/Engineering :: Information Analysis',
        'Topic :: Software Development :: Libraries',
        'Topic :: Utilities',
    ],

    # Requirements
    python_requires='>=3.4',
    install_requires=[], # No dependencies

    # API
    packages=setuptools.find_packages(),

)
