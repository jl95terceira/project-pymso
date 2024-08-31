import abc
import dataclasses
import functools
import io
import typing
import xml.parsers.expat as expat
import zipfile

def internal_file_by_name(zf:zipfile.ZipFile|str,fn:str):

     if isinstance(zf, str):

          with zipfile.ZipFile(zf, mode='r') as zf_:

               return internal_file_by_name(zf=zf_, fn=fn)
     
     return zf.open(fn, mode='r')

def internal_files(zf:zipfile.ZipFile|str):

     if isinstance(zf, str):

          with zipfile.ZipFile(zf, mode='r') as zf_:

               yield from internal_files(zf_)

          return

     for fn in sorted(finfo.filename for finfo in zf.filelist):
          
          yield (fn,
                 internal_file_by_name(zf=zf,fn=fn),)

@dataclasses.dataclass
class Node():

     type    :str             = ""
     args    :tuple           = tuple()
     children:list['Node'] = dataclasses.field(default_factory=lambda: list())

class NODE_TYPES:
     
     XMLDECL  = 'XMLDECL'
     DOCTYPE  = 'DOCTYPE'
     ELEMENT  = 'ELEMENT'
     ELEMDECL = 'ELEMDECL'
     CDATASEC = 'CDATASEC'
     CDATA    = 'CDATA'
     ___      = '***'

def load_tree(f:io.BytesIO):

    stack:list[Node] = [Node()]
    def upstacker  (name:str): return lambda *aa,_name=name: (stack             .append(Node(type=_name,args=aa)),stack[-2].children.append(stack[-1]),)
    def downstacker()        : return lambda *aa: (stack.pop(),)
    def appender   (name:str): return lambda *aa,_name=name: (stack[-1].children.append(Node(type=_name ,args=aa)),)
    xp = expat.ParserCreate()
    xp.XmlDeclHandler           = appender   (NODE_TYPES.XMLDECL)
    xp.StartDoctypeDeclHandler  = upstacker  (NODE_TYPES.DOCTYPE)
    xp.EndDoctypeDeclHandler    = downstacker()
    xp.StartElementHandler      = upstacker  (NODE_TYPES.ELEMENT)
    xp.ElementDeclHandler       = appender   (NODE_TYPES.ELEMDECL)
    xp.EndElementHandler        = downstacker()
    xp.StartCdataSectionHandler = upstacker  (NODE_TYPES.CDATASEC)
    xp.CharacterDataHandler     = appender   (NODE_TYPES.CDATA)
    xp.EndCdataSectionHandler   = downstacker()
    xp.DefaultHandlerExpand     = appender   (NODE_TYPES.___)
    xp.ParseFile(f)
    return stack[-1]

def load_tree_map(zf:zipfile.ZipFile|str):

    return {fn:load_tree(f) for fn,f in internal_files(zf)}

_XML_CHAR_ESCAPE_TUPLES = (
    ('&' ,'&amp;'),
    ('"' ,'&quot;'),
    ('\'','&apos;'),
    ('<' ,'&lt;'),
    ('>' ,'&gt;'),
)

def to_xml_string(s:str):
     
     return f'"{functools.reduce(lambda s,c: s.replace(c[0],c[1]), _XML_CHAR_ESCAPE_TUPLES, s)}"'

class _DUMP_TREE_FUNCTIONS:

    @staticmethod
    def _dump(f:io.BytesIO,et:Node): 
         
         f.write(et.args[0].encode())

    @staticmethod
    def _dump_parent (f:io.BytesIO,et:Node): 
         
         for child in et.children:
              
              dump_tree(f,child)

    @staticmethod
    def _dump_xmldecl(f:io.BytesIO,et:Node): 
         
         f.write(f'<?xml version="{et.args[0]}" encoding="{et.args[1]}" standalone="{ {1:'yes',0:'no'}[et.args[2]] }"?>'.encode())

    @staticmethod
    def _dump_element(f:io.BytesIO,et:Node): 
         
         f.write(f'<{et.args[0]}{''.join(f' {a}={to_xml_string(v) if isinstance(v,str) else v}' for a,v in et.args[1].items())}>'.encode())
         _DUMP_TREE_FUNCTIONS._dump_parent(f,et)
         f.write(f'</{et.args[0]}>'.encode())

    @staticmethod
    def _dump_cdata(f:io.BytesIO,et:Node): 
         
         f.write(et.args[0].encode())

_DUMP_TREE_HANDLER_MAP = { ''                   : _DUMP_TREE_FUNCTIONS._dump_parent,
                            NODE_TYPES.XMLDECL: _DUMP_TREE_FUNCTIONS._dump_xmldecl,
                            NODE_TYPES.ELEMENT: _DUMP_TREE_FUNCTIONS._dump_element, 
                            NODE_TYPES.CDATA  : _DUMP_TREE_FUNCTIONS._dump_cdata, 
                            NODE_TYPES.___    : _DUMP_TREE_FUNCTIONS._dump }

def dump_tree(f:io.BytesIO,et:Node):
     
     _DUMP_TREE_HANDLER_MAP[et.type](f,et)

def dump_tree_map(zfn:str,et_map:dict[str,Node]):
     
     with zipfile.ZipFile(zfn, mode='w') as zf:
          
          for fn,et in et_map.items():
               
               with zf.open(name=fn, mode='w') as f:

                    print(f'Dumping to {fn}')
                    dump_tree(f,et)

@dataclasses.dataclass
class Pointer[T]:

     x:T = dataclasses.field(default_factory=lambda: None)

def as_xml_elem(name: str, attrs:dict[str,str]={}, inner:str='', force_explicit_end=False, tail:str=''):

     return f'<{name}{'' if not attrs else f' {' '.join(f'{k}="{v}"' for k,v in attrs.items())}'}{('/>' if not force_explicit_end else f'></{name}>') if not inner else f'>{inner}</{name}>'}{tail}'

class EnumValues[T]:

     def __init__(self,e:'Enum[T]'):

          self._e = e
     
     def __iter__    (self)    : return iter(self._e._list)
     def __contains__(self,x:T): return x in self._e._set

class Enum[T]:

     def __init__(self):

          self._list  :list[T] = list()
          self._set   :set [T] = set ()
          self._values         = EnumValues(self)

     def __call__(self, x:T):

          self._list.append(x)
          self._set .add   (x)
          return x
     
     def values(self): return self._values

class ToXmlAble(metaclass=abc.ABCMeta):

     @abc.abstractmethod
     def to_xml(self) -> str: pass

def to_xml(x:ToXmlAble): return x.to_xml()

@dataclasses.dataclass
class GenericParent: # class for elements without specialized classes yet - ephemeral

    children:list[ToXmlAble] = dataclasses.field(default_factory=lambda: [], kw_only=True)

@dataclasses.dataclass
class GenericElement(GenericParent, ToXmlAble): # class for elements without specialized classes yet - ephemeral

    name :str
    attrs:dict[str,str]

    @typing.override
    def to_xml(self):
         
         return as_xml_elem(name=self.name, attrs=self.attrs, inner=''.join(map(to_xml, self.children)))

@dataclasses.dataclass
class GenericData(ToXmlAble):

     data:str

     @typing.override
     def to_xml(self):
         
         return self.data

def ifinstance[T](t:typing.Type[T], iterable:typing.Iterable) -> typing.Iterable[T]: 
     
     return filter(lambda x: isinstance(x, t), iterable)