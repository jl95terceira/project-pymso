import dataclasses
import io
from   xml.parsers import expat

from ..      import xml
from .._util import *

# XML

@dataclasses.dataclass
class PropertiesElementDefinition:

    """
    Define the types XML element
    """

    name = 'Properties'

class PropertiesElementAttributeNames:

    """
    Enumerate the names of all of the attributes of the properties XML element
    """

    _e :Enum[str] = Enum()
    @classmethod
    def values(clas): yield from clas._e

    # enum BEGIN
    XMLNS  = _e('xmlns')
    V_TYPE = _e('xmlns:vt')
    # enum END

# XML parsing

class _PropertiesXmlParsingState : pass
class _PropertiesXmlParsingStates:

    INIT          = _PropertiesXmlParsingState()
    IN_PROPERTIES = _PropertiesXmlParsingState()

class PropertiesXmlError             (Exception)         : pass
class NotAPropertiesElementError     (PropertiesXmlError): pass
class PropertiesElementAttributeError(PropertiesXmlError): pass
class PropertyElementAttributeError  (PropertiesXmlError): pass

# Objects

@dataclasses.dataclass
class Properties:

    xmld   :xml.Declaration = dataclasses.field(default_factory=lambda: xml.Declaration())
    xns    :str             = dataclasses.field(default        ="http://schemas.openxmlformats.org/package/2006/content-types")
    v_type :str             = dataclasses.field(default        ="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes")
    items  :dict[str,str]   = dataclasses.field(default_factory=lambda: {})

    @staticmethod
    def get(f:io.BytesIO):

        """
        Load content types from an XML file
        """

        self = Properties()
        xp   = expat.ParserCreate()
        st   = Pointer(_PropertiesXmlParsingStates.INIT)
        curp = ''
        # handle XML declaration
        def XML_DECL_CB(xmld:xml.Declaration):

            self.xmld = xmld

        xp.XmlDeclHandler = xml.Declaration.expat_handler(XML_DECL_CB)
        # handle elements
        def START_ELEM_HANDLER(name :str, attrs:dict[str,str]):

            if st.x is _PropertiesXmlParsingStates.INIT:

                if name != PropertiesElementDefinition.name: 
                    
                    raise NotAPropertiesElementError(f'found at root an element other than Properties: {name}')
                
                self.xns    = attrs[PropertiesElementAttributeNames.XMLNS]
                self.v_type = attrs[PropertiesElementAttributeNames.V_TYPE]
                st.x        = _PropertiesXmlParsingStates.IN_PROPERTIES
            
            elif st.x is _PropertiesXmlParsingStates.IN_PROPERTIES:

                if attrs: raise PropertyElementAttributeError(f'property element must have NO attributes - got {', '.join(map(repr,attrs))}')
                curp = name

        xp.StartElementHandler = START_ELEM_HANDLER
        xp.EndElementHandler   = lambda name: None
        def DEFAULT_HANDLER(data: str):

            if curp:

                self.items[curp] = data

        xp.DefaultHandler = DEFAULT_HANDLER
        # do it
        xp.ParseFile(f)
        return self

    def put(self, f:io.BytesIO):

        """
        Save these content types to an XML file
        """

        f.write(self.xmld.to_xml().encode())
        f.write(as_xml_elem(name =PropertiesElementDefinition.name, 
                            attrs={PropertiesElementAttributeNames.XMLNS :self.xns,
                                   PropertiesElementAttributeNames.V_TYPE:self.v_type}, 
                            inner=''.join(as_xml_elem(name=p, inner=v, force_explicit_end=True) for p,v in self.items.items())).encode())
        