import os.path
import unittest

from   . import test
from   ..package import *
from   ..package._util import *

class TestsForDocX(unittest.TestCase): 

    def setUp(self): pass
    
    def test_DocX_equal(self): 

        doc      = DocX.load_from_file(test.OFFICE_FILES.EXAMPLE)
        doc            .save_to_file  (test.OFFICE_FILES.EXAMPLE_COPY)
        doc_copy = DocX.load_from_file(test.OFFICE_FILES.EXAMPLE_COPY)
        self.assertEqual(doc,doc_copy,msg="a doc loaded from a file is equal to the doc that was saved to such file")
