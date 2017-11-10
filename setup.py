"""Barnapy package definition and install configuration"""

# Copyright (c) 2017 Aubrey Barnard.  This is free software released
# under the MIT license.  See `LICENSE` for details.


import setuptools

import barnapy.version


# Define package attributes
setuptools.setup(

    # Basics
    name='barnapy',
    version=barnapy.version.__version__,
    url='https://github.com/afbarnard/barnapy',
    license='MIT',
    author='Aubrey Barnard',
    #author_email='',

    # Description
    description='Infrastructure for data processing',
    long_description="""
Infrastructure for data processing and other common code collected from
my research projects.  A personal standard library of sorts.
""".strip(),
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
