import zipfile

def internal_files(zf:zipfile.ZipFile, prep=lambda: None):

    for finfo in zf.filelist:

        prep(finfo)
        with zf.open(finfo.filename, mode='r') as f:

            yield (finfo.filename,f,)

def internal_files_by_name(zfn:str, prep=lambda f: None):

    with zipfile.ZipFile(zfn, mode='r') as zf:

        yield from internal_files(zf, prep=prep)
