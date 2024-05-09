import os.path
import unittest

from   . import test
from   ..package._util import *

class TestsForElement    (unittest.TestCase):

    @staticmethod
    def create_Element(): return Element(name    ="foo",
                                         args    =("hello",{"world":123}),
                                         children=[Element(name="bar"), Element(name="John", args={"The answer":42})])

    def setUp(self):

        self.e1 = TestsForElement.create_Element()
        self.e2 = TestsForElement.create_Element()

    def test_Element_equal(self):

        self.assertEqual(self.e1,self.e2,msg="elements with equal attributes are equal")
    
    def test_Element_not_equal_name(self):

        self.e2.name = "bar"
        self.assertNotEqual(self.e1,self.e2,msg="elements with different name are NOT equal")

    def test_Element_not_equal_args(self):

        self.e2.args = tuple()
        self.assertNotEqual(self.e1,self.e2,msg="elements with different args are NOT equal")

    def test_Element_not_equal_children(self):

        self.e2.children.pop()
        self.assertNotEqual(self.e1,self.e2,msg="elements with different children are NOT equal")
    
class TestsForElementTree(unittest.TestCase):

    def setUp(self):

        self.et1 = load_etree_map(test.file_path(file_name=test.FILES.EXAMPLE))

    def test_ElementTree_equal(self):

        et2 = load_etree_map(test.file_path(file_name=test.FILES.EXAMPLE))
        self.assertEqual   (self.et1,et2,msg="element trees loaded from the same file are equal")

    def test_ElementTree_not_equal(self):

        et3 = load_etree_map(test.file_path(file_name=test.FILES.EXAMPLE_EDITED))
        self.assertNotEqual(self.et1,et3,msg="element trees loaded from files with different (uncompressed) content are NOT equal")
