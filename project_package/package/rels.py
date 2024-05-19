import dataclasses
import enum
import io
import typing
from   xml.parsers import expat

from .      import xml
from ._util import *

class Definition:
    
    """
    Definition / Constants
    """

    RELS_NAME = 'Relationships'
    class RELS_ATTR_NAMES:

        _E :Enum[str] = Enum()
        @classmethod
        def values(clas): return clas._E.values()
        XMLNS = _E('xmlns')

    REL_NAME  = 'Relationship'
    class REL_ATTR_NAMES:

        _E :Enum[str] = Enum()
        @classmethod
        def values(clas): return clas._E.values()
        ID     = _E('Id')
        TYPE   = _E('Type')
        TARGET = _E('Target')

# Parsing

class _RelationshipsXmlParsingState:

    def __init__(self):

        self.in_relationships = False

class RelationshipsXmlError             (Exception)            : pass
class NotARelationshipsElementError     (RelationshipsXmlError): pass
class RelationshipsElementAttributeError(RelationshipsXmlError): pass
class NotARelationshipElementError      (RelationshipsXmlError): pass
class RelationshipElementAttributeError (RelationshipsXmlError): pass

# Objects

@dataclasses.dataclass
class Relationship:

    """
    Define a relationship between entities in the document
    """
    # TODO: confirm the above and add detail

    type  :str
    target:str

    def to_xml(self, id:str):

        return as_xml_elem(name =Definition.REL_NAME,
                           attrs={Definition.REL_ATTR_NAMES.ID    : id,
                                  Definition.REL_ATTR_NAMES.TYPE  : self.type,
                                  Definition.REL_ATTR_NAMES.TARGET: self.target})

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
        st   = _RelationshipsXmlParsingState()
        # handle XML declaration
        def XML_DECL_CB(xmld:xml.Declaration):

            self.xmld = xmld

        xp.XmlDeclHandler = xml.Declaration.expat_handler(XML_DECL_CB)
        # handle elements
        def START_ELEM_HANDLER(name :str, attrs:dict[str,str]):

            if not st.in_relationships:

                if name !=      Definition.RELS_NAME:                                raise NotARelationshipsElementError     (f'found at root an element other than {Definition.RELS_NAME}: {name}')
                if not all(a in Definition.RELS_ATTR_NAMES.values() for a in attrs): raise RelationshipsElementAttributeError(f'got unexpected attributes of relationship element: {', '.join(map(repr, filter(lambda a: a not in Definition.RELS_ATTR_NAMES.values(), attrs)))}')

                self.xns = attrs[Definition.RELS_ATTR_NAMES.XMLNS]
                st.in_relationships = True
            
            else:

                if name !=      Definition.REL_NAME:                                raise NotARelationshipElementError     (f'found in {Definition.RELS_NAME} an element that is not a {Definition.REL_NAME}: {name}')
                if not all(a in Definition.REL_ATTR_NAMES.values() for a in attrs): raise RelationshipElementAttributeError(f'got unexpected attributes of relationship element: {', '.join(map(repr, filter(lambda a: a not in Definition.REL_ATTR_NAMES.values(), attrs)))}')

                rel    = Relationship(type  =attrs[Definition.REL_ATTR_NAMES.TYPE  ],
                                      target=attrs[Definition.REL_ATTR_NAMES.TARGET])
                self.rel_by_id_dict[attrs[Definition.REL_ATTR_NAMES.ID]] \
                       = rel

        xp.StartElementHandler = START_ELEM_HANDLER
        # do it
        xp.ParseFile(f)
        return self

    def put(self, f:io.BytesIO):

        """
        Save these relationships to an XML file
        """

        f.write(self.xmld.to_xml().encode())
        f.write(b'\n')
        f.write(as_xml_elem(name =Definition.RELS_NAME, 
                            attrs={Definition.RELS_ATTR_NAMES.XMLNS:self.xns}, 
                            inner=''.join(rel.to_xml(id) for id,rel in self.rel_by_id_dict.items())).encode())
