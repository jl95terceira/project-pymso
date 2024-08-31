import os.path

OFFICE_FILES_DIRECTORY_PATH = os.path.join(os.path.split(os.path.abspath(__file__))[0],'files')

def file_path(file_name:str):

    return os.path.join(OFFICE_FILES_DIRECTORY_PATH, file_name)

class OFFICE_FILES:

    EXAMPLE        = file_path('example.docx')
    EXAMPLE_COPY   = file_path('example.copy.docx')
    EXAMPLE_EDITED = file_path('example-edited.docx')

