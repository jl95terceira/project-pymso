import dataclasses
import io
from   xml.parsers import expat

from ..      import xml
from .._util import *

class Definition:

    PROPS_NAME = 'Properties'
    class PROPS_ATTR_NAMES:

        _E :Enum[str] = Enum()
        @classmethod
        def values(clas): return clas._E.values()
        XMLNS        = _E('xmlns')
        XMLNS_V_TYPE = _E('xmlns:vt')

# Parsing

class _PropertiesXmlParsingState : 
    
    def __init__(self):

        self.in_properties = False

class PropertiesXmlError             (Exception)         : pass
class NotAPropertiesElementError     (PropertiesXmlError): pass
class PropertiesElementAttributeError(PropertiesXmlError): pass
class PropertyElementAttributeError  (PropertiesXmlError): pass

# Objects

@dataclasses.dataclass
class Properties:

    xmld   :xml.Declaration = dataclasses.field(default_factory=lambda: xml.Declaration())
    xns    :str             = dataclasses.field(default        ="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties")
    v_type :str             = dataclasses.field(default        ="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes")
    items  :dict[str,str]   = dataclasses.field(default_factory=lambda: {})

    @staticmethod
    def get(f:io.BytesIO):

        """
        Load content types from an XML file
        """

        self = Properties()
        xp   = expat.ParserCreate()
        st   = _PropertiesXmlParsingState()
        curp = Pointer('')
        # handle XML declaration
        def XML_DECL_CB(xmld:xml.Declaration):

            self.xmld = xmld

        xp.XmlDeclHandler = xml.Declaration.expat_handler(XML_DECL_CB)
        # handle elements
        def START_ELEM_HANDLER(name :str, attrs:dict[str,str]):

            if not st.in_properties:

                if name !=      Definition.PROPS_NAME:                                raise NotAPropertiesElementError     (f'found at root an element other than {Definition.PROPS_NAME}: {name}')
                if not all(a in Definition.PROPS_ATTR_NAMES.values() for a in attrs): raise PropertiesElementAttributeError(f'got invalid attributes for {Definition.PROPS_NAME} element: {', '.join(map(repr, filter(lambda a: a not in Definition.PROPS_ATTR_NAMES.values(), attrs)))}')
                
                self.xns    = attrs[Definition.PROPS_ATTR_NAMES.XMLNS]
                self.v_type = attrs[Definition.PROPS_ATTR_NAMES.XMLNS_V_TYPE]
                st.in_properties = True
            
            else:

                if attrs: raise PropertyElementAttributeError(f'property element must have NO attributes - got {', '.join(map(repr,attrs))}')
                curp.x = name

        xp.StartElementHandler = START_ELEM_HANDLER
        xp.EndElementHandler   = lambda name: None
        def DEFAULT_HANDLER(data: str):

            if curp.x:

                self.items[curp.x] = data

        xp.DefaultHandler = DEFAULT_HANDLER
        # do it
        xp.ParseFile(f)
        return self

    def put(self, f:io.BytesIO):

        """
        Save these content types to an XML file
        """

        f.write(self.xmld.to_xml().encode())
        f.write(b'\n')
        f.write(as_xml_elem(name =Definition.PROPS_NAME, 
                            attrs={Definition.PROPS_ATTR_NAMES.XMLNS :self.xns,
                                   Definition.PROPS_ATTR_NAMES.XMLNS_V_TYPE:self.v_type}, 
                            inner=''.join(as_xml_elem(name=p, inner=v, force_explicit_end=True) for p,v in self.items.items())).encode())
        