#!/bin/bash

PYTHONPATH=".:$PYTHONPATH"


echo '=== pyflakes ==='
pyflakes ./functable.py || exit $?
echo 'pyflakes completed.'


echo -e '\n=== Running unittests ==='
coverage run --branch ./functable.py --verbose
STATUS=$?

echo -e '\n--- Generating Coverage Report ---'
coverage html --include='functable*'

echo 'Report generated.'

[ "$STATUS" -eq 0 ] || exit $STATUS

echo -e '\n=== Running doctests ==='
exec python -m doctest ./functable.py
