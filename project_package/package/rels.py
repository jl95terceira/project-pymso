import dataclasses
import enum
import io
import sys
import xml.parsers.expat as expat

from   ._util import *
from   .xmldecl import XmlDeclaration

@dataclasses.dataclass
class Relationship:

    type  :str
    target:'Target'

    class Target(enum.Enum):

        APP      = 0
        CORE     = 1
        DOCUMENT = 2
    
    def to_xml(self, id:str):

        return f'<Relationship Id="{id}" Type="{self.type}" Target="{_REL_TARGET_RMAP[self.target]}"/>'

_REL_TARGET_MAP  = {'docProps/app.xml' : Relationship.Target.APP,
                    'docProps/core.xml': Relationship.Target.CORE,
                    'word/document.xml': Relationship.Target.DOCUMENT}
_REL_TARGET_RMAP = {v:k for k,v in _REL_TARGET_MAP.items()}

@dataclasses.dataclass
class Relationships:

    xd   :XmlDeclaration         = dataclasses.field(default_factory=lambda: XmlDeclaration())
    xmlns:str                    = dataclasses.field(default_factory=lambda: "")
    dictt:dict[str,Relationship] = dataclasses.field(default_factory=lambda: {})

    @staticmethod
    def get(f:io.BytesIO):

        self = Relationships()
        xp   = expat.ParserCreate()
        class _State(enum.Enum):

            INIT          = 0
            RELATIONSHIPS = 1

        st = [_State.INIT]
        # handle XML declaration
        def _f(xd:XmlDeclaration):

            self.xd = xd

        xp.XmlDeclHandler = XmlDeclaration.expat_handler(_f)
        # handle elements
        def START_ELEM_HANDLER(name :str, attrs:dict[str,str]):

            if st[0] is _State.INIT:

                if name != 'Relationships': raise Exception('found at root an element other than Relationships')
                # ...
                self.xmlns = attrs['xmlns']
                st[0] = _State.RELATIONSHIPS
            
            elif st[0] is _State.RELATIONSHIPS:

                if name != 'Relationship': raise Exception('found in Relationships an element that is not a Relationship')
                # ...
                self.dictt[attrs['Id']] = Relationship(type  =                attrs['Type'],
                                                       target=_REL_TARGET_MAP[attrs['Target']])

        xp.StartElementHandler = START_ELEM_HANDLER
        # do it
        xp.ParseFile(f)
        return self

    def put(self, f:io.BytesIO):

        f.write(self.xd.to_xml().encode())
        f.write(f'<Relationships xmlns="{self.xmlns}">'.encode())
        for id,rel in self.dictt.items():

            f.write(rel.to_xml(id).encode())

        f.write(f'</Relationships>'.encode())
