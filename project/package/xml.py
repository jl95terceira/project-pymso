import dataclasses
import typing

from   ._util import *

_XML_DECLARATION_STANDALONE_REPR_MAP = {True :'yes',
                                        False:'no',}

@dataclasses.dataclass
class Declaration:

    version   :str  = dataclasses.field(default="1.0")
    encoding  :str  = dataclasses.field(default="UTF-8")
    standalone:bool = dataclasses.field(default=True)

    @staticmethod
    def expat_handler(cb:typing.Callable[['Declaration'],None]):

        def HANDLER(version:str, encoding:str|None, standalone:int):

            cb(Declaration(version=version,encoding=encoding,standalone=bool(standalone)))

        return HANDLER

    def to_xml(self):

        return f'<?xml version="{self.version}" encoding="{self.encoding}" standalone="{_XML_DECLARATION_STANDALONE_REPR_MAP[self.standalone]}"?>'
