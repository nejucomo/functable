#! /usr/bin/env python

import sys
from setuptools import setup


if 'upload' in sys.argv:
    if '--sign' not in sys.argv and sys.argv[1:] != ['upload', '--help']:
        raise SystemExit('Refusing to upload unsigned packages.')


setup(
    name='functable',
    description='A small utility for grouping functions/methods into a table.',
    url='https://github.org/nejucomo/functable',
    license='GPLv3',
    version='0.2',
    author='Nathan Wilcox',
    author_email='nejucomo@gmail.com',
    py_modules=['functable'],
    install_requires=['proptools >= 0.1'],
)
