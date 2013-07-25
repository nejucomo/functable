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
class FunctionTableTests (unittest.TestCase):
    def test_mapping_methods(self):
        ft = FunctionTable()

        @ft.register
        def add(x, y):
            return x + y

        @ft.register
        def mult(x, y):
            return x * y

        self._test_mapping_methods(ft, add, mult)

    def test_mapping_methods_on_bound_table(self):

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
        bound = unbound.bind_instance(i)

        self._test_mapping_methods(bound, i.add, i.mult)


    def _test_mapping_methods(self, ft, add, mult):

        self.assertEqual(2, len(ft))

        self.failUnless('add' in ft)
        self.failUnless('mult' in ft)

        self.assertEqual(['add', 'mult'], sorted(ft.keys()))
        self.assertEqual(['add', 'mult'], sorted(list(ft.iterkeys())))

        self.assertEqual(set([add, mult]), set(ft.values()))
        self.assertEqual(set([add, mult]), set(ft.itervalues()))

        self.assertEqual([('add', add), ('mult', mult)], sorted(ft.items()))
        self.assertEqual([('add', add), ('mult', mult)], sorted(list(ft.iteritems())))

        def assertIsOrIsEquivalentMethod(a, b):
            if isinstance(a, MethodType) and isinstance(b, MethodType):
                a = a.im_func
                b = b.im_func
            self.assertIs(a, b)

        assertIsOrIsEquivalentMethod(add, ft['add'])
        assertIsOrIsEquivalentMethod(mult, ft['mult'])

        assertIsOrIsEquivalentMethod(add, ft.get('add'))
        assertIsOrIsEquivalentMethod(mult, ft.get('mult'))

        assertIsOrIsEquivalentMethod(add, ft.get('add', 'banana'))
        assertIsOrIsEquivalentMethod(mult, ft.get('mult', 'bongo drum'))

        sentinel = object()
        self.assertIs(sentinel, ft.get('NON_EXISTENT', sentinel))



if __name__ == '__main__':
    unittest.main()
