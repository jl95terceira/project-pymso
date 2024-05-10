import dataclasses
import typing

from   ._util import *

_XML_DECLARATION_STANDALONE_REPR_MAP = {True :'yes',
                                        False:'no',}

@dataclasses.dataclass
class XmlDeclaration:

    version   :str  = dataclasses.field(default_factory=lambda: "0.0")
    encoding  :str  = dataclasses.field(default_factory=lambda: "???")
    standalone:bool = dataclasses.field(default_factory=lambda: True)

    @staticmethod
    def expat_handler(cb:typing.Callable[['XmlDeclaration'],None]):

        def HANDLER(version:str, encoding:str|None, standalone:int):

            cb(XmlDeclaration(version=version,encoding=encoding,standalone=bool(standalone)))

        return HANDLER

    def to_xml(self):

        return f'<?xml version="{self.version}" encoding="{self.encoding}" standalone="{_XML_DECLARATION_STANDALONE_REPR_MAP[self.standalone]}"?>'
