import dataclasses
import io
from   xml.parsers import expat

from .      import xml
from ._util import *

# XML

class DefaultElementDefinition:
    
    """
    Define the default XML element
    """

    name = 'Default'

class DefaultElementAttributeNames:

    """
    Enumerate the names of all of the attributes of the default XML element
    """

    _e :Enum[str] = Enum()
    @classmethod
    def values(clas): yield from clas._e

    # enum BEGIN
    EXTENSION    = _e('Extension')
    CONTENT_TYPE = _e('ContentType')
    # enum END
    
    _set = set(r for r in _e)
    @classmethod
    def set(clas): return clas._set

class OverrideElementDefinition:
    
    """
    Define the override XML element
    """

    name = 'Override'

class OverrideElementAttributeNames:

    """
    Enumerate the names of all of the attributes of the override XML element
    """

    _e :Enum[str] = Enum()
    @classmethod
    def values(clas): yield from clas._e

    # enum BEGIN
    PART_NAME    = _e('PartName')
    CONTENT_TYPE = _e('ContentType')
    # enum END
    
    _set = set(r for r in _e)
    @classmethod
    def set(clas): return clas._set

@dataclasses.dataclass
class TypesElementDefinition:

    """
    Define the types XML element
    """

    name = 'Types'

# XML parsing

class _TypesXmlParsingState : pass
class _TypesXmlParsingStates:

    INIT     = _TypesXmlParsingState()
    IN_TYPES = _TypesXmlParsingState()

class TypesXmlError                (Exception)    : pass
class NotATypesElementError        (TypesXmlError): pass
class NotATypeElementError         (TypesXmlError): pass
class DefaultElementAttributeError (TypesXmlError): pass
class OverrideElementAttributeError(TypesXmlError): pass

# Objects

@dataclasses.dataclass
class Default(ElementLike):

    content_type:str = dataclasses.field(default=MISSING)

    def to_xml(self, extension:str):

        return as_xml_elem(name =DefaultElementDefinition.name,
                           attrs={DefaultElementAttributeNames.EXTENSION   : extension,
                                  DefaultElementAttributeNames.CONTENT_TYPE: self.content_type},
                           tail =''.join(self.tail))
        
@dataclasses.dataclass
class Override(ElementLike):

    content_type:str = dataclasses.field(default=MISSING)

    def to_xml(self, part_name:str):

        return as_xml_elem(name =OverrideElementDefinition.name,
                           attrs={OverrideElementAttributeNames.PART_NAME   : part_name,
                                  OverrideElementAttributeNames.CONTENT_TYPE: self.content_type},
                           tail =''.join(self.tail))
    
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
        st   = Pointer(_TypesXmlParsingStates.INIT)
        curp = Pointer[ElementLike]()
        # handle XML declaration
        def XML_DECL_CB(xmld:xml.Declaration):

            self.xmld = xmld
            curp.x    = xmld

        xp.XmlDeclHandler = xml.Declaration.expat_handler(XML_DECL_CB)
        # handle elements
        def START_ELEM_HANDLER(name :str, attrs:dict[str,str]):

            if st.x is _TypesXmlParsingStates.INIT:

                if name != TypesElementDefinition.name: 
                    
                    raise NotATypesElementError('found at root an element other than Types')
                
                self.xns = attrs['xmlns']
                st.x     = _TypesXmlParsingStates.IN_TYPES
            
            elif st.x is _TypesXmlParsingStates.IN_TYPES:

                if name == DefaultElementDefinition.name:

                    if not all(a in DefaultElementAttributeNames.set() for a in attrs):
                        
                        raise DefaultElementAttributeError(f'got unexpected attributes of default element: {', '.join(map(repr, filter(lambda a: a not in DefaultElementAttributeNames.set(), attrs)))}')
                
                    t      = Default(content_type=attrs[DefaultElementAttributeNames.CONTENT_TYPE])
                    self.default_by_extension_dict[attrs[DefaultElementAttributeNames.EXTENSION]] \
                           = t
                    curp.x = t
                    
                elif name == OverrideElementDefinition.name:

                    if not all(a in OverrideElementAttributeNames.set() for a in attrs):
                        
                        raise OverrideElementAttributeError(f'got unexpected attributes of default element: {', '.join(map(repr, filter(lambda a: a not in OverrideElementAttributeNames.set(), attrs)))}')

                    t      = Override(content_type=attrs[OverrideElementAttributeNames.CONTENT_TYPE])
                    self.override_by_part_name_dict[attrs[OverrideElementAttributeNames.PART_NAME]] \
                           = t
                    curp.x = t

                else:

                    raise NotATypeElementError('found in Types an element that is not a Type')

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
        Save these content types to an XML file
        """

        f.write(self.xmld.to_xml().encode())
        f.write(as_xml_elem(name ='Types', 
                            attrs={'xmlns':self.xns}, 
                            inner=''.join((''.join(rel.to_xml(id) for id,rel in self.default_by_extension_dict .items()), 
                                           ''.join(rel.to_xml(id) for id,rel in self.override_by_part_name_dict.items())))).encode())
        