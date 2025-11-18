#!/usr/bin/env python3
#
# Copyright (c) 2024 Nordic Semiconductor ASA
#
# SPDX-License-Identifier: Apache-2.0
#
"""Tests for CDDL unwrapping operator ~"""

from unittest import TestCase, main
from zcbor.zcbor import CddlXcoder, CddlParsingError


class TestUnwrapping(TestCase):
    """Test cases for the ~ unwrapping operator"""

    def test_basic_unwrapping_in_list(self):
        """Test basic unwrapping of a group into a list"""
        cddl = """
        Foo = (a: 1, b: 2)
        Bar = [~Foo, c: 3]
        """
        parser = CddlXcoder.from_cddl(cddl_string=cddl, default_max_qty=10)
        
        bar = parser.my_types['Bar']
        self.assertEqual(bar.type, 'LIST')
        self.assertEqual(len(bar.value), 3)
        
        # Check that the group was unwrapped
        self.assertEqual(bar.value[0].label, 'a')
        self.assertEqual(bar.value[0].value, 1)
        self.assertEqual(bar.value[1].label, 'b')
        self.assertEqual(bar.value[1].value, 2)
        self.assertEqual(bar.value[2].label, 'c')
        self.assertEqual(bar.value[2].value, 3)

    def test_unwrapping_in_map(self):
        """Test unwrapping of a group into a map"""
        cddl = """
        PersonFields = (
            "name" => tstr,
            "age" => uint
        )
        Employee = {~PersonFields, "id" => uint}
        """
        parser = CddlXcoder.from_cddl(cddl_string=cddl, default_max_qty=10)
        
        employee = parser.my_types['Employee']
        self.assertEqual(employee.type, 'MAP')
        self.assertEqual(len(employee.value), 3)
        
        # Check that keys are preserved
        self.assertIsNotNone(employee.value[0].key)
        self.assertIsNotNone(employee.value[1].key)
        self.assertIsNotNone(employee.value[2].key)

    def test_unwrapping_map_into_map(self):
        """Test unwrapping of a map into another map"""
        cddl = """
        BaseMap = {
            "x" => uint,
            "y" => uint
        }
        ExtendedMap = {~BaseMap, "z" => uint}
        """
        parser = CddlXcoder.from_cddl(cddl_string=cddl, default_max_qty=10)
        
        extended = parser.my_types['ExtendedMap']
        self.assertEqual(extended.type, 'MAP')
        self.assertEqual(len(extended.value), 3)
        
        # Check that all keys are present
        keys = [child.key.value for child in extended.value if child.key]
        self.assertEqual(sorted(keys), ['x', 'y', 'z'])

    def test_nested_unwrapping(self):
        """Test nested unwrapping across multiple levels"""
        cddl = """
        Inner = (i1: 1, i2: 2)
        Middle = (~Inner, m1: 3)
        Outer = [~Middle, o1: 4]
        """
        parser = CddlXcoder.from_cddl(cddl_string=cddl, default_max_qty=10)
        
        outer = parser.my_types['Outer']
        self.assertEqual(outer.type, 'LIST')
        self.assertEqual(len(outer.value), 4)
        
        # Check all labels are present at the same level
        labels = [child.label for child in outer.value]
        self.assertEqual(labels, ['i1', 'i2', 'm1', 'o1'])

    def test_unwrap_non_group_error(self):
        """Test that unwrapping a non-group/non-map type raises an error"""
        cddl = """
        NotAGroup = [1, 2, 3]
        Bar = [~NotAGroup, c: 3]
        """
        with self.assertRaises(CddlParsingError) as context:
            CddlXcoder.from_cddl(cddl_string=cddl, default_max_qty=10)
        
        self.assertIn("can only be applied to groups or maps", str(context.exception))

    def test_mixed_unwrapped_and_regular(self):
        """Test mixing unwrapped and regular group references"""
        cddl = """
        Data = (d1: uint, d2: tstr)
        Container = [~Data, Data]
        """
        parser = CddlXcoder.from_cddl(cddl_string=cddl, default_max_qty=10)
        
        container = parser.my_types['Container']
        self.assertEqual(container.type, 'LIST')
        # First two from unwrapped Data, then one reference for the regular Data
        # The regular Data will be flattened to its children during flatten()
        self.assertGreaterEqual(len(container.value), 2)
        
        # First two should be unwrapped
        self.assertEqual(container.value[0].type, 'UINT')
        self.assertEqual(container.value[1].type, 'TSTR')


if __name__ == '__main__':
    main()
