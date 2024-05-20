import unittest

import io
import typing

from . import test
from .. import package

class Tests(unittest.TestCase):

    def setUp(self):

        pass

    def _test(self, fn:str, parsef:typing.Callable[[io.BytesIO], None]):

        with package.internal_file_by_name(test.OFFICE_FILES.EXAMPLE, fn) as f:

            parsef(f)

    def test_parse_Content_Types(self):

        self._test(package.DOCX_INTERNAL_FILE_PATHS.CONTENT_TYPES, package.content_types.Types.get)

    def test_parse_Relationships(self):

        self._test(package.DOCX_INTERNAL_FILE_PATHS.RELATIONSHIPS, package.rels.Relationships.get)

    def test_parse_DocProps_App(self):

        self._test(package.DOCX_INTERNAL_FILE_PATHS.DOCPROPS_APP, package.docprops.app.Properties.get)

    def test_parse_DocProps_Core(self):

        self._test(package.DOCX_INTERNAL_FILE_PATHS.DOCPROPS_CORE, package.docprops.core.CoreProperties.get)

    def test_parse_Word_Document(self):

        self._test(package.DOCX_INTERNAL_FILE_PATHS.WORD_DOCUMENT, package.word.document.Document.get)
