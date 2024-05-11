import dataclasses
import enum
import io
import sys
import xml.parsers.expat as expat

from   ._util   import *
from   .xmldecl import XmlDeclaration

@dataclasses.dataclass
class Relationship(ElementLike):

    type  :str = dataclasses.field(default=MISSING)
    target:str = dataclasses.field(default=MISSING)

    def to_xml(self, id:str):

        return f'<Relationship Id="{id}" Type="{self.type}" Target="{self.target}"/>{''.join(self.tail)}'

@dataclasses.dataclass
class Relationships:

    xmld :XmlDeclaration         = dataclasses.field(default_factory=lambda: XmlDeclaration())
    xmlns:str                    = dataclasses.field(default        ="http://schemas.openxmlformats.org/package/2006/relationships")
    dictt:dict[str,Relationship] = dataclasses.field(default_factory=lambda: {})

    @staticmethod
    def get(f:io.BytesIO):

        self = Relationships()
        xp   = expat.ParserCreate()
        class _State(enum.Enum):

            INIT          = 0
            RELATIONSHIPS = 1

        st   = [_State.INIT]
        curp = Pointer[ElementLike]()
        # handle XML declaration
        def XML_DECL_CB(xmld:XmlDeclaration):

            self.xmld = xmld
            curp.x    = xmld

        xp.XmlDeclHandler = XmlDeclaration.expat_handler(XML_DECL_CB)
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
                rel                     = Relationship(type  =attrs['Type'],
                                                       target=attrs['Target'])
                self.dictt[attrs['Id']] = rel
                curp.x                  = rel

        xp.StartElementHandler = START_ELEM_HANDLER
        xp.EndElementHandler   = lambda name: None
        def DEFAULT_HANDLER(data: str):

            curp.x.tail.append(data)
            pass

        xp.DefaultHandler = DEFAULT_HANDLER
        # do it
        xp.ParseFile(f)
        return self

    def put(self, f:io.BytesIO):

        f.write(self.xmld.to_xml().encode())
        f.write(f'<Relationships xmlns="{self.xmlns}">'.encode())
        for id,rel in self.dictt.items():

            f.write(rel.to_xml(id).encode())

        f.write(f'</Relationships>'.encode())
