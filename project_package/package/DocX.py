import dataclasses
import enum
import io
import sys
import xml.parsers.expat as expat

from   . import Relationships
from   ._util import *

class Class:

    def __init__(self, docxfn:str):

        self._generic:dict[str,Element] = {}
        for fn,f in internal_files(docxfn):

            if fn == '_rels/.rels' and False:

                self._rels = Relationships(f)
            
            else:

                self._generic[fn] = load_etree(f)

    def save(self,docxfn:str):

        with zipfile.ZipFile(file=docxfn, mode='w') as zf:

            for fn,et in self._generic.items():

                with zf.open(name=fn, mode='w') as f:

                    dump_etree(f, et)

sys.modules[__name__] = Class
