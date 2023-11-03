import dataclasses
import io
import operator
import typing
import xml.parsers.expat as expat
import zipfile
import _util
import _model

def process(zfn:str, p:typing.Callable[[str,io.BytesIO],None]):

    for fn, f in _util.internal_files_by_name(zfn):

        p(fn,f)

def count_types(f:io.BytesIO):

    namelist:list[str]     = []
    counter :dict[str,int] = {}
    handler_factory        = lambda name: (namelist.append(name),counter.__setitem__(name,0), lambda *aa: (counter.__setitem__(name, counter.__getitem__(name)+1),),)[-1]
    xp = expat.ParserCreate()
    xp.XmlDeclHandler          = handler_factory('XmlDecl')
    xp.StartDoctypeDeclHandler = handler_factory('StartDocTypeDecl')
    xp.EndDoctypeDeclHandler   = handler_factory('EndDocTypeDecl')
    xp.ElementDeclHandler      = handler_factory('ElementDeclHandler')
    xp.StartElementHandler     = handler_factory('StartElementHandler')
    xp.EndElementHandler       = handler_factory('EndElementHandler')
    xp.CharacterDataHandler    = handler_factory('CharacterDataHandler')
    xp.DefaultHandler          = handler_factory('Other')
    xp.ParseFile(f)
    return list(map(lambda name: (name,counter[name]), namelist))

def count_types_and_print_all(zfn:str):

    supercounter:dict[str,dict[str,int]] = {}
    def foo(fn:str, f:io.BytesIO):

        print(fn)
        counter = count_types(f)
        pad = max(map(len,map(operator.itemgetter(0), counter)))
        for name,count in counter:

            if not count: continue
            print(name+((pad-len(name))*' ')+': '+str(count))

        print(64*'-',end='\n\n')
        supercounter[fn] = counter
    
    process(zfn,foo)

class Element():

    def __init__(self,name="",args=tuple()):

        self.name     = name
        self.args     = args
        self.children = list()

def get_etree(f:io.BytesIO):

    stack:list[Element] = [Element()]
    upstacker             = lambda name: lambda *aa: (stack.append(Element(name=name,args=aa)),stack[-2].children.append(stack[-1]),)
    downstacker           = lambda     : lambda *aa: (stack.pop(),)
    stacker               = lambda name: lambda *aa: (stack.append(Element(name=name ,args=aa)),)
    xp = expat.ParserCreate()
    xp.XmlDeclHandler          = stacker    ('xmldecl')
    xp.StartDoctypeDeclHandler = upstacker  ('doctype')
    xp.EndDoctypeDeclHandler   = downstacker()
    xp.ElementDeclHandler      = stacker    ('elemdecl')
    xp.StartElementHandler     = upstacker  ('element')
    xp.EndElementHandler       = downstacker()
    xp.CharacterDataHandler    = stacker    ('cdata')
    xp.DefaultHandler          = stacker    ('???')
    xp.ParseFile(f)
    return stack[-1]

def print_etree(e:Element, filter:typing.Callable[[Element],bool]=lambda e: True, ind=0):

    if filter(e): 
        
        print(ind*'>'+f"{repr(e.name)} {repr(e.args)}")

    for se in e.children:

        print_etree(se,filter=filter,ind=ind+2)

if __name__ == '__main__':

    doc = count_types_and_print_all(r'2.docx')
    process(r'2.docx', lambda fn,f: (print(fn,end=':\n'),print_etree(get_etree(f)),print(end=64*'-'+'\n\n')))
    #process(r'2.docx', lambda fn,f: (print(fn,end=':\n'),print_etree(get_etree(f), filter=lambda e: e.name == "???"),print(end=64*'-'+'\n\n')))
