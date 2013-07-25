#! /usr/bin/env python

__all__ = ['FunctionTable']


import unittest
from collections import Mapping
from types import MethodType



class FunctionTable (Mapping):

    def __init__(self):
        self._table = {}

    def register(self, f):
        """A decorator which registers the function in this table and returns f unmodified."""
        self._table[f.__name__] = f
        return f

    def bind_instance(self, instance):
        """Given a FunctionTable of unbound methods, return a function table of methods bound to instance."""
        cls = type(instance)
        boundtable = FunctionTable()
        for name, unbound in self.iteritems():
            bound = MethodType(unbound, instance, cls)
            boundtable.register(bound)
        return boundtable

    # Mapping interface:
    def __getitem__(self, methodname):
        return self._table[methodname]

    def __iter__(self):
        return iter(self._table)

    def __len__(self):
        return len(self._table)



# Unit test code:
class GeneralFunctionTableTests (object):
    # This abstract class expects the following attributes:
    # ft   - a FunctionTable (may be bound)
    # add  - a function or bound method
    # mult - a function or bound method

    # This method can be overridden:
    def _get_func(self, f):
        assert isinstance(f, MethodType)
        return f.im_func

    # The former method is used for this test criterion:
    def _assertIsEquivalent(self, a, b):
        self.assertIs(self._get_func(a), self._get_func(b))

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



class UnboundFunctionTableTests (unittest.TestCase, GeneralFunctionTableTests):

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



class BoundFunctionTableTests (unittest.TestCase, GeneralFunctionTableTests):

    def setUp(self):

        unbound = FunctionTable()

        class C (object):
            x = 42

            @unbound.register
            def add(self, y):
                return self.x + y

            @unbound.register
            def mult(self, y):
                return self.x * y

        i = C()

        self.ft = unbound.bind_instance(i)
        self.add = i.add
        self.mult = i.mult



if __name__ == '__main__':
    unittest.main()
