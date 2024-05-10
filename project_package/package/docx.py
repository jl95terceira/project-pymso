import dataclasses
import enum
import io
import sys
import xml.parsers.expat as expat

from   .rels import *
from   ._util import *

@dataclasses.dataclass
class _DocXData:

    rels:Relationships = dataclasses.field(default_factory=lambda: Relationships())

class DocX:

    def __init__(self):

        self._etrees:dict[str,Element] = {}
        self._data  :_DocXData         = _DocXData()

    @staticmethod
    def load_from_file(docf:zipfile.ZipFile|str):

        self                    = DocX()
        for fn,f in internal_files(docf):

            # relationships
            if fn == DOCX_INTERNAL_FILE_PATHS.RELATIONSHIPS:
#            if False:

                self._data.rels = Relationships.get(f)
            
            # other (into element trees)
            else:

                self._etrees[fn] = load_etree(f)

        return self

    def save_to_file  (self, docf:zipfile.ZipFile|str):

        if isinstance(docf, str):

            with zipfile.ZipFile(file=docf, mode='w') as docf:

                self.save_to_file(docf)

            return
        
        # relationships
        with docf.open(DOCX_INTERNAL_FILE_PATHS.RELATIONSHIPS, mode='w') as f:

            self._data.rels.put(f)

        # other (out of element trees)
        for fn,et in self._etrees.items():

            with docf.open(name=fn, mode='w') as f:

                dump_etree(f, et)

    def __eq__(self, other:'DocX'):

        return self._etrees == other._etrees and \
               self._data   == other._data
