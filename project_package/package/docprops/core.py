import dataclasses
import io
import typing
from   xml.parsers import expat

from ..      import xml
from .._util import *
import re

class Definition:

    CPROPS_NAME = 'cp:coreProperties'
    class CPROPS_NS_TYPES:

        _E :Enum[str] = Enum()
        @classmethod
        def values(clas): return clas._E.values()
        CORE_PROPS  = _E('cp')
        DC_ELEMENTS = _E('dc')
        DC_TERMS    = _E('dcterms')
        DCMI_TYPE   = _E('dcmitype')
        XML_SCHEMA  = _E('xsi')
    
    class CPROPS_ATTR_NAMES:

        _E :Enum[str] = Enum()
        @classmethod
        def values(clas): return clas._E.values()
        # It seems that there are only namespace-related attributes.

    class DCTERMS_ATTR_NAMES:

        _E :Enum[str] = Enum()
        @classmethod
        def values(clas): return clas._E.values()
        XSI_TYPE = _E('xsi:type')

for namespace_type in Definition.CPROPS_NS_TYPES.values(): Definition.CPROPS_ATTR_NAMES._E(f'xmlns:{namespace_type}')

# Parsing

class _CorePropertiesXmlParsingState : pass
class _CorePropertiesXmlParsingStates:

    INIT               = _CorePropertiesXmlParsingState()
    IN_CORE_PROPERTIES = _CorePropertiesXmlParsingState()

class CorePropertiesXmlError             (Exception)             : pass
class NotACorePropertiesElementError     (CorePropertiesXmlError): pass
class CorePropertiesElementAttributeError(CorePropertiesXmlError): pass
class CorePropertyElementNameError       (CorePropertiesXmlError): pass
class CpAttributeError                   (CorePropertiesXmlError): pass
class DcAttributeError                   (CorePropertiesXmlError): pass
class DcTermsAttributeError              (CorePropertiesXmlError): pass

# Objects

@dataclasses.dataclass
class DcTerms:

    type :str = dataclasses.field(default=MISSING)
    value:str = dataclasses.field(default=MISSING)

_CORE_PROPERTY_NAMESPACE_AND_NAME_RE  = re.compile('^(.*?):(.*)$')
def _CORE_PROPERTY_NAMESPACE_AND_NAME(a:str):

    m = _CORE_PROPERTY_NAMESPACE_AND_NAME_RE.match(a)
    if not m:

        raise CorePropertyElementNameError(f"core property element name not compliant with expression {repr(_CORE_PROPERTY_NAMESPACE_AND_NAME_RE.pattern)}: {a}")
    
    return m.group(1),m.group(2)

@dataclasses.dataclass
class CoreProperties:

    xmld         :xml.Declaration   = dataclasses.field(default_factory=lambda: xml.Declaration())
    xns_by_type_dict:dict[str,str]  = dataclasses.field(default_factory=lambda: {Definition.CPROPS_NS_TYPES.CORE_PROPS :"http://schemas.openxmlformats.org/package/2006/metadata/core-properties",
                                                                                 Definition.CPROPS_NS_TYPES.DC_ELEMENTS:"http://purl.org/dc/elements/1.1/",
                                                                                 Definition.CPROPS_NS_TYPES.DC_TERMS   :"http://purl.org/dc/terms/",
                                                                                 Definition.CPROPS_NS_TYPES.DCMI_TYPE  :"http://purl.org/dc/dcmitype/",
                                                                                 Definition.CPROPS_NS_TYPES.XML_SCHEMA :"http://www.w3.org/2001/XMLSchema-instance"})
    items_cp     :dict[str,str]     = dataclasses.field(default_factory=lambda: {})
    items_dc     :dict[str,str]     = dataclasses.field(default_factory=lambda: {})
    items_dcterms:dict[str,DcTerms] = dataclasses.field(default_factory=lambda: {})

    def __post_init__(self):

        def _put_cp     (name:str,attrs:dict[str,str],value:str): 
            
            if attrs: raise CpAttributeError(f"{Definition.CPROPS_NS_TYPES.CORE_PROPS} property element ({name}) must have NO attributes - got: {repr(tuple(attrs))}")
            self.items_cp[name] = value

        def _put_dc     (name:str,attrs:dict[str,str],value:str): 
            
            if attrs: raise DcAttributeError(f"{Definition.CPROPS_NS_TYPES.DC_ELEMENTS} property element ({name}) must have NO attributes - got: {repr(tuple(attrs))}")
            self.items_dc[name] = value

        def _put_dcterms(name:str,attrs:dict[str,str],value:str): 
            
            invalid = list(filter(lambda a: a not in Definition.DCTERMS_ATTR_NAMES.values(), attrs))
            if invalid: raise DcTermsAttributeError(f'got invalid attributes for {Definition.CPROPS_NS_TYPES.DC_TERMS} property element ({name}): {', '.join(map(repr,invalid))}')
            self.items_dcterms[name] = DcTerms(type=attrs[Definition.DCTERMS_ATTR_NAMES.XSI_TYPE], value=value)

        self._core_prop_value_cb_dict:dict[str,typing.Callable[[str,dict[str,str],str],None]] = {
            
            Definition.CPROPS_NS_TYPES.CORE_PROPS : _put_cp,
            Definition.CPROPS_NS_TYPES.DC_ELEMENTS: _put_dc,
            Definition.CPROPS_NS_TYPES.DC_TERMS   : _put_dcterms,

        }

    def _core_prop_value_cb_default(ns:str):

        raise NotImplementedError(f'processing not implemented for core property in namespace of type {ns}')

    @staticmethod
    def get(f:io.BytesIO):

        """
        Load content types from an XML file
        """

        self = CoreProperties()
        xp   = expat.ParserCreate()
        st   = Pointer(_CorePropertiesXmlParsingStates.INIT)
        curp     = Pointer('')
        curpns   = Pointer('')
        curattrs = Pointer[dict[str,str]]({})
        # handle XML declaration
        def XML_DECL_CB(xmld:xml.Declaration):

            self.xmld = xmld

        xp.XmlDeclHandler = xml.Declaration.expat_handler(XML_DECL_CB)
        # handle elements
        def START_ELEM_HANDLER(name :str, attrs:dict[str,str]):

            if st.x is _CorePropertiesXmlParsingStates.INIT:

                if name !=      Definition.CPROPS_NAME:                                raise NotACorePropertiesElementError     (f'found at root an element other than {Definition.CPROPS_NAME}: {name}')
                if not all(a in Definition.CPROPS_ATTR_NAMES.values() for a in attrs): raise CorePropertiesElementAttributeError(f'got unexpected attributes of {Definition.CPROPS_NAME} element: {', '.join(map(repr, filter(lambda a: a not in Definition.CPROPS_ATTR_NAMES.values(), attrs)))}')

                for namespace_type in Definition.CPROPS_NS_TYPES.values():

                    a = f'xmlns:{namespace_type}'
                    if a in attrs:

                        self.xns_by_type_dict[namespace_type] = attrs[a]

                st.x = _CorePropertiesXmlParsingStates.IN_CORE_PROPERTIES
            
            elif st.x is _CorePropertiesXmlParsingStates.IN_CORE_PROPERTIES:

                curpns.x,curp.x = _CORE_PROPERTY_NAMESPACE_AND_NAME(name)
                curattrs.x      = attrs

        xp.StartElementHandler = START_ELEM_HANDLER
        xp.EndElementHandler   = lambda name: None
        def DEFAULT_HANDLER(data: str):

            if curp.x:

                self._core_prop_value_cb_dict.get(curpns.x, lambda name,attrs,value: self._core_prop_value_cb_default(curpns.x))(curp.x,curattrs.x,data)

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
        f.write(as_xml_elem(name =Definition.CPROPS_NAME, 
                            attrs={f'xmlns:{nst}':ns for nst,ns in self.xns_by_type_dict.items()}, 
                            inner=''.join((
                                
                                ''.join(as_xml_elem(name=f'{Definition.CPROPS_NS_TYPES.CORE_PROPS }:{p}', inner=v,                                                             force_explicit_end=True) for p,v in self.items_cp     .items()),
                                ''.join(as_xml_elem(name=f'{Definition.CPROPS_NS_TYPES.DC_ELEMENTS}:{p}', inner=v,                                                             force_explicit_end=True) for p,v in self.items_dc     .items()),
                                ''.join(as_xml_elem(name=f'{Definition.CPROPS_NS_TYPES.DC_TERMS   }:{p}', inner=v.value, attrs={Definition.DCTERMS_ATTR_NAMES.XSI_TYPE:v.type}, force_explicit_end=True) for p,v in self.items_dcterms.items()),
                                
                            ))).encode())
        