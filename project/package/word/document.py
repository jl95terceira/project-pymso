import dataclasses
import io
import typing
from   xml.parsers import expat

from ..      import xml
from .._util import *
import re

class Definition:

    class Names:

        DOCUMENT     = 'w:document'
        BODY         = 'w:body'
        PARAGRAPH    = 'w:p'
        TABLE        = 'w:tbl'
        SECTION_PR   = 'w:sectPr'
        PARAGRAPH_PR = 'w:pPr'
        RUN          = 'w:r'
        PROOF_ERROR  = 'w:proofErr'

    class AttrNames:

        class DOCUMENT:

            _E :Enum[str] = Enum()
            @classmethod
            def values(clas): return clas._E.values()
            IGNORABLE = _E('mc:Ignorable')

        class PARAGRAPH:

            _E :Enum[str] = Enum()
            @classmethod
            def values(clas): return clas._E.values()
            PARA_ID         = _E('w14:paraId')
            TEXT_ID         = _E('w14:textId')
            RSID_R          = _E('w:rsidR')
            RSID_R_DEFAULT  = _E('w:rsidRDefault')
            RSID_P          = _E('w:rsidP')
            RSID_R_PR       = _E('w:rsidRPr')

# TODO: a lot of work
# Document is loaded mostly still as an element tree, as suggested by some classes still inheriting from GenericParent, GenericElement. 
# The goal is for the data to be contained in instances only of specialized classes. 

# Parsing

class DocumentXmlError              (Exception)       : pass
class NotADocumentElementError      (DocumentXmlError): pass
class DocumentElementAttributeError (DocumentXmlError): pass
class BodyElementAttributeError     (DocumentXmlError): pass
class ParagraphElementAttributeError(DocumentXmlError): pass
class DocumentXmlSchemaError        (DocumentXmlError): pass
    
class _DocumentXmlParsingState : 
    
    def __init__(self,root_element:typing.Any):

        self.in_document:bool     = False
        self.stack                = [root_element]
        self.unstacked:typing.Any = None
        self.start_elem_handling_dict:dict[str,typing.Callable[[dict[str,str]],None]] = {

            Definition.Names.BODY           :self._handle_body,
            Definition.Names.PARAGRAPH      :self._handle_para,
            Definition.Names.TABLE          :self._handle_table,
            Definition.Names.SECTION_PR     :self._handle_section_pr,
            Definition.Names.PARAGRAPH_PR   :self._handle_paragraph_pr,
            Definition.Names.RUN            :self._handle_run,
            Definition.Names.PROOF_ERROR    :self._handle_proof_err,
        }

    def _cur_name(self): return type(self.stack[-1]).__name__

    def _handle_body        (self, attrs:dict[str,str]):

        if attrs: raise BodyElementAttributeError(f'got attributes of body element but expected none: {', '.join(map(repr, attrs))}')
        body = Body()
        cur = self.stack[-1]
        if   isinstance(cur, Document): cur.body = body
        else:                           raise DocumentXmlSchemaError(f'{Definition.Names.BODY} element unexpected as child of {self._cur_name()} element')
        self.stack.append(body)

    def _handle_para        (self, attrs:dict[str,str]):

        if not all(a in Definition.AttrNames.PARAGRAPH.values() for a in attrs): raise ParagraphElementAttributeError(f'got unexpected attributes of paragraph element: {', '.join(map(repr, filter(lambda a: a not in Definition.AttrNames.PARAGRAPH.values(), attrs)))}')
        para = ParagraphData(id             =attrs    [Definition.AttrNames.PARAGRAPH.PARA_ID],
                         text_id        =attrs    [Definition.AttrNames.PARAGRAPH.TEXT_ID],
                         rsid_r         =attrs    [Definition.AttrNames.PARAGRAPH.RSID_R],
                         rsid_r_default =attrs    [Definition.AttrNames.PARAGRAPH.RSID_R_DEFAULT],
                         rsid_p         =attrs.get(Definition.AttrNames.PARAGRAPH.RSID_P),
                         rsid_r_pr      =attrs.get(Definition.AttrNames.PARAGRAPH.RSID_R_PR))
        cur = self.stack[-1]
        if   isinstance(cur, Body):          cur.elements.append(para)
        elif isinstance(cur, GenericParent): cur.children.append(para)
        else:                                raise DocumentXmlSchemaError(f'{Definition.Names.PARAGRAPH} element unexpected as child of {self._cur_name()} element')
        self.stack.append(para)

    def _handle_table       (self, attrs:dict[str,str]):

        # TODO: update when Table no longer is generic element
        table = Table(name=Definition.Names.TABLE, attrs=attrs)
        cur = self.stack[-1]
        if   isinstance(cur, Body):          cur.elements.append(table)
        elif isinstance(cur, GenericParent): cur.children.append(table)
        else:                                raise DocumentXmlSchemaError(f'{Definition.Names.TABLE} element unexpected as child of {self._cur_name()} element')
        self.stack.append(table)

    def _handle_section_pr  (self, attrs:dict[str,str]):

        # TODO: update when SectionProperties no longer is generic element
        section_pr = SectionProperties(name=Definition.Names.SECTION_PR, attrs=attrs)
        cur = self.stack[-1]
        if   isinstance(cur, Body):          cur.elements.append(section_pr)
        elif isinstance(cur, ParagraphData):     cur.elements.append(section_pr)
        elif isinstance(cur, GenericParent): cur.children.append(section_pr)
        else:                                raise DocumentXmlSchemaError(f'{Definition.Names.SECTION_PR} element unexpected as child of {self._cur_name()} element')
        self.stack.append(section_pr)

    def _handle_paragraph_pr(self, attrs:dict[str,str]):

        # TODO: update when SectionProperties no longer is generic element
        paragraph_pr = ParagraphProperties(name=Definition.Names.PARAGRAPH_PR, attrs=attrs)
        cur = self.stack[-1]
        if   isinstance(cur, ParagraphData):     cur.properties = paragraph_pr
        elif isinstance(cur, GenericParent): cur.children.append(paragraph_pr)
        else:                                raise DocumentXmlSchemaError(f'{Definition.Names.PARAGRAPH_PR} element unexpected as child of {self._cur_name()} element')
        self.stack.append(paragraph_pr)

    def _handle_run         (self, attrs:dict[str,str]):

        # TODO: update when SectionProperties no longer is generic element
        run = RunData(name=Definition.Names.RUN, attrs=attrs)
        cur = self.stack[-1]
        if   isinstance(cur, ParagraphData):     cur.elements.append(run)
        elif isinstance(cur, GenericParent): cur.children.append(run)
        else:                                raise DocumentXmlSchemaError(f'{Definition.Names.RUN} element unexpected as child of {self._cur_name()} element')
        self.stack.append(run)

    def _handle_proof_err   (self, attrs:dict[str,str]):

        # TODO: update when SectionProperties no longer is generic element
        proof_err = ProofErr(name=Definition.Names.PROOF_ERROR, attrs=attrs)
        cur = self.stack[-1]
        if   isinstance(cur, ParagraphData):     cur.elements.append(proof_err)
        elif isinstance(cur, GenericParent): cur.children.append(proof_err)
        else:                                raise DocumentXmlSchemaError(f'{Definition.Names.PROOF_ERROR} element unexpected as child of {self._cur_name()} element')
        self.stack.append(proof_err)

# Data Objects

@dataclasses.dataclass
class ParagraphProperties(GenericElement): pass # TODO: remove inheritance from generic type

@dataclasses.dataclass
class RunData(GenericElement): pass # TODO: remove inheritance from generic type

@dataclasses.dataclass
class ProofErr(GenericElement): pass # TODO: remove inheritance from generic type

@dataclasses.dataclass
class ParagraphData:    

    id            :str
    text_id       :str
    rsid_r        :str
    rsid_r_default:str
    rsid_p        :str
    rsid_r_pr     :str
    properties    :ParagraphProperties = dataclasses.field(default        =None)
    elements      :list[ToXmlAble]     = dataclasses.field(default_factory=lambda: [])

    @typing.override
    def to_xml(self):

        return as_xml_elem(name =Definition.Names.PARAGRAPH,
                           attrs={a:v for a,v in ((Definition.AttrNames.PARAGRAPH.PARA_ID        ,self.id),
                                                  (Definition.AttrNames.PARAGRAPH.TEXT_ID        ,self.text_id),
                                                  (Definition.AttrNames.PARAGRAPH.RSID_R         ,self.rsid_r),
                                                  (Definition.AttrNames.PARAGRAPH.RSID_R_DEFAULT ,self.rsid_r_default),
                                                  (Definition.AttrNames.PARAGRAPH.RSID_P         ,self.rsid_p),
                                                  (Definition.AttrNames.PARAGRAPH.RSID_R_PR      ,self.rsid_r_pr)) if v is not None},
                           inner=''.join((self.properties.to_xml(), 
                                          ''.join(map(to_xml, self.elements)),)))

@dataclasses.dataclass
class Table(GenericElement): pass # TODO: remove inheritance from generic type

@dataclasses.dataclass
class SectionProperties(GenericElement): pass # TODO: remove inheritance from generic type

@dataclasses.dataclass
class Body:

    elements:list[ToXmlAble] = dataclasses.field(default_factory=lambda: [])

    def to_xml(self):

        return as_xml_elem(name =Definition.Names.BODY,
                           inner=''.join(map(to_xml, self.elements)))

@dataclasses.dataclass
class Document:

    xmld     :xml.Declaration = dataclasses.field(default_factory=lambda: xml.Declaration())
    ns_dict  :dict[str,str]   = dataclasses.field(default_factory=lambda: {})
    ignorable:list[str]       = dataclasses.field(default_factory=lambda: [])
    body     :Body            = dataclasses.field(default_factory=lambda: Body())

    @staticmethod
    def get(f:io.BytesIO):

        self  = Document()
        xp    = expat.ParserCreate()
        st    = _DocumentXmlParsingState(root_element=self)
        # handle XML declaration
        def XML_DECL_CB(xmld:xml.Declaration):

            self.xmld = xmld

        xp.XmlDeclHandler = xml.Declaration.expat_handler(XML_DECL_CB)
        # handle elements
        def START_ELEM_HANDLER(name :str, attrs:dict[str,str]):

            if not st.in_document:

                if name != Definition.Names.DOCUMENT: raise NotADocumentElementError(f'found at root an element other than {Definition.Names.DOCUMENT}: {name}')
                # TOMAYBEDO: check if all found attributes are in predefined set of expected attributes (there's a lot!)
                self.ignorable.extend(attrs[Definition.AttrNames.DOCUMENT.IGNORABLE].split(' '))
                for a,v in attrs.items():

                    if a.startswith('xmlns:'):

                        self.ns_dict[a[len('xmlns:'):]] = v
                
                st.in_document = True
            
            else:

                if name in st.start_elem_handling_dict:

                    st.start_elem_handling_dict[name](attrs)
                
                else:

                    e = GenericElement(name=name, attrs=attrs)
                    cur = st.stack[-1]
                    if isinstance(cur, GenericParent): 
                        
                        cur.children.append(e)
                        st.stack    .append(e)

                    else:

                        raise NotImplementedError(f'cannot append generic element {name} ({attrs}) to children of non-parent {type(cur).__name__}')

        xp.StartElementHandler = START_ELEM_HANDLER
        def END_ELEM_HANDLER(name: str):

            st.unstacked = st.stack.pop()

        xp.EndElementHandler   = END_ELEM_HANDLER
        def DEFAULT_HANDLER(data: str):

            if not st.in_document: return
            cur = st.stack[-1]
            if isinstance(cur, GenericElement): 

                cur.children.append(GenericData(data))    
                
            else: raise NotImplementedError(f'cannot append generic data {data} to children of non-parent {type(cur).__name__}')
            
        xp.DefaultHandler = DEFAULT_HANDLER
        # do it
        xp.ParseFile(f)
        return self
    
    def put(self, f:io.BytesIO):

        f.write(self.xmld.to_xml().encode())
        f.write(b'\n')
        f.write(as_xml_elem(name =Definition.Names.DOCUMENT, 
                            attrs={**{f'xmlns:{nst}':ns for nst,ns in self.ns_dict.items()},
                                   Definition.AttrNames.DOCUMENT.IGNORABLE:' '.join(self.ignorable)}, 
                            inner=self.body.to_xml()).encode())

# API

class Run:

    def __init__(self, data:RunData):

        self._data = data

    def text(self):

        for x in ifinstance(GenericElement, self._data.children):

            if x.name == 'w:t': 

                t = x.children[0]
                if isinstance(t, GenericData):

                    return t.data
        
        raise NotImplementedError()
    
class Paragraph:

    def __init__(self, data:ParagraphData):

        self._data = data
    
    def runs(self): 

        yield from map(Run, ifinstance(RunData, self._data.elements))

    def text(self):

        return ''.join(run.text() for run in self.runs())
    
    
    
