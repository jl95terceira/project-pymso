import dataclasses
import io
import operator
import typing
import xml.parsers.expat as expat
import model
import _util

def process(zfn:str, p:typing.Callable[[str,io.BytesIO],None]):

    for fn, f in _util.internal_files_by_name(zfn):

        p(fn,f)

def count_types(f:io.BytesIO):

    namelist:list[str]     = []
    counter :dict[str,int] = {}
    handler_factory        = lambda name: (namelist.append(name),counter.__setitem__(name,0), lambda *aa: (counter.__setitem__(name, counter.__getitem__(name)+1),),)[-1]
    xp = expat.ParserCreate()
    xp.XmlDeclHandler           = handler_factory('XmlDecl')
    xp.StartDoctypeDeclHandler  = handler_factory('StartDocTypeDecl')
    xp.EndDoctypeDeclHandler    = handler_factory('EndDocTypeDecl')
    xp.ElementDeclHandler       = handler_factory('ElementDeclHandler')
    xp.StartElementHandler      = handler_factory('StartElementHandler')
    xp.EndElementHandler        = handler_factory('EndElementHandler')
    xp.CharacterDataHandler     = handler_factory('CharacterDataHandler')
    xp.StartCdataSectionHandler = handler_factory('StartCdataSectionHandler')
    xp.EndCdataSectionHandler   = handler_factory('EndCdataSectionHandler')
    xp.DefaultHandlerExpand     = handler_factory('Other')
    xp.ParseFile(f)
    return tuple(map(lambda name: (name,counter[name]), namelist))

def count_types_all(zfn:str):

    return {fn:count_types(f) for fn,f in _util.internal_files_by_name(zfn)}

def count_types_all_print(zfn:str):

    supercounter:dict[str,list[tuple[str,int]]] = {}
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

@dataclasses.dataclass
class CountTypeDiff:

    changed:dict[str,dict[str,tuple[int,int]]]
    new    :dict[str,dict[str,      int]]
    removed:set [str]

def count_types_all_diff(zfn1:str,zfn2:str):

    cm1 = {k:dict(v) for k,v in count_types_all(zfn1).items()}
    cm2 = {k:dict(v) for k,v in count_types_all(zfn2).items()}
    return CountTypeDiff(changed={fn:{n:(v1,v2,) for n,v1,v2 in ((n,v,c2[n]) for n,v in c1.items()) if v1 != v2} for fn,c1,c2 in ((fn,c1,cm2[fn],)\
                                       for fn,c1 in cm1.items() if fn     in cm2) if c1 != c2},
                         new    ={fn:c for fn,c  in cm2.items() if fn not in cm1},
                         removed={fn   for fn    in cm1         if fn not in cm2})

def count_types_all_diff_print(zfn1:str,zfn2:str):

    d = count_types_all_diff(zfn1,zfn2)
    if d.changed:

        print('\nChanged:')
        for fn,count in d.changed.items():

            print(f'\n{{{fn}}}')
            padn  = max(map(len,count))
            padc1 = max(map(len,map(str,map(operator.itemgetter(0),count.values()))))
            padc2 = max(map(len,map(str,map(operator.itemgetter(1),count.values()))))
            print('\n'.join(n+(padn-len(n))*' '+': '+(padc1-len(c1))*' '+c1+' -> '+(padc2-len(c2))*' '+c2 for n,c1,c2 in ((n,str(c1),str(c2),) for n,(c1,c2) in count.items() if c1)))
        
    if d.new: 

        print('\nNew:')
        for fn,count in d.new.items():

            print(f'\n{{{fn}}}')
            pad = max(map(len,map(operator.itemgetter(0), count)))
            print('\n'.join(n+(pad-len(n))*' '+': '+str(c) for n,c in count if c))

    if d.removed:

        print('\nRemoved')
        for fn in d.removed:

            print(f'\n{{{fn}}}')

@dataclasses.dataclass
class Element():

        name    :str             = ""
        args    :tuple           = ()
        children:list['Element'] = dataclasses.field(default_factory=lambda: [])

def get_etree(f:io.BytesIO):

    stack:list[Element] = [Element()]
    upstacker             = lambda name: lambda *aa: (stack.append(Element(name=name,args=aa)),stack[-2].children.append(stack[-1]),)
    downstacker           = lambda     : lambda *aa: (stack.pop(),)
    stacker               = lambda name: lambda *aa: (stack[-1].children.append(Element(name=name ,args=aa)),)
    xp = expat.ParserCreate()
    xp.XmlDeclHandler           = stacker    ('XMLDECL')
    xp.StartDoctypeDeclHandler  = upstacker  ('DOCTYPE')
    xp.EndDoctypeDeclHandler    = downstacker()
    xp.StartElementHandler      = upstacker  ('ELEMENT')
    xp.ElementDeclHandler       = stacker    ('ELEMDECL')
    xp.EndElementHandler        = downstacker()
    xp.StartCdataSectionHandler = upstacker  ('CDATASEC')
    xp.CharacterDataHandler     = stacker    ('CDATA')
    xp.EndCdataSectionHandler   = downstacker()
    xp.DefaultHandlerExpand     = stacker    ('***')
    xp.ParseFile(f)
    return stack[-1]

def print_etree(e:Element, filter:typing.Callable[[Element],bool]=lambda e: True, ind=0):

    if filter(e): 
        
        print(ind*'-'+f"{repr(e.name)} {repr(e.args)}")

    for se in e.children:

        print_etree(se,filter=filter,ind=ind+2)

def get_etree_map(zfn:str):

    return {fn:get_etree(f) for fn,f in _util.internal_files_by_name(zfn)}

@dataclasses.dataclass
class ElementTreeDiff:

    changed:dict[str,Element]
    new    :dict[str,Element]
    removed:set[str]

def get_etree_map_diff(zfn1:str,zfn2:str):

    etm1 = get_etree_map(zfn1)
    etm2 = get_etree_map(zfn2)
    return ElementTreeDiff(changed={fn:et for fn,et in etm2.items() if fn     in etm1 and et != etm1[fn]},
                           new    ={fn:et for fn,et in etm2.items() if fn not in etm1},
                           removed={fn    for fn    in etm1         if fn not in etm2})

def get_etree_map_diff_print(zfn1:str,zfn2:str):

    d = get_etree_map_diff(zfn1,zfn2)
    if d.changed:

        print('\nChanged ({0}):'.format(sorted(d.changed)))
        for fn,et in d.changed.items():

            print(f'\n{{{fn}}}')
            print_etree(et)
    
    if d.new:

        print('\nNew ({0}):'.format(sorted(d.new)))
        for fn,et in d.new.items():

            print(f'\n{{{fn}}}')
            print_etree(et)
    
    if d.removed:

        print('\nRemoved ({0})'.format(sorted(d.removed)))
        for fn,et in d.removed.items():

            print(f'\n{{{fn}}}')

if __name__ == '__main__':

    for zfn in (
        #r'2.docx',
        r'3.docx',
        ):

        print(zfn,end='\n{}\n\n'.format(32*':'))
        print('\n'.join(fn for fn,f in _util.internal_files_by_name(zfn)), end='\n\n')
        #doc = count_types_all_print(zfn)
        #process(zfn, lambda fn,f: (print(fn,end=':\n'),print_etree(get_etree(f)),print(end=64*'-'+'\n\n')))
        #process(zfn, lambda fn,f: (print(fn,end=':\n'),print_etree(get_etree(f)),print(end=64*'-'+'\n\n')) if fn == '_rels/.rels' else None)
        #process(zfn, lambda fn,f: (print(fn,end=':\n'),print_etree(get_etree(f), filter=lambda e: e.name == "***"),print(end=64*'-'+'\n\n')))
        docx = model.DocX(zfn)
        print(docx._rels)

    #print('Diff')    
    #count_types_all_diff_print(r'2.docx',r'3.docx')
    #get_etree_map_diff_print  (r'2.docx',r'3.docx')
