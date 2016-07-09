"""A Mapping abstraction for grouping functions.

A simple example:
>>> from functable import FunctionTable
>>> table = FunctionTable()
>>> @table.register
... def add(x, y):
...     return x + y
...
>>> @table.register
... def mult(x, y):
...     return x * y
...
>>> sorted(table.keys())
['add', 'mult']
>>> operation = 'add'
>>> table[operation](2, 3)
5
>>> operation = 'mult'
>>> table[operation](2, 3)
6
>>> operation = 'modulus'
>>> table[operation](2, 3)
Traceback (most recent call last):
  File "<stdin>", line 1, in ?
KeyError: 'modulus'

A FunctionTable is useful for doing dynamic dispatch in a more principled
manner.  For example, consider a script function which implements two
commands: "add" and "mult" so that it can be called like this:

$ myscript.py add 2 3
5
$ myscript.py mult 2 3
6

A common way to write this looks like this:
>>> def cmd_add(x, y):
...     return x + y
...
>>> def cmd_mult(x, y):
...     return x * y
...
>>> def main():
...     command = sys.argv[1]
...     args = map(int, sys.argv[2:])
...     func = globals()['cmd_' + command]
...     print func(*args)
...

With functable, we can write this:

>>> from functable import FunctionTable
>>> commands = FunctionTable()
>>> @commands.register
... def add(x, y):
...     return x + y
...
>>> @commands.register
... def mult(x, y):
...     return x + y
...
>>> def main():
...     command = sys.argv[1]
...     args = map(int, sys.argv[2:])
...     func = commands[command]
...     print func(*args)
...

Notice that if code wants to call the command functions elsewhere,
in the first example they must call "cmd_add(2, 3)", but with a
FunctionTable approach, they can naturally call "add(2, 3)".  The "cmd_"
prefix is used to manage a namespace of commands in an ad-hoc manner.
With FunctionTable this namespace is handled in a principled manner.

The FunctionTableProperty class is useful for the same kind of
principled namespace management, except on methods of a class, rather
than stand-alone functions:

>>> from functable import FunctionTableProperty
>>> class C (object):
...     value = 5
...
...     operations = FunctionTableProperty()
...
...     @operations.register
...     def add(self, x):
...         return self.value + x
...
>>> C.operations.keys()
['add']
>>> obj = C()
>>> obj.operations['add'](7)
12
>>> type(C.operations['add']) # the class-scoped table holds unbound methods:
<type 'function'>
>>> C.operations['add'](obj, 7)
12

However, sometimes it's important to distinguish the key names from the
actual method names, for example if there are multiple FunctionTables
with the same key namespace.  This is possible with the prefix argument
to the FunctionTable or FunctionTableProperty classes:

>>> class Codec (object):
...     encoders = FunctionTableProperty('_enc_')
...     decoders = FunctionTableProperty('_dec_')
...
...     def encode(self, obj):
...         tag = type(obj).__name__
...         encoding = self.encoders[tag](obj)
...         return (tag, encoding)
...
...     def decode(self, tup):
...         (tag, encoding) = tup
...         return self.decoders[tag](encoding)
...
...     @encoders.register
...     def _enc_int(self, i):
...         return str(i)
...
...     @decoders.register
...     def _dec_int(self, s):
...         return int(s)
...
>>> codec = Codec()
>>> codec.encode(42)
('int', '42')
>>> codec.decode(('int', '42'))
42
>>> codec.encoders.keys()
['int']
>>> codec.decoders.keys()
['int']
"""

import unittest
from collections import Mapping
from types import MethodType, FunctionType

from proptools import LazyProperty


__all__ = ['FunctionTable', 'FunctionTableProperty']


class FunctionTable (Mapping):

    def __init__(self, prefix=''):
        self.prefix = prefix
        self._table = {}

    def register(self, f, name=None):
        """Register f in self, and return f unmodified (for decorator use)."""
        if name is None:
            name = f.__name__
            assert name.startswith(self.prefix), repr((self.prefix, f))
            name = name[len(self.prefix):]
        self._table[name] = f
        return f

    # Mapping interface:
    def __getitem__(self, methodname):
        return self._table[methodname]

    def __iter__(self):
        return iter(self._table)

    def __len__(self):
        return len(self._table)


class FunctionTableProperty (FunctionTable, LazyProperty):

    def __init__(self, prefix=''):
        FunctionTable.__init__(self, prefix)

        def bind(instance):
            """Return a function table of methods bound to instance."""
            cls = type(instance)
            boundtable = FunctionTable(self.prefix)
            for name, unbound in self.iteritems():
                bound = MethodType(unbound, instance, cls)
                boundtable.register(bound)
            return boundtable

        LazyProperty.__init__(self, bind)


# Unit test code:
class GeneralFunctionTableTests (object):
    # This abstract class expects the following attributes:
    # ft   - a FunctionTable (may be bound)
    # add  - a function or bound method
    # mult - a function or bound method

    # addresult - the result of calling add
    # addargs   - a tuple to pass to add

    # multresult - the result of calling mult
    # multargs   - a tuple to pass to mult

    # This method can be overridden:
    def _get_func(self, f):
        assert isinstance(f, MethodType)
        return f.im_func

    # The former method is used for this test criterion:
    def _assertIsEquivalent(self, a, b):
        self.assertIs(self._get_func(a), self._get_func(b))

    # This is used by some test cases:
    funcnames = ['add', 'mult']

    # Tests:
    def test_len(self):
        self.assertEqual(2, len(self.ft))

    def test_membership(self):
        self.failUnless('add' in self.ft)
        self.failUnless('mult' in self.ft)

    def test_keys_and_iterkeys(self):
        expected = ['add', 'mult']
        self.assertEqual(expected, sorted(self.ft.keys()))
        self.assertEqual(expected, sorted(list(self.ft.iterkeys())))

    def test_values_and_itervalues(self):
        expected = set([self.add, self.mult])
        self.assertEqual(expected, set(self.ft.values()))
        self.assertEqual(expected, set(self.ft.itervalues()))

    def test_items_and_iteritems(self):
        expected = [('add', self.add), ('mult', self.mult)]
        self.assertEqual(expected, sorted(self.ft.items()))
        self.assertEqual(expected, sorted(list(self.ft.iteritems())))

    def test___getitem__successful(self):
        self._assertIsEquivalent(self.add, self.ft['add'])
        self._assertIsEquivalent(self.mult, self.ft['mult'])

    def test___getitem__unsuccessful(self):
        self.assertRaises(KeyError, self.ft.__getitem__, 'NON_EXISTENT')

    def test_successful_get_no_default(self):
        self._assertIsEquivalent(self.add, self.ft.get('add'))
        self._assertIsEquivalent(self.mult, self.ft.get('mult'))

    def test_successful_get_with_default(self):
        self._assertIsEquivalent(self.add, self.ft.get('add', 'banana'))
        self._assertIsEquivalent(self.mult, self.ft.get('mult', 'bongo drum'))

    def test_unsuccessful_get_no_default(self):
        self.assertIs(None, self.ft.get('NON_EXISTENT'))

    def test_unsuccessful_get_with_default(self):
        sentinel = object()
        self.assertIs(sentinel, self.ft.get('NON_EXISTENT', sentinel))

    def test_call_add(self):
        self.assertEqual(self.addresult, self.ft['add'](*self.addargs))
        self.assertEqual(self.multresult, self.ft['mult'](*self.multargs))


class UnboundFunctionTableTests (unittest.TestCase, GeneralFunctionTableTests):

    addargs = (2, 3)
    addresult = 5

    multargs = (2, 3)
    multresult = 6

    def setUp(self):
        self.ft = FunctionTable()

        @self.ft.register
        def add(x, y):
            return x + y

        self.add = add

        @self.ft.register
        def mult(x, y):
            return x * y

        self.mult = mult

    def _get_func(self, f):
        return f

    def test_explicit_name(self):
        self.ft.register(lambda a, b: a ** b, 'pow')
        self.assertEqual(8, self.ft['pow'](2, 3))


class UnboundPrefixedFunctionTableTests (
        unittest.TestCase,
        GeneralFunctionTableTests):

    addargs = (2, 3)
    addresult = 5

    multargs = (2, 3)
    multresult = 6

    def setUp(self):
        self.ft = FunctionTable('foo_')

        @self.ft.register
        def foo_add(x, y):
            return x + y

        self.add = foo_add

        @self.ft.register
        def foo_mult(x, y):
            return x * y

        self.mult = foo_mult

    def _get_func(self, f):
        return f


class FunctionTablePropertyTests (
        unittest.TestCase,
        GeneralFunctionTableTests):

    addargs = (3,)
    addresult = 45

    multargs = (3,)
    multresult = 126

    def setUp(self):

        class C (object):
            ft = FunctionTableProperty()

            x = 42

            @ft.register
            def add(self, y):
                return self.x + y

            @ft.register
            def mult(self, y):
                return self.x * y

        i = C()

        self.cls = C
        self.instance = i
        self.ft = i.ft
        self.add = i.add
        self.mult = i.mult

    def test_unbound_lookup(self):
        for name in self.funcnames:
            self.assertIsInstance(self.cls.ft[name], FunctionType)

    def test_bound_lookup(self):
        for name in self.funcnames:
            self.assertIsInstance(self.instance.ft[name], MethodType)


class PrefixedFunctionTablePropertyTests (
        unittest.TestCase,
        GeneralFunctionTableTests):

    addargs = (3,)
    addresult = 45

    multargs = (3,)
    multresult = 126

    def setUp(self):

        class C (object):
            ft = FunctionTableProperty('foo_')

            x = 42

            @ft.register
            def foo_add(self, y):
                return self.x + y

            @ft.register
            def foo_mult(self, y):
                return self.x * y

        i = C()

        self.cls = C
        self.instance = i
        self.ft = i.ft
        self.add = i.foo_add
        self.mult = i.foo_mult

    def test_unbound_lookup(self):
        for name in self.funcnames:
            self.assertIsInstance(self.cls.ft[name], FunctionType)

    def test_bound_lookup(self):
        for name in self.funcnames:
            self.assertIsInstance(self.instance.ft[name], MethodType)
