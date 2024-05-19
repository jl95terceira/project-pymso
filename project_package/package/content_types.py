import dataclasses
import io
from   xml.parsers import expat

from .      import xml
from ._util import *

class Definition:
    
    TYPES_NAME = 'Types'
    class TYPES_ATTR_NAME:

        _E :Enum[str] = Enum()
        @classmethod
        def values(clas): return clas._E.values()
        XMLNS = _E('xmlns')

    TDEFAULT_NAME  = 'Default'
    class TDEFAULT_ATTR_NAMES:

        _E :Enum[str] = Enum()
        @classmethod
        def values(clas): return clas._E.values()
        EXTENSION    = _E('Extension')
        CONTENT_TYPE = _E('ContentType')
    
    TOVERRIDE_NAME = "Override"
    class TOVERRIDE_ATTR_NAMES:

        _E :Enum[str] = Enum()
        @classmethod
        def values(clas): return clas._E.values()
        PART_NAME    = _E('PartName')
        CONTENT_TYPE = _E('ContentType')

# Parsing

class _TypesXmlParsingState : 
    
    def __init__(self):

        self.in_types = False

class TypesXmlError                (Exception)    : pass
class NotATypesElementError        (TypesXmlError): pass
class NotATypeElementError         (TypesXmlError): pass
class DefaultElementAttributeError (TypesXmlError): pass
class OverrideElementAttributeError(TypesXmlError): pass

# Objects

@dataclasses.dataclass
class Default:

    content_type:str

    def to_xml(self, extension:str):

        return as_xml_elem(name =Definition.TDEFAULT_NAME,
                           attrs={Definition.TDEFAULT_ATTR_NAMES.EXTENSION   : extension,
                                  Definition.TDEFAULT_ATTR_NAMES.CONTENT_TYPE: self.content_type})
        
@dataclasses.dataclass
class Override:

    content_type:str

    def to_xml(self, part_name:str):

        return as_xml_elem(name =Definition.TOVERRIDE_NAME,
                           attrs={Definition.TOVERRIDE_ATTR_NAMES.PART_NAME   : part_name,
                                  Definition.TOVERRIDE_ATTR_NAMES.CONTENT_TYPE: self.content_type})
    
@dataclasses.dataclass
class Types:

    xmld                      :xml.Declaration    = dataclasses.field(default_factory=lambda: xml.Declaration())
    xns                       :str                = dataclasses.field(default        ="http://schemas.openxmlformats.org/package/2006/content-types")
    default_by_extension_dict :dict[str,Default]  = dataclasses.field(default_factory=lambda: {})
    override_by_part_name_dict:dict[str,Override] = dataclasses.field(default_factory=lambda: {})

    @staticmethod
    def get(f:io.BytesIO):

        """
        Load content types from an XML file
        """

        self = Types()
        xp   = expat.ParserCreate()
        st   = _TypesXmlParsingState()
        # handle XML declaration
        def XML_DECL_CB(xmld:xml.Declaration):

            self.xmld = xmld

        xp.XmlDeclHandler = xml.Declaration.expat_handler(XML_DECL_CB)
        # handle elements
        def START_ELEM_HANDLER(name :str, attrs:dict[str,str]):

            if not st.in_types:

                if name != Definition.TYPES_NAME:  raise NotATypesElementError(f'found at root an element other than {Definition.TYPES_NAME}: {name}')
                
                self.xns    = attrs[Definition.TYPES_ATTR_NAME.XMLNS]
                st.in_types = True
            
            else:

                if name == Definition.TDEFAULT_NAME:

                    if not all(a in Definition.TDEFAULT_ATTR_NAMES.values() for a in attrs): raise DefaultElementAttributeError(f'got unexpected attributes of {Definition.TDEFAULT_NAME} element: {', '.join(map(repr, filter(lambda a: a not in Definition.TDEFAULT_ATTR_NAMES.values(), attrs)))}')
                
                    t      = Default(content_type=attrs[Definition.TDEFAULT_ATTR_NAMES.CONTENT_TYPE])
                    self.default_by_extension_dict[attrs[Definition.TDEFAULT_ATTR_NAMES.EXTENSION]] \
                           = t
                    
                elif name == Definition.TOVERRIDE_NAME:

                    if not all(a in Definition.TOVERRIDE_ATTR_NAMES.values() for a in attrs): raise OverrideElementAttributeError(f'got unexpected attributes of {Definition.TOVERRIDE_NAME} element: {', '.join(map(repr, filter(lambda a: a not in Definition.TOVERRIDE_ATTR_NAMES.values(), attrs)))}')

                    t      = Override(content_type=attrs[Definition.TOVERRIDE_ATTR_NAMES.CONTENT_TYPE])
                    self.override_by_part_name_dict[attrs[Definition.TOVERRIDE_ATTR_NAMES.PART_NAME]] \
                           = t

                else:

                    raise NotATypeElementError(f'found in {Definition.TYPES_NAME} an element that is neither of {repr((Definition.TDEFAULT_NAME, 
                                                                                                                       Definition.TOVERRIDE_NAME))}')

        xp.StartElementHandler = START_ELEM_HANDLER
        # do it
        xp.ParseFile(f)
        return self

    def put(self, f:io.BytesIO):

        """
        Save these content types to an XML file
        """

        f.write(self.xmld.to_xml().encode())
        f.write(b'\n')
        f.write(as_xml_elem(name =Definition.TYPES_NAME, 
                            attrs={Definition.TYPES_ATTR_NAME.XMLNS:self.xns}, 
                            inner=''.join((''.join(t.to_xml(id) for id,t in self.default_by_extension_dict .items()), 
                                           ''.join(t.to_xml(id) for id,t in self.override_by_part_name_dict.items())))).encode())
        