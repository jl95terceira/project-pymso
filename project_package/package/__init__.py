import dataclasses
import xml.parsers.expat as expat

from .      import content_types, xml, rels, docprops, word
from ._util import *

class _DOCX_INTERNAL_FILE_PATHS:

     RELATIONSHIPS = '_rels/.rels'
     CONTENT_TYPES = '[Content_Types].xml'
     DOCPROPS_APP  = 'docProps/app.xml'
     DOCPROPS_CORE = 'docProps/core.xml'
     WORD_DOCUMENT = 'word/document.xml'

@dataclasses.dataclass
class _DocXData:

    types:'content_types.Types' = dataclasses.field(default_factory=lambda: content_types.Types())
    rels :'rels.Relationships'  = dataclasses.field(default_factory=lambda: rels.Relationships ())
    props:'docprops.DocProps'   = dataclasses.field(default_factory=lambda: docprops.DocProps  ())
    word :'word.Word'           = dataclasses.field(default_factory=lambda: word.Word          ())

class DocX:

    """
    Document
    """
    
    # relationships
    def _load_rels    (self, f:io.BytesIO): self._data.rels          = rels.Relationships          .get(f)
    # content types
    def _load_types   (self, f:io.BytesIO): self._data.types         = content_types.Types         .get(f)
    # document properties - app
    def _load_doc_app (self, f:io.BytesIO): self._data.props.app     = docprops.app.Properties     .get(f)
    # document properties - core
    def _load_doc_core(self, f:io.BytesIO): self._data.props.core    = docprops.core.CoreProperties.get(f)
    # word - document
    def _load_word_doc(self, f:io.BytesIO): self._data.word.document = word.document.Document      .get(f)
    
    def __init__(self):

        self._etrees      :dict[str,Node]                          = {}
        self._data        :_DocXData                               = _DocXData()
        self._loading_dict:dict[str,typing.Callable[[io.BytesIO]]] = {
            _DOCX_INTERNAL_FILE_PATHS.RELATIONSHIPS: self._load_rels,
            _DOCX_INTERNAL_FILE_PATHS.CONTENT_TYPES: self._load_types,
            _DOCX_INTERNAL_FILE_PATHS.DOCPROPS_APP : self._load_doc_app,
            _DOCX_INTERNAL_FILE_PATHS.DOCPROPS_CORE: self._load_doc_core,
            _DOCX_INTERNAL_FILE_PATHS.WORD_DOCUMENT: self._load_word_doc,
        }

    @staticmethod
    def load_from_file(docf:zipfile.ZipFile|str):

        """
        Load a document from the given file (or from the file with the given name)
        """

        self = DocX()
        for fn,f in internal_files(docf):

            if fn in self._loading_dict:

                self._loading_dict[fn](f)

            # other (as element trees - not implemented yet)
            else:

                self._etrees[fn] = load_tree(f)

        return self

    def save_to_file  (self, docf:zipfile.ZipFile|str):

        """
        Save this document to the given file (or to the file with the given name)
        """

        if isinstance(docf, str):

            with zipfile.ZipFile(file=docf, mode='w') as docf:

                self.save_to_file(docf)

            return
        
        # relationships
        with docf.open(_DOCX_INTERNAL_FILE_PATHS.RELATIONSHIPS, mode='w') as f: self._data.rels         .put(f)
        # content types
        with docf.open(_DOCX_INTERNAL_FILE_PATHS.CONTENT_TYPES, mode='w') as f: self._data.types        .put(f)
        # document properties - app
        with docf.open(_DOCX_INTERNAL_FILE_PATHS.DOCPROPS_APP , mode='w') as f: self._data.props.app    .put(f)
        # document properties - core
        with docf.open(_DOCX_INTERNAL_FILE_PATHS.DOCPROPS_CORE, mode='w') as f: self._data.props.core   .put(f)
        # word - document
        with docf.open(_DOCX_INTERNAL_FILE_PATHS.WORD_DOCUMENT, mode='w') as f: self._data.word.document.put(f)
        # other (as element trees - not implemented yet)
        for fn,et in self._etrees.items():

            with docf.open(name=fn, mode='w') as f:

                dump_tree(f, et)

    def __eq__(self, other:'DocX'):

        return self._etrees == other._etrees and \
               self._data   == other._data

