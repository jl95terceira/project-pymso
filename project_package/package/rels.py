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

@dataclasses.dataclass
class Relationships:

    d:dict[str,Relationship] = dataclasses.field(default_factory=lambda: {})

    _REL_TARGET_MAP = {'docProps/app.xml' : Relationship.Target.APP,
                       'docProps/core.xml': Relationship.Target.CORE,
                       'word/document.xml': Relationship.Target.DOCUMENT}

    @staticmethod
    def get(f:io.BytesIO):

        self = Relationships()
        xp = expat.ParserCreate()
        class _State(enum.Enum):

            INIT          = 0
            RELATIONSHIPS = 1

        st = [_State.INIT]
        # handle XML declaration
        def xmldeclh(vers,enc,stal):

            self._xmldecl = XmlDeclaration(version=vers,encoding=enc,standalone=bool(stal))

        xp.XmlDeclHandler = xmldeclh
        # handle elements
        def start_elem_h(name :str, 
                         attrs:dict[str,str]):

            if st[0] is _State.INIT:

                if name != 'Relationships': raise Exception('found at root an element other than Relationships')
                self._xmlns = attrs['xmlns']
                st[0] = _State.RELATIONSHIPS
            
            elif st[0] is _State.RELATIONSHIPS:

                if name != 'Relationship': raise Exception('found in Relationships an element that is not a Relationship')
                self.d[attrs['Id']] = Relationship(type  =attrs['Type'],
                                                   target=Relationships._REL_TARGET_MAP[attrs['Target']])
                print(self.d[attrs['Id']])

        xp.StartElementHandler = start_elem_h
        # do it
        xp.ParseFile(f)
        return self
