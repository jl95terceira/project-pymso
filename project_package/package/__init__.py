import dataclasses
import xml.parsers.expat as expat

from .      import xml, rels as rel_, cont
from ._util import *

class _DOCX_INTERNAL_FILE_PATHS:

     RELATIONSHIPS = '_rels/.rels'
     CONTENT_TYPES = '[Content_Types].xml'

@dataclasses.dataclass
class _DocXData:

    types:cont.Types         = dataclasses.field(default_factory=lambda: cont.Types ())
    rels :rel_.Relationships = dataclasses.field(default_factory=lambda: rel_.Relationships())

class DocX:

    """
    Document
    """
    
    def __init__(self):

        self._etrees:dict[str,Element] = {}
        self._data  :_DocXData         = _DocXData()

    @staticmethod
    def load_from_file(docf:zipfile.ZipFile|str):

        """
        Load a document from the given file (or from the file with the given name)
        """

        self                    = DocX()
        for fn,f in internal_files(docf):

            # relationships
            if fn == _DOCX_INTERNAL_FILE_PATHS.RELATIONSHIPS:

                self._data.rels = rel_.Relationships.get(f)

            # content types            
            elif fn == _DOCX_INTERNAL_FILE_PATHS.CONTENT_TYPES:

                self._data.types = cont.Types.get(f)

            # other (as element trees - not implemented yet)
            else:

                self._etrees[fn] = load_etree(f)

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
        with docf.open(_DOCX_INTERNAL_FILE_PATHS.RELATIONSHIPS, mode='w') as f:

            self._data.rels.put(f)

        # content types
        with docf.open(_DOCX_INTERNAL_FILE_PATHS.CONTENT_TYPES, mode='w') as f:

            self._data.types.put(f)

        # other (as element trees - not implemented yet)
        for fn,et in self._etrees.items():

            with docf.open(name=fn, mode='w') as f:

                dump_etree(f, et)

    def __eq__(self, other:'DocX'):

        return self._etrees == other._etrees and \
               self._data   == other._data

