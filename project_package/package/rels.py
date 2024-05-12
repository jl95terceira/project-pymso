import dataclasses
import enum
import io
import typing
from   xml.parsers import expat

from .      import xml
from ._util import *

# XML

class RelationshipElementDefinition:
    
    """
    Define the "Relationship" XML element
    """

    name = 'Relationship'

class RelationshipElementAttributeNames:

    """
    Enumerate the names of all of the attributes of the "Relationship" XML element
    """

    _e :Enum[str] = Enum()
    @classmethod
    def values(clas): yield from clas._e

    # enum BEGIN
    ID     = _e('Id')
    TYPE   = _e('Type')
    TARGET = _e('Target')
    # enum END
    
    _set = set(r for r in _e)
    @classmethod
    def set(clas): return clas._set

@dataclasses.dataclass
class RelationshipsElementDefinition:

    """
    Define the "Relationships" (plural) XML element
    """

    name = 'Relationships'

# XML parsing

class _RelationshipsXmlParsingState : pass
class _RelationshipsXmlParsingStates:

    INIT             = _RelationshipsXmlParsingState()
    IN_RELATIONSHIPS = _RelationshipsXmlParsingState()

class RelationshipsXmlError            (Exception)            : pass
class NotARelationshipsElementError    (RelationshipsXmlError): pass
class NotARelationshipElementError     (RelationshipsXmlError): pass
class RelationshipElementAttributeError(RelationshipsXmlError): pass

# Objects

@dataclasses.dataclass
class Relationship(ElementLike):

    """
    Define a relationship between entities in the document
    """
    # TODO: confirm the above and add detail

    type  :str = dataclasses.field(default=MISSING)
    target:str = dataclasses.field(default=MISSING)

    def to_xml(self, id:str):

        return as_xml_elem(name =RelationshipElementDefinition.name,
                           attrs={RelationshipElementAttributeNames.ID    : id,
                                  RelationshipElementAttributeNames.TYPE  : self.type,
                                  RelationshipElementAttributeNames.TARGET: self.target},
                           tail =''.join(self.tail))

@dataclasses.dataclass
class Relationships:

    """
    Map all of the relationships between entities in the document
    """

    xmld          :xml.Declaration        = dataclasses.field(default_factory=lambda: xml.Declaration())
    xns           :str                    = dataclasses.field(default        ="http://schemas.openxmlformats.org/package/2006/relationships")
    rel_by_id_dict:dict[str,Relationship] = dataclasses.field(default_factory=lambda: {})

    @staticmethod
    def get(f:io.BytesIO):

        """
        Load relationships from an XML file
        """

        self = Relationships()
        xp   = expat.ParserCreate()
        st   = Pointer(_RelationshipsXmlParsingStates.INIT)
        curp = Pointer[ElementLike]()
        # handle XML declaration
        def XML_DECL_CB(xmld:xml.Declaration):

            self.xmld = xmld
            curp.x    = xmld

        xp.XmlDeclHandler = xml.Declaration.expat_handler(XML_DECL_CB)
        # handle elements
        def START_ELEM_HANDLER(name :str, attrs:dict[str,str]):

            if st.x is _RelationshipsXmlParsingStates.INIT:

                if name != RelationshipsElementDefinition.name: 
                    
                    raise NotARelationshipsElementError('found at root an element other than Relationships')
                
                self.xns = attrs['xmlns']
                st.x     = _RelationshipsXmlParsingStates.IN_RELATIONSHIPS
            
            elif st.x is _RelationshipsXmlParsingStates.IN_RELATIONSHIPS:

                if name != RelationshipElementDefinition.name: 
                    
                    raise NotARelationshipElementError('found in Relationships an element that is not a Relationship')
                
                if not all(a in RelationshipElementAttributeNames.set() for a in attrs):
                    
                    raise RelationshipElementAttributeError(f'got unexpected attributes of relationship element: {', '.join(map(repr, filter(lambda a: a not in RelationshipElementAttributeNames.set(), attrs)))}')

                rel    = Relationship(type  =attrs[RelationshipElementAttributeNames.TYPE  ],
                                      target=attrs[RelationshipElementAttributeNames.TARGET])
                self.rel_by_id_dict[attrs[RelationshipElementAttributeNames.ID]] \
                       = rel
                curp.x = rel

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

        """
        Save these relationships to an XML file
        """

        f.write(self.xmld.to_xml().encode())
        f.write(as_xml_elem(name ='Relationships', 
                            attrs={'xmlns':self.xns}, 
                            inner=''.join(rel.to_xml(id) for id,rel in self.rel_by_id_dict.items())).encode())
