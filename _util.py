import zipfile

def internal_files(zf:zipfile.ZipFile, prep=lambda: None):

    for fn in sorted(finfo.filename for finfo in zf.filelist):

        with zf.open(fn, mode='r') as f:

            yield (fn,f,)

def internal_files_by_name(zfn:str, prep=lambda f: None):

    with zipfile.ZipFile(zfn, mode='r') as zf:

        yield from internal_files(zf, prep=prep)
