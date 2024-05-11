import dataclasses
import io
import operator
import os
import os.path
import typing
import xml.parsers.expat as expat

from   project_package.package       import *
from   project_package.package._util import *
from   project_package.tests         import test

def line_sep(prefix:str=''):

    return f'{prefix}{(128-len(prefix))*':'}'

def process(zfn:str, p:typing.Callable[[str,io.BytesIO],None]):

    for fn, f in internal_files(zfn):

        p(fn,f)

def count_types(f:io.BytesIO,filter_name=lambda name: True):

    namelist:list[str]     = []
    counter :dict[str,int] = {}
    def handler_factory(name:str): 
        
        if not filter_name(name):

            return lambda *aa: None

        namelist.append(name)
        counter[name] = 0
        def _f(*aa): 

            counter[name] += 1

        return _f
    
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

    return {fn:count_types(f) for fn,f in internal_files(zfn)}

def count_types_all_print(zfn:str,filter_name=lambda name: True):

    supercounter:dict[str,list[tuple[str,int]]] = {}
    def foo(fn:str, f:io.BytesIO):

        print(fn)
        counter = count_types(f,filter_name=filter_name)
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

def print_etree(e:Element, filter:typing.Callable[[Element],bool]=lambda e: True, ind=0):

    if filter(e): 
        
        print(f"{ind*'-'}{repr(e.name)} {repr(e.args)}")

    for se in e.children:

        print_etree(se,filter=filter,ind=ind+2)

@dataclasses.dataclass
class ElementTreeDiff:

    changed:dict[str,tuple[Element,Element]]
    new    :dict[str,Element]
    removed:set[str]

def load_etree_map_diff(zfn1:str,zfn2:str):

    etm1 = load_etree_map(zfn1)
    etm2 = load_etree_map(zfn2)
    return ElementTreeDiff(changed={fn:(etm1[fn],et,) for fn,et in etm2.items() if fn     in etm1 and et != etm1[fn]},
                           new    ={fn:et             for fn,et in etm2.items() if fn not in etm1},
                           removed={fn                for fn    in etm1         if fn not in etm2})

def load_etree_map_diff_print(zfn1:str,zfn2:str):

    d = load_etree_map_diff(zfn1,zfn2)
    if d.changed:

        print(f'\nChanged ({sorted(d.changed)}):')
        for fn,et in d.changed.items():

            print(f'{line_sep(fn)}')
            print(f'{line_sep('OLD')}')
            print_etree(et[0])
            print(f'{line_sep('NEW')}')
            print_etree(et[1])
            print(f'{line_sep()}')
    
    if d.new:

        print(f'\nNew ({sorted(d.new)}):')
        for fn,et in d.new.items():

            print(f'{line_sep(fn)}')
            print_etree(et)
            print(f'{line_sep()}')
    
    if d.removed:

        print(f'\nRemoved ({sorted(d.removed)})')
        for fn,et in d.removed.items():

            print(f'{line_sep(fn)}')
            print(f'{line_sep()}')

if __name__ == '__main__':

    import os

    for zfn in (
        test.OFFICE_FILES.EXAMPLE,
        ):

        print(zfn,end='\n\n')
        print('\n'.join(fn for fn,f in internal_files(zfn)), end='\n\n')
        #count_types_all_print(zfn) # count all element types
        #count_types_all_print(zfn,filter_name=lambda name: name in {'XmlDecl','StartElementHandler','EndElementHandler','Other'}) # count rarer element types
        #process(zfn, lambda fn,f: (print(line_sep(fn)),print_etree(load_etree(f))                                  , print(line_sep()))) # print all
        #process(zfn, lambda fn,f: (print(line_sep(fn)),print_etree(load_etree(f))                                  , print(line_sep())) if fn == '_rels/.rels' else None) # print only rels
        #process(zfn, lambda fn,f: (print(line_sep(fn)),print_etree(load_etree(f), filter=lambda e: e.name == "***"), print(line_sep()))) # print only unknown
        #print(docx._rels)


    print('\nDiff')
    count_types_all_diff_print(test.OFFICE_FILES.EXAMPLE,test.OFFICE_FILES.EXAMPLE_COPY)
    #load_etree_map_diff_print (r'3.docx',r'3.3.docx')