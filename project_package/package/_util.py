import dataclasses
import functools
import io
import sys
import xml.parsers.expat as expat
import zipfile

def internal_files(zf:zipfile.ZipFile|str):

     if isinstance(zf, str):

          with zipfile.ZipFile(zf, mode='r') as zf_:

               yield from internal_files(zf_)

          return

     for fn in sorted(finfo.filename for finfo in zf.filelist):
          
          with zf.open(fn, mode='r') as f:
               
               yield (fn,f,)

@dataclasses.dataclass
class Element():

     name    :str             = ""
     args    :tuple           = tuple()
     children:list['Element'] = dataclasses.field(default_factory=lambda: list())

class ELEMENT_NAMES:
     
     XMLDECL  = 'XMLDECL'
     DOCTYPE  = 'DOCTYPE'
     ELEMENT  = 'ELEMENT'
     ELEMDECL = 'ELEMDECL'
     CDATASEC = 'CDATASEC'
     CDATA    = 'CDATA'
     ___      = '***'

def load_etree(f:io.BytesIO):

    stack:list[Element] = [Element()]
    upstacker             = lambda name: lambda *aa: (stack.append(Element(name=name,args=aa)),stack[-2].children.append(stack[-1]),)
    downstacker           = lambda     : lambda *aa: (stack.pop(),)
    stacker               = lambda name: lambda *aa: (stack[-1].children.append(Element(name=name ,args=aa)),)
    xp = expat.ParserCreate()
    xp.XmlDeclHandler           = stacker    (ELEMENT_NAMES.XMLDECL)
    xp.StartDoctypeDeclHandler  = upstacker  (ELEMENT_NAMES.DOCTYPE)
    xp.EndDoctypeDeclHandler    = downstacker()
    xp.StartElementHandler      = upstacker  (ELEMENT_NAMES.ELEMENT)
    xp.ElementDeclHandler       = stacker    (ELEMENT_NAMES.ELEMDECL)
    xp.EndElementHandler        = downstacker()
    xp.StartCdataSectionHandler = upstacker  (ELEMENT_NAMES.CDATASEC)
    xp.CharacterDataHandler     = stacker    (ELEMENT_NAMES.CDATA)
    xp.EndCdataSectionHandler   = downstacker()
    xp.DefaultHandlerExpand     = stacker    (ELEMENT_NAMES.___)
    xp.ParseFile(f)
    return stack[-1]

def load_etree_map(zf:zipfile.ZipFile|str):

    return {fn:load_etree(f) for fn,f in internal_files(zf)}

_XML_CHAR_ESCAPE_TUPLES = (
    ('&' ,'&amp;'),
    ('"' ,'&quot;'),
    ('\'','&apos;'),
    ('<' ,'&lt;'),
    ('>' ,'&gt;'),
)

def to_xml_string(s:str):
     
     return f'"{functools.reduce(lambda s,c: s.replace(c[0],c[1]), _XML_CHAR_ESCAPE_TUPLES, s)}"'

class _DUMP_ETREE_FUNCTIONS:

    @staticmethod
    def _dump(f:io.BytesIO,et:Element): 
         
         f.write(et.args[0].encode())

    @staticmethod
    def _dump_parent (f:io.BytesIO,et:Element): 
         
         for child in et.children:
              
              dump_etree(f,child)

    @staticmethod
    def _dump_xmldecl(f:io.BytesIO,et:Element): 
         
         f.write(f'<?xml version="{et.args[0]}" encoding="{et.args[1]}" standalone="{ {1:'yes',0:'no'}[et.args[2]] }"?>'.encode())

    @staticmethod
    def _dump_element(f:io.BytesIO,et:Element): 
         
         f.write(f'<{et.args[0]}{''.join(f' {a}={to_xml_string(v) if isinstance(v,str) else v}' for a,v in et.args[1].items())}>'.encode())
         _DUMP_ETREE_FUNCTIONS._dump_parent(f,et)
         f.write(f'</{et.args[0]}>'.encode())

    @staticmethod
    def _dump_cdata(f:io.BytesIO,et:Element): 
         
         f.write(et.args[0].encode())

_DUMP_ETREE_HANDLER_MAP = { ''                   : _DUMP_ETREE_FUNCTIONS._dump_parent,
                            ELEMENT_NAMES.XMLDECL: _DUMP_ETREE_FUNCTIONS._dump_xmldecl,
                            ELEMENT_NAMES.ELEMENT: _DUMP_ETREE_FUNCTIONS._dump_element, 
                            ELEMENT_NAMES.CDATA  : _DUMP_ETREE_FUNCTIONS._dump_cdata, 
                            ELEMENT_NAMES.___    : _DUMP_ETREE_FUNCTIONS._dump }

def dump_etree(f:io.BytesIO,et:Element):
     
     _DUMP_ETREE_HANDLER_MAP[et.name](f,et)

def dump_etree_map(zfn:str,et_map:dict[str,Element]):
     
     with zipfile.ZipFile(zfn, mode='w') as zf:
          
          for fn,et in et_map.items():
               
               with zf.open(name=fn, mode='w') as f:

                    print(f'Dumping to {fn}')
                    dump_etree(f,et)
